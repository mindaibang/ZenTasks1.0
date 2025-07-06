-- Bảng phòng ban
CREATE TABLE IF NOT EXISTS departments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL
);

-- Bảng người dùng
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    full_name TEXT,
    email TEXT,
    phone TEXT,
    role TEXT CHECK(role IN ('admin', 'manager', 'member')) NOT NULL DEFAULT 'member',
    department_id INTEGER,
    approved INTEGER DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (department_id) REFERENCES departments(id)
);

-- Bảng công việc
CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT,
    priority TEXT CHECK(priority IN ('High', 'Medium', 'Low')) DEFAULT 'Medium',
    status TEXT CHECK(status IN ('To Do', 'In Progress', 'Done')) DEFAULT 'To Do',
    start_date DATE,
    due_date DATE,
    assigned_to INTEGER,
    created_by INTEGER,
    department_id INTEGER,
    FOREIGN KEY (assigned_to) REFERENCES users(id),
    FOREIGN KEY (created_by) REFERENCES users(id),
    FOREIGN KEY (department_id) REFERENCES departments(id)
);
