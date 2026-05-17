<div align="center">

<img src="https://img.shields.io/badge/TaskForge-Live-10b981?style=for-the-badge&logo=render&logoColor=white" alt="Live"/>

# ⚒️ TaskForge

**A full-stack real-time task management web application**  
built with Flask, PostgreSQL, WebSockets, and Pandas analytics.

[![Live Demo](https://img.shields.io/badge/🌐_Live_Demo-taskforge--lx52.onrender.com-10b981?style=flat-square)](https://taskforge-lx52.onrender.com/)
[![Python](https://img.shields.io/badge/Python-3.11-3776ab?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-3.0.3-000000?style=flat-square&logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-18-336791?style=flat-square&logo=postgresql&logoColor=white)](https://postgresql.org)
[![License](https://img.shields.io/badge/License-MIT-yellow?style=flat-square)](./LICENSE)

</div>

---

## 🌐 Live Demo

| | |
|---|---|
| **URL** | [https://taskforge-lx52.onrender.com](https://taskforge-lx52.onrender.com/) |
| **Status** | 🟢 Live |
| **Hosting** | Render (Web Service) |
| **Database** | Supabase (PostgreSQL) |
| **Region** | Asia Pacific |

> ⚠️ Hosted on Render's free tier — first load may take 30–60 seconds to wake up from idle.

---

## 📸 Screenshots

### Landing Page
![Landing Page](./demo1.png)

### Dashboard — Task List with Inline Status Toggle
![Dashboard](./demo2.png)

### Analytics View
![Analytics](./demo3.png)

---

## ✨ Features

### 🔐 Authentication
- Secure user registration, login, and logout
- Passwords hashed using Werkzeug's `pbkdf2:sha256` — never stored plain text
- Flask session-based auth with route guards on every page and API endpoint

### ✅ Task Management
- Full CRUD — create, read, update, delete tasks
- Each task has a **title**, **description**, **priority** (low / medium / high), **status**, and **created date**
- Filter tasks by status or priority instantly
- **Inline status toggle** — flip between Pending / In Progress / Done directly in the task row, no modal needed
- **Inline edit panel** — expand title, description, and priority editor without leaving the page

### 📊 Analytics (Pandas + NumPy)
- Total tasks, completed, pending, in-progress counts
- Completion percentage computed with `numpy.divide`
- Priority distribution chart
- Average tasks per day using `numpy.mean` over a Pandas time-grouped DataFrame

### 🔴 Real-time WebSockets
- Powered by Flask-SocketIO with gevent async mode
- Every task add, update, and delete instantly pushes to the dashboard without a page reload
- Analytics stats update live on every change
- Live event feed view shows a timestamped stream of all WebSocket events
- Users are isolated in private rooms (`user_<id>`) — no data leaks between sessions

### 🎨 Frontend
- Dark-themed, responsive UI — no frontend framework, pure HTML/CSS/JS
- Landing page with hero, feature cards, tech stack strip, and auth modal
- Dashboard with sidebar navigation, stat cards, task list, analytics panel, and live feed

---

## 🧱 Tech Stack

| Layer | Technology | Purpose |
|---|---|---|
| **Language** | Python 3.11 | Core runtime |
| **Web Framework** | Flask 3.0.3 | HTTP routing, templating, sessions |
| **Real-time** | Flask-SocketIO 5.3.6 + gevent | WebSocket push events |
| **Database Driver** | psycopg2-binary 2.9.9 | PostgreSQL connection |
| **Analytics** | Pandas 2.2.2 + NumPy 1.26.4 | Task stats computation |
| **Auth** | Werkzeug | Password hashing (pbkdf2:sha256) |
| **WSGI Server** | Gunicorn + gevent-websocket | Production server |
| **Database** | PostgreSQL (Supabase) | Persistent storage |
| **Frontend** | HTML5, CSS3, Vanilla JS | UI — no frameworks |
| **Hosting** | Render | Web service deployment |
| **Env Config** | python-dotenv | Environment variable management |

---

## 🚀 Deployment

### Infrastructure

| Component | Service | Plan |
|---|---|---|
| Web Server | [Render](https://render.com) | Free |
| Database | [Supabase](https://supabase.com) | Free (500MB) |
| WebSockets | Flask-SocketIO / gevent | Included |
| Domain | Render subdomain | Free |

### Deployment Stack

```
GitHub → Render (auto-deploy on push)
              ↓
     Gunicorn + GeventWebSocketWorker
              ↓
         Flask App
         /       \
   REST API    SocketIO
        \         /
        psycopg2
             ↓
    Supabase PostgreSQL
    (Transaction Pooler — IPv4)
```

### Why These Choices
- **Render** over Railway/Heroku — free tier with no credit card, native WebSocket support, GitHub auto-deploy
- **Supabase** over Render's own DB — free forever (no 90-day expiry), managed PostgreSQL with connection pooling
- **gevent** over eventlet — better compatibility with Render's infrastructure, required for gunicorn WebSocket workers
- **Transaction Pooler URL** — Supabase's direct DB URL uses IPv6 which Render's free tier doesn't support; pooler forces IPv4

---

## 📁 Project Structure

```
taskforge/
├── app.py                  # Flask app — routes, APIs, SocketIO, analytics
├── schema.sql              # PostgreSQL schema with indexes and constraints
├── initdb.py               # Standalone DB initializer (no Flask dependency)
├── requirements.txt        # All Python dependencies
├── Procfile                # Gunicorn start command for Render
├── runtime.txt             # Python version pin
├── .env.example            # Environment variable template
├── .gitignore
├── README.md
├── LICENSE
├── demo1.png               # Landing page screenshot
├── demo2.png               # Dashboard screenshot
├── demo3.png               # Analytics screenshot
└── templates/
    ├── landing.html        # Public landing page with auth modal
    └── dashboard.html      # Protected dashboard (tasks, analytics, live feed)
```

---

## ⚙️ Local Setup

### Prerequisites
- Python 3.11+
- PostgreSQL running locally
- Git

### Steps

```bash
# 1. Clone the repository
git clone https://github.com/YOUR_USERNAME/taskforge.git
cd taskforge

# 2. Create and activate virtual environment
python -m venv venv
source venv/bin/activate        # macOS / Linux
# venv\Scripts\activate         # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Create the database
psql -U postgres -c "CREATE DATABASE taskforge;"

# 5. Configure environment variables
cp .env.example .env
# Edit .env and fill in your values

# 6. Initialize tables
python initdb.py

# 7. Start the app
python app.py
```

App runs at: **http://localhost:5000**

---

## 🔐 Environment Variables

```env
# Flask
SECRET_KEY=your-super-secret-key-change-this

# Local PostgreSQL (used when DATABASE_URL is not set)
DB_HOST=localhost
DB_PORT=5432
DB_NAME=taskforge
DB_USER=postgres
DB_PASSWORD=your_postgres_password

# Production — Supabase Transaction Pooler URL (IPv4, required on Render)
DATABASE_URL=postgresql://postgres.xxxxxxxxxxxx:PASSWORD@aws-1-ap-northeast-1.pooler.supabase.com:6543/postgres
```

> Generate a secure `SECRET_KEY` with:
> ```bash
> python -c "import secrets; print(secrets.token_hex(32))"
> ```

---

## 🔌 REST API Reference

### Authentication

| Method | Endpoint | Body | Response |
|---|---|---|---|
| `POST` | `/api/register` | `{username, email, password}` | `201` user created |
| `POST` | `/api/login` | `{username, password}` | `200` logged in |
| `POST` | `/api/logout` | — | `200` logged out |

### Tasks

| Method | Endpoint | Params / Body | Response |
|---|---|---|---|
| `GET` | `/api/tasks` | `?status=&priority=` | Array of task objects |
| `POST` | `/api/tasks` | `{title, description, priority, status}` | Created task |
| `PUT` | `/api/tasks/<id>` | Any task fields | Updated task |
| `DELETE` | `/api/tasks/<id>` | — | `{message, id}` |

### Analytics

| Method | Endpoint | Response |
|---|---|---|
| `GET` | `/api/analytics` | `{total, completed, pending, in_progress, completion_pct, priority_dist, avg_tasks_per_day}` |

**Task object shape:**
```json
{
  "id": 1,
  "user_id": 3,
  "title": "Fix auth bug",
  "description": "Users can't login with special chars",
  "priority": "high",
  "status": "in_progress",
  "created_at": "2026-05-17T10:00:00",
  "updated_at": "2026-05-17T11:30:00"
}
```

---

## 🔴 WebSocket Events

| Event | Direction | Payload | Trigger |
|---|---|---|---|
| `connect` | client → server | — | On page load |
| `joined` | server → client | `{room, user_id}` | Confirms room join |
| `task_added` | server → client | Full task object | New task created |
| `task_updated` | server → client | Full task object | Task updated |
| `task_deleted` | server → client | `{id}` | Task deleted |
| `analytics_update` | server → client | Analytics object | Any task change |

Users are placed in a private room (`user_<id>`) on connect using Flask session — no client-side user ID passing required.

---

## 🗄️ Database Schema

```sql
-- Users table
CREATE TABLE users (
    id         SERIAL       PRIMARY KEY,
    username   VARCHAR(80)  UNIQUE NOT NULL,
    email      VARCHAR(120) UNIQUE NOT NULL,
    password   TEXT         NOT NULL,
    created_at TIMESTAMP    DEFAULT NOW()
);

-- Tasks table
CREATE TABLE tasks (
    id          SERIAL       PRIMARY KEY,
    user_id     INTEGER      NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title       VARCHAR(200) NOT NULL,
    description TEXT,
    priority    VARCHAR(20)  NOT NULL DEFAULT 'medium'
                CHECK (priority IN ('low', 'medium', 'high')),
    status      VARCHAR(20)  NOT NULL DEFAULT 'pending'
                CHECK (status IN ('pending', 'in_progress', 'completed')),
    created_at  TIMESTAMP    NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMP    NOT NULL DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_tasks_user_id  ON tasks(user_id);
CREATE INDEX idx_tasks_status   ON tasks(status);
CREATE INDEX idx_tasks_priority ON tasks(priority);
```

---

## 📦 Dependencies

```
Flask==3.0.3
Flask-SocketIO==5.3.6
psycopg2-binary==2.9.9
Werkzeug==3.0.3
pandas==2.2.2
numpy==1.26.4
python-dotenv==1.0.1
gevent==23.9.1
gevent-websocket==0.10.1
gunicorn==21.2.0
```

---

## 📜 License

This project is licensed under the **MIT License** — see [LICENSE](./LICENSE) for details.

---

<div align="center">

Built with precision by **Aditya Mogha**

⚒️ **TaskForge** — Forge your productivity

</div>
