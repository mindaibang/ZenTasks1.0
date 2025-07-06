import streamlit as st
import matplotlib.pyplot as plt
from utils import *
from datetime import date

# ✅ Init DB + Admin mặc định
create_tables()
ensure_admin_exists()

st.sidebar.title("🔐 Login / Register")

# Session page control
if "page" not in st.session_state:
    st.session_state["page"] = "login"

# Navigation buttons
if st.sidebar.button("📝 Register"):
    st.session_state["page"] = "register"
if st.sidebar.button("🚪 Logout"):
    st.session_state.clear()
    st.rerun()

# ------------------ Register Page ------------------
if st.session_state["page"] == "register":
    st.title("📝 Register Account")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    full_name = st.text_input("Full Name")
    email = st.text_input("Email")
    phone = st.text_input("Phone")
    departments = get_departments()
    department = st.selectbox("Department", departments, format_func=lambda x: x[1])

    if st.button("Register"):
        conn = get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO users (username, password_hash, full_name, email, phone, role, department_id, approved)
                VALUES (?, ?, ?, ?, ?, 'member', ?, 0)
            """, (username, hash_password(password), full_name, email, phone, department[0]))
            conn.commit()
            st.success("🎉 Account registered. Waiting for admin approval.")
            st.session_state["page"] = "login"
            st.rerun()
        except sqlite3.IntegrityError:
            st.error("⚠️ Username already exists.")
        conn.close()

# ------------------ Login Page ------------------
elif st.session_state["page"] == "login":
    st.title("🔐 Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        user = check_login(username, password)
        if user:
            user_id, role, approved, full_name = user
            if not approved:
                st.warning("⏳ Account not approved yet.")
            else:
                st.session_state["user_id"] = user_id
                st.session_state["role"] = role
                st.session_state["full_name"] = full_name
                st.session_state["page"] = "dashboard"
                st.rerun()
        else:
            st.error("❌ Wrong username or password.")

# ------------------ Dashboard Page ------------------
elif st.session_state["page"] == "dashboard":
    role = st.session_state["role"]
    st.sidebar.success(f"👤 {st.session_state['full_name']} ({role})")

    if role == "admin":
        st.title("👑 Admin Dashboard")

        # ---------- Manage Departments ----------
        st.subheader("🏢 Manage Departments")
        new_dept = st.text_input("Add New Department")
        if st.button("Add Department"):
            add_department(new_dept)
            st.success(f"✅ Added department: {new_dept}")
            st.rerun()

        st.write("📋 Existing Departments:")
        for dept in get_departments():
            st.write(f"- {dept[1]}")

        # ---------- Approve Users ----------
        st.subheader("👥 Approve New Users")
        pending_users = get_pending_users()
        if pending_users:
            for user in pending_users:
                st.write(f"- **{user[2]}** ({user[1]}, {user[3]})")
                if st.button(f"✅ Approve {user[1]}", key=f"approve_{user[0]}"):
                    approve_user(user[0])
                    st.success(f"✅ Approved {user[1]}")
                    st.rerun()
        else:
            st.info("✅ No pending users.")

        # ---------- Manage Tasks ----------
        st.subheader("📝 Manage Tasks")
        task_title = st.text_input("Task Title")
        task_description = st.text_area("Description")
        task_priority = st.selectbox("Priority", ["High", "Medium", "Low"])
        task_start_date = st.date_input("Start Date", date.today())
        task_due_date = st.date_input("Due Date", date.today())
        assigned_users = get_all_users()
        if assigned_users:
            assigned_to = st.selectbox("Assign To", assigned_users, format_func=lambda u: f"{u[1]} ({u[2]})")
        else:
            st.warning("⚠ No users to assign. Add users first.")
            assigned_to = None

        if st.button("Add Task") and assigned_to:
            add_task(
                task_title,
                task_description,
                task_priority,
                task_start_date.strftime("%Y-%m-%d"),
                task_due_date.strftime("%Y-%m-%d"),
                assigned_to[0],  # user id
                st.session_state["user_id"],  # created_by
                assigned_to[3]  # department_id
            )
            st.success(f"✅ Task '{task_title}' added.")
            st.rerun()

        # ---------- Task Summary ----------
        st.subheader("📋 All Tasks")
        summary = get_tasks_summary()
        if summary:
            for status, count in summary.items():
                st.write(f"- **{status}**: {count}")
            # Show pie chart
            fig, ax = plt.subplots()
            ax.pie(summary.values(), labels=summary.keys(), autopct='%1.1f%%')
            st.pyplot(fig)
        else:
            st.info("📭 No tasks yet.")

    else:
        st.title("📋 User Dashboard")
        st.info("🚧 Features for non-admin users coming soon!")
