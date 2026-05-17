"""
TaskForge
Flask + PostgreSQL + WebSockets (Flask-SocketIO) + Pandas/NumPy
"""

from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_socketio import SocketIO, emit, join_room   # join_room imported at top level
import psycopg2
import psycopg2.extras
from werkzeug.security import generate_password_hash, check_password_hash
import pandas as pd
import numpy as np
from functools import wraps
import os
import socket
from urllib.parse import urlparse
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")

# FIX 1: explicit async_mode — without this SocketIO silently falls back
#         to HTTP polling and real-time push never works

socketio = SocketIO(
    app,
    cors_allowed_origins="*",
    async_mode="gevent",
    logger=False,
    engineio_logger=False,
)
# ─── Database ──────────────────────────────────────────────────────────────

def get_db():
    database_url = os.getenv("SUPABASE_POOLER_URL") or os.getenv("DATABASE_URL")
    if database_url:
        # Supabase requires SSL and Render may need explicit IPv4 resolution.
        connect_kwargs = {"sslmode": "require", "connect_timeout": 10}
        parsed = urlparse(database_url)
        if parsed.hostname:
            try:
                infos = socket.getaddrinfo(parsed.hostname, None, socket.AF_INET, socket.SOCK_STREAM)
                if infos:
                    connect_kwargs["hostaddr"] = infos[0][4][0]
            except socket.gaierror:
                pass
        return psycopg2.connect(database_url, **connect_kwargs)
    # local fallback
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        database=os.getenv("DB_NAME", "taskforge"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", ""),
        port=os.getenv("DB_PORT", "5432"),
        connect_timeout=10,
    )

