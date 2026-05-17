-- ============================================================
--  TaskForge — Database Schema
--  PostgreSQL
-- ============================================================

-- Drop existing tables (for clean re-runs)
DROP TABLE IF EXISTS tasks CASCADE;
DROP TABLE IF EXISTS users CASCADE;

-- ─────────────────────────────────────────────
-- USERS TABLE
-- ─────────────────────────────────────────────
CREATE TABLE users (
    id         SERIAL       PRIMARY KEY,
    username   VARCHAR(80)  UNIQUE NOT NULL,
    email      VARCHAR(120) UNIQUE NOT NULL,
    password   TEXT         NOT NULL,
    created_at TIMESTAMP    NOT NULL DEFAULT NOW()
);

-- ─────────────────────────────────────────────
-- TASKS TABLE
-- ─────────────────────────────────────────────
CREATE TABLE tasks (
    id          SERIAL      PRIMARY KEY,
    user_id     INTEGER     NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title       VARCHAR(200) NOT NULL,
    description TEXT,
    priority    VARCHAR(20)  NOT NULL DEFAULT 'medium'
                CHECK (priority IN ('low', 'medium', 'high')),
    status      VARCHAR(20)  NOT NULL DEFAULT 'pending'
                CHECK (status IN ('pending', 'in_progress', 'completed')),
    created_at  TIMESTAMP   NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMP   NOT NULL DEFAULT NOW()
);

-- ─────────────────────────────────────────────
-- INDEXES
-- ─────────────────────────────────────────────
CREATE INDEX idx_tasks_user_id  ON tasks(user_id);
CREATE INDEX idx_tasks_status   ON tasks(status);
CREATE INDEX idx_tasks_priority ON tasks(priority);

-- ─────────────────────────────────────────────
-- SAMPLE SEED DATA  (optional — remove if not needed)
-- ─────────────────────────────────────────────
-- Password for seed user is: password123
INSERT INTO users (username, email, password) VALUES
('demo', 'demo@example.com',
 'pbkdf2:sha256:600000$abc123$hashedpasswordhere');

-- Seeds tasks for demo user (id=1)
INSERT INTO tasks (user_id, title, description, priority, status) VALUES
(1, 'Set up Flask project structure',       'Create app.py, templates, static folders',             'high',   'completed'),
(1, 'Implement PostgreSQL integration',     'Connect psycopg2, create schema, test queries',        'high',   'completed'),
(1, 'Build REST API endpoints',             'CRUD for tasks: GET, POST, PUT, DELETE',               'high',   'in_progress'),
(1, 'Add JWT or session authentication',    'Register, login, logout with hashed passwords',        'high',   'completed'),
(1, 'Integrate Flask-SocketIO',             'Real-time task broadcast on add/update/delete',        'medium', 'in_progress'),
(1, 'Build analytics module with Pandas',   'Compute stats: total, completed, pending, avg/day',    'medium', 'pending'),
(1, 'Design landing page UI',               'Hero section, features, tech stack, auth modal',       'low',    'completed'),
(1, 'Design dashboard UI',                  'Sidebar, task list, analytics view, live feed',        'low',    'pending'),
(1, 'Write README with setup instructions', 'Installation, env setup, how to run',                  'medium', 'pending'),
(1, 'Record demo video',                    '2-3 min walkthrough of all features',                  'low',    'pending');
