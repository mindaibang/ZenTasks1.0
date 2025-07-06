import sqlite3
import hashlib
import pandas as pd

# ------------------ Database ------------------

def get_connection():
    return sqlite3.connect("database.db")


def create_tables():
    conn = get_connection()
    cursor = conn.cursor()

    # Departments
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS departments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL
    )
    """)

    # Users
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        full_name TEXT,
        email TEXT,
        phone TEXT,
        role TEXT CHECK(role IN ('admin', 'manager', 'member')) NOT NULL,
        department_id INTEGER,
        approved INTEGER DEFAULT 0,
        FOREIGN KEY(department_id) REFERENCES departments(id)
    )
    """)

    # Tasks
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        description TEXT,
        priority TEXT,
        status TEXT DEFAULT 'To Do',
        start_date TEXT,
        due_date TEXT,
        assigned_to INTEGER,
        created_by INTEGER,
        department_id INTEGER,
        FOREIGN KEY(assigned_to) REFERENCES users(id),
        FOREIGN KEY(created_by) REFERENCES users(id),
        FOREIGN KEY(department_id) REFERENCES departments(id)
    )
    """)

    conn.commit()
    conn.close()


# ------------------ Password Hashing ------------------

def hash_password(password):
    return hashlib.sha1(password.encode()).hexdigest()


def verify_password(password, hashed):
    return hash_password(password) == hashed


# ------------------ Admin ------------------

def ensure_admin_exists():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = 'admin'")
    admin = cursor.fetchone()
    if not admin:
        cursor.execute("INSERT INTO users (username, password_hash, full_name, role, approved) VALUES (?, ?, ?, ?, ?)",
                       ('admin', hash_password('admin123'), 'Default Admin', 'admin', 1))
        conn.commit()
    conn.close()


# ------------------ Departments ------------------

def add_department(name):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO departments (name) VALUES (?)", (name,))
    conn.commit()
    conn.close()


def get_departments():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name FROM departments")
    departments = cursor.fetchall()
    conn.close()
    return departments


# ------------------ Users ------------------

def check_login(username, password):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT id, role, approved, full_name FROM users
    WHERE username=? AND password_hash=?
    """, (username, hash_password(password)))
    user = cursor.fetchone()
    conn.close()
    return user


def get_pending_users():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT id, username, full_name, role FROM users WHERE approved=0
    """)
    users = cursor.fetchall()
    conn.close()
    return users


def approve_user(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET approved=1 WHERE id=?", (user_id,))
    conn.commit()
    conn.close()


def get_all_users():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT id, username, full_name, department_id FROM users WHERE approved=1
    """)
    users = cursor.fetchall()
    conn.close()
    return users


def get_user_department(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT department_id FROM users WHERE id=?
    """, (user_id,))
    dept = cursor.fetchone()
    conn.close()
    return dept[0] if dept else None


# ------------------ Tasks ------------------

def add_task(title, description, priority, start_date, due_date, assigned_to, created_by, department_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO tasks (title, description, priority, start_date, due_date, assigned_to, created_by, department_id)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (title, description, priority, start_date, due_date, assigned_to, created_by, department_id))
    conn.commit()
    conn.close()


def get_all_tasks():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT t.id, t.title, t.description, t.priority, t.status,
           t.start_date, t.due_date, u.full_name as assigned_to, d.name as department
    FROM tasks t
    JOIN users u ON t.assigned_to = u.id
    JOIN departments d ON t.department_id = d.id
    """)
    tasks = cursor.fetchall()
    conn.close()
    return tasks


def get_tasks_for_user(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT id, title, description, priority, status, start_date, due_date
    FROM tasks
    WHERE assigned_to=?
    """, (user_id,))
    tasks = cursor.fetchall()
    conn.close()
    return tasks


def save_task_updates(df_tasks):
    conn = get_connection()
    cursor = conn.cursor()
    for _, row in df_tasks.iterrows():
        cursor.execute("""
        UPDATE tasks
        SET status=?, priority=?
        WHERE id=?
        """, (row["Status"], row["Priority"], row["ID"]))
    conn.commit()
    conn.close()


def get_tasks_summary():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT status, COUNT(*) FROM tasks GROUP BY status
    """)
    summary = {status: count for status, count in cursor.fetchall()}
    conn.close()
    return summary


def get_tasks_summary_by_department(department_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT status, COUNT(*) FROM tasks
    WHERE department_id=?
    GROUP BY status
    """, (department_id,))
    summary = {status: count for status, count in cursor.fetchall()}
    conn.close()
    return summary


def get_tasks_as_df():
    tasks = get_all_tasks()
    df = pd.DataFrame(tasks, columns=[
        "ID", "Title", "Description", "Priority", "Status",
        "Start Date", "Due Date", "Assigned To", "Department"
    ])
    return df