def init_db():
    conn = get_db()
    cur  = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id         SERIAL       PRIMARY KEY,
            username   VARCHAR(80)  UNIQUE NOT NULL,
            email      VARCHAR(120) UNIQUE NOT NULL,
            password   TEXT         NOT NULL,
            created_at TIMESTAMP    DEFAULT NOW()
        );
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id          SERIAL       PRIMARY KEY,
            user_id     INTEGER      NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            title       VARCHAR(200) NOT NULL,
            description TEXT,
            priority    VARCHAR(20)  NOT NULL DEFAULT 'medium'
                        CHECK (priority IN ('low','medium','high')),
            status      VARCHAR(20)  NOT NULL DEFAULT 'pending'
                        CHECK (status IN ('pending','in_progress','completed')),
            created_at  TIMESTAMP    NOT NULL DEFAULT NOW(),
            updated_at  TIMESTAMP    NOT NULL DEFAULT NOW()
        );
    """)
    conn.commit()
    cur.close(); conn.close()

# ─── Auth helpers ──────────────────────────────────────────────────────────

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            return jsonify({"error": "Unauthorized"}), 401
        return f(*args, **kwargs)
    return decorated

def login_required_page(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("index"))
        return f(*args, **kwargs)
    return decorated

# ─── Pages ─────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    if "user_id" in session:
        return redirect(url_for("dashboard"))
    return render_template("landing.html")

@app.route("/dashboard")
@login_required_page
def dashboard():
    return render_template("dashboard.html", username=session.get("username"))

# ─── Auth APIs ─────────────────────────────────────────────────────────────

@app.route("/api/register", methods=["POST"])
def register():
    data     = request.get_json()
    username = data.get("username", "").strip()
    email    = data.get("email", "").strip()
    password = data.get("password", "")

    if not username or not email or not password:
        return jsonify({"error": "All fields are required"}), 400
    if len(password) < 6:
        return jsonify({"error": "Password must be at least 6 characters"}), 400

    hashed = generate_password_hash(password)
    try:
        conn = get_db()
        cur  = conn.cursor()
        cur.execute(
            "INSERT INTO users (username, email, password) VALUES (%s,%s,%s) RETURNING id",
            (username, email, hashed)
        )
        user_id = cur.fetchone()[0]
        conn.commit(); cur.close(); conn.close()
        session["user_id"]  = user_id
        session["username"] = username
        return jsonify({"message": "Registered successfully", "username": username}), 201
    except psycopg2.errors.UniqueViolation:
        return jsonify({"error": "Username or email already exists"}), 409
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/login", methods=["POST"])
def login():
    data     = request.get_json()
    username = data.get("username", "").strip()
    password = data.get("password", "")

    if not username or not password:
        return jsonify({"error": "Username and password required"}), 400

    try:
        conn = get_db()
        cur  = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT * FROM users WHERE username=%s", (username,))
        user = cur.fetchone()
        cur.close(); conn.close()

        if not user or not check_password_hash(user["password"], password):
            return jsonify({"error": "Invalid credentials"}), 401

        session["user_id"]  = user["id"]
        session["username"] = user["username"]
        return jsonify({"message": "Login successful", "username": user["username"]})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"message": "Logged out"})

# ─── Task APIs ─────────────────────────────────────────────────────────────

@app.route("/api/tasks", methods=["GET"])
@login_required
def get_tasks():
    priority = request.args.get("priority")
    status   = request.args.get("status")
    query    = "SELECT * FROM tasks WHERE user_id=%s"
    params   = [session["user_id"]]
    if priority: query += " AND priority=%s"; params.append(priority)
    if status:   query += " AND status=%s";   params.append(status)
    query += " ORDER BY created_at DESC"

    try:
        conn = get_db()
        cur  = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(query, params)
        tasks = [dict(t) for t in cur.fetchall()]
        for t in tasks:
            t["created_at"] = t["created_at"].isoformat()
            t["updated_at"] = t["updated_at"].isoformat()
        cur.close(); conn.close()
        return jsonify(tasks)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/tasks", methods=["POST"])
@login_required
def add_task():
    data        = request.get_json()
    title       = data.get("title", "").strip()
    description = data.get("description", "").strip()
    priority    = data.get("priority", "medium")
    status      = data.get("status", "pending")

    if not title:
        return jsonify({"error": "Title is required"}), 400
    if priority not in ("low","medium","high"):
        return jsonify({"error": "Invalid priority"}), 400
    if status not in ("pending","in_progress","completed"):
        return jsonify({"error": "Invalid status"}), 400

    try:
        conn = get_db()
        cur  = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(
            "INSERT INTO tasks (user_id,title,description,priority,status) VALUES (%s,%s,%s,%s,%s) RETURNING *",
            (session["user_id"], title, description, priority, status)
        )
        task = dict(cur.fetchone())
        task["created_at"] = task["created_at"].isoformat()
        task["updated_at"] = task["updated_at"].isoformat()
        conn.commit(); cur.close(); conn.close()

        room = f"user_{session['user_id']}"
        socketio.emit("task_added", task, room=room)
        broadcast_analytics(session["user_id"])
        return jsonify(task), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/tasks/<int:task_id>", methods=["PUT"])
@login_required
def update_task(task_id):
    data           = request.get_json()
    fields, params = [], []

    for col in ("title","description","priority","status"):
        if col in data:
            fields.append(f"{col}=%s")
            params.append(data[col])

    if not fields:
        return jsonify({"error": "No fields to update"}), 400

    fields.append("updated_at=NOW()")
    params += [task_id, session["user_id"]]

    try:
        conn = get_db()
        cur  = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(
            f"UPDATE tasks SET {','.join(fields)} WHERE id=%s AND user_id=%s RETURNING *",
            params
        )
        task = cur.fetchone()
        if not task:
            return jsonify({"error": "Task not found"}), 404
        task = dict(task)
        task["created_at"] = task["created_at"].isoformat()
        task["updated_at"] = task["updated_at"].isoformat()
        conn.commit(); cur.close(); conn.close()

        room = f"user_{session['user_id']}"
        socketio.emit("task_updated", task, room=room)
        broadcast_analytics(session["user_id"])
        return jsonify(task)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/tasks/<int:task_id>", methods=["DELETE"])
@login_required
def delete_task(task_id):
    try:
        conn = get_db()
        cur  = conn.cursor()
        cur.execute(
            "DELETE FROM tasks WHERE id=%s AND user_id=%s RETURNING id",
            (task_id, session["user_id"])
        )
        row = cur.fetchone()
        if not row:
            return jsonify({"error": "Task not found"}), 404
        conn.commit(); cur.close(); conn.close()

        room = f"user_{session['user_id']}"
        socketio.emit("task_deleted", {"id": task_id}, room=room)
        broadcast_analytics(session["user_id"])
        return jsonify({"message": "Task deleted", "id": task_id})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ─── Analytics (Pandas + NumPy) ────────────────────────────────────────────

def compute_analytics(user_id):
    conn = get_db()
    cur  = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("SELECT * FROM tasks WHERE user_id=%s", (user_id,))
    rows = cur.fetchall()
    cur.close(); conn.close()

    if not rows:
        return {"total":0,"completed":0,"pending":0,"in_progress":0,
                "completion_pct":0.0,"priority_dist":{},"avg_tasks_per_day":0.0}

    df = pd.DataFrame(rows)
    df["created_at"] = pd.to_datetime(df["created_at"])

    total       = len(df)
    completed   = int((df["status"] == "completed").sum())
    in_progress = int((df["status"] == "in_progress").sum())
    pending     = int((df["status"] == "pending").sum())
    completion  = round(float(np.divide(completed * 100, total)), 1)
    priority_dist = df["priority"].value_counts().to_dict()
    daily       = df.groupby(df["created_at"].dt.date).size().values
    avg_per_day = round(float(np.mean(daily)), 2) if len(daily) else 0.0

    return {"total":total,"completed":completed,"pending":pending,
            "in_progress":in_progress,"completion_pct":completion,
            "priority_dist":priority_dist,"avg_tasks_per_day":avg_per_day}

@app.route("/api/analytics")
@login_required
def analytics():
    return jsonify(compute_analytics(session["user_id"]))

def broadcast_analytics(user_id):
    socketio.emit("analytics_update", compute_analytics(user_id), room=f"user_{user_id}")

# ─── WebSocket events ──────────────────────────────────────────────────────

@socketio.on("connect")
def on_connect():
    """
    FIX 2 (root cause of the real-time bug):
    The old code had a separate 'join' event that the client emitted with
    socket.emit('join', {}) — an empty object.  on_join then did
    data.get("user_id") which returned None, so join_room was never called
    and nobody was ever placed in a room.  Broadcasts to f"user_{id}" rooms
    went into a void and were silently dropped.

    The fix: join the room here, on 'connect', using the Flask session
    that is already available in the SocketIO request context.
    No client-side user_id needed at all.
    """
    user_id = session.get("user_id")
    if user_id:
        room = f"user_{user_id}"
        join_room(room)
        emit("joined", {"room": room, "user_id": user_id})

@socketio.on("disconnect")
def on_disconnect():
    pass  # Flask-SocketIO handles room leave on disconnect automatically

# ─── Entry point ───────────────────────────────────────────────────────────
# Called by both gunicorn and direct python run
with app.app_context():
    init_db()

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    socketio.run(
        app,
        debug=False,
        host="0.0.0.0",
        port=port,
        allow_unsafe_werkzeug=True
    )
