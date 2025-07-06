import sqlite3
import hashlib

# ---------------- DB CONNECTION -----------------
def get_connection():
    return sqlite3.connect("database.db", check_same_thread=False)

# ---------------- DB INIT -----------------
def create_tables():
    conn = get_connection()
    c = conn.cursor()

    # Departments
    c.execute('''
        CREATE TABLE IF NOT EXISTS departments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL
        )
    ''')

    # Users
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            full_name TEXT,
            email TEXT,
            phone TEXT,
            department_id INTEGER,
            approved INTEGER DEFAULT 0,
            role TEXT DEFAULT "member",
            FOREIGN KEY(department_id) REFERENCES departments(id)
        )
    ''')

    # Tasks
    c.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            priority TEXT,
            status TEXT DEFAULT "To Do",
            start_date TEXT,
            due_date TEXT,
            assigned_to INTEGER,
            created_by INTEGER,
            department_id INTEGER,
            FOREIGN KEY(assigned_to) REFERENCES users(id),
            FOREIGN KEY(created_by) REFERENCES users(id),
            FOREIGN KEY(department_id) REFERENCES departments(id)
        )
    ''')

    conn.commit()
    conn.close()


# ---------------- DEFAULT ADMIN -----------------
def ensure_admin_exists():
    conn = get_connection()
    c = conn.cursor()

    # Check if admin user exists
    c.execute("SELECT * FROM users WHERE username='admin'")
    if not c.fetchone():
        password_hash = hash_password("admin123")
        c.execute('''
            INSERT INTO users (username, password, full_name, email, phone, department_id, approved, role)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', ("admin", password_hash, "Default Admin", "admin@task.com", "0000000000", None, 1, "admin"))
        conn.commit()

    conn.close()


# ---------------- UTILITY FUNCTIONS -----------------
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


# ---------------- USER FUNCTIONS -----------------
def register_user(username, password, full_name, email, phone, department_id):
    conn = get_connection()
    c = conn.cursor()
    password_hash = hash_password(password)
    c.execute('''
        INSERT INTO users (username, password, full_name, email, phone, department_id, approved, role)
        VALUES (?, ?, ?, ?, ?, ?, 0, "member")
    ''', (username, password_hash, full_name, email, phone, department_id))
    conn.commit()
    conn.close()

def check_login(username, password):
    conn = get_connection()
    c = conn.cursor()
    password_hash = hash_password(password)
    c.execute('''
        SELECT id, role, approved, full_name FROM users
        WHERE username=? AND password=?
    ''', (username, password_hash))
    user = c.fetchone()
    conn.close()
    return user

def get_pending_users():
    conn = get_connection()
    c = conn.cursor()
    c.execute('''
        SELECT id, username, full_name, role FROM users WHERE approved=0
    ''')
    users = c.fetchall()
    conn.close()
    return users

def approve_user(user_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute('UPDATE users SET approved=1 WHERE id=?', (user_id,))
    conn.commit()
    conn.close()

def get_all_users():
    conn = get_connection()
    c = conn.cursor()
    c.execute('''
        SELECT id, username, role, department_id FROM users WHERE approved=1
    ''')
    users = c.fetchall()
    conn.close()
    return users

# ---------------- DEPARTMENT FUNCTIONS -----------------
def get_departments():
    conn = get_connection()
    c = conn.cursor()
    c.execute('SELECT id, name FROM departments')
    departments = c.fetchall()
    conn.close()
    return departments

def add_department(name):
    conn = get_connection()
    c = conn.cursor()
    c.execute('INSERT INTO departments (name) VALUES (?)', (name,))
    conn.commit()
    conn.close()

# ---------------- TASK FUNCTIONS -----------------
def add_task(title, description, priority, start_date, due_date, assigned_to, created_by, department_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute('''
        INSERT INTO tasks (title, description, priority, status, start_date, due_date, assigned_to, created_by, department_id)
        VALUES (?, ?, ?, "To Do", ?, ?, ?, ?, ?)
    ''', (title, description, priority, start_date, due_date, assigned_to, created_by, department_id))
    conn.commit()
    conn.close()

def get_all_tasks():
    conn = get_connection()
    c = conn.cursor()
    c.execute('''
        SELECT t.id, t.title, t.description, t.priority, t.status, t.start_date, t.due_date,
               u.username as assigned_to, d.name as department
        FROM tasks t
        LEFT JOIN users u ON t.assigned_to = u.id
        LEFT JOIN departments d ON t.department_id = d.id
    ''')
    tasks = c.fetchall()
    conn.close()
    return tasks

def get_tasks_summary():
    conn = get_connection()
    c = conn.cursor()
    c.execute('SELECT status, COUNT(*) FROM tasks GROUP BY status')
    summary = {status: count for status, count in c.fetchall()}
    conn.close()
    return summary
