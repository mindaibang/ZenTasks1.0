import streamlit as st
import matplotlib.pyplot as plt
from utils import *
from datetime import date

# ✅ Init DB + Admin
create_tables()
ensure_admin_exists()

# Sidebar
st.sidebar.title("🔐 Login / Register")

if "page" not in st.session_state:
    st.session_state["page"] = "login"

if st.sidebar.button("📝 Register"):
    st.session_state["page"] = "register"

# ------------------ Register ------------------
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
        except sqlite3.IntegrityError:
            st.error("⚠️ Username already exists.")
        conn.close()

# ------------------ Login ------------------
elif st.session_state["page"] == "login":
    st.title("🔐 Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        user = check_login(username, password)
        if user:
            user_id, role, approved, full_name = user
            if not approved:
                st.warning("⏳ Account not approved.")
            else:
                st.session_state["user_id"] = user_id
                st.session_state["role"] = role
                st.session_state["full_name"] = full_name
                st.session_state["page"] = "dashboard"
                st.experimental_rerun()
        else:
            st.error("❌ Wrong username or password.")

# ------------------ Dashboard ------------------
elif st.session_state["page"] == "dashboard":
    role = st.session_state["role"]
    st.sidebar.success(f"👤 {st.session_state['full_name']} ({role})")

    if role == "admin":
        st.title("👑 Admin Dashboard")

        # Phòng ban
        st.subheader("🏢 Manage Departments")
        new_dept = st.text_input("Add new department")
        if st.button("Add Department"):
            add_department(new_dept)
            st.success(f"✅ Added department: {new_dept}")
            st.experimental_rerun()

        st.write("📋 Existing Departments:")
        for dept in get_departments():
            st.write(f"- {dept[1]}")

        # User approval
        st.subheader("👥 Approve New Users")
        for user in get_pending_users():
            st.write(f"- **{user[2]}** ({user[1]}, {user[3]})")
            if st.button(f"✅ Approve {user[1]}", key=f"approve_{user[0]}"):
                approve_user(user[0])
                st.success(f"✅ Approved {user[1]}")
                st.experimental_rerun()

        # Dashboard Pie Chart
        st.subheader("📊 Task Summary")
        summary = get_tasks_summary()
        if summary:
            fig, ax = plt.subplots()
            ax.pie(summary.values(), labels=summary.keys(), autopct='%1.1f%%')
            st.pyplot(fig)
        else:
            st.info("📭 No tasks found.")

# ------------------ Logout ------------------
if st.sidebar.button("🚪 Logout"):
    st.session_state.clear()
    st.experimental_rerun()
