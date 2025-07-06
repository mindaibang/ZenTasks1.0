import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date
from utils import *

# ---------------- INIT -----------------
create_tables()
ensure_admin_exists()
st.set_page_config(page_title="🌟 Task Manager", layout="wide")

# ---------------- SIDEBAR -----------------
st.sidebar.title("🔐 Login / Register")
if "page" not in st.session_state:
    st.session_state["page"] = "login"

if st.sidebar.button("📝 Register"):
    st.session_state["page"] = "register"
if st.sidebar.button("🚪 Logout"):
    st.session_state.clear()
    st.rerun()

# ---------------- REGISTER -----------------
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
        try:
            register_user(username, password, full_name, email, phone, department[0])
            st.success("🎉 Registered! Wait for admin approval.")
            st.session_state["page"] = "login"
            st.rerun()
        except:
            st.error("⚠ Username already exists!")

# ---------------- LOGIN -----------------
elif st.session_state["page"] == "login":
    st.title("🔐 Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        user = check_login(username, password)
        if user:
            if user[2] == 0:
                st.warning("⏳ Account pending approval.")
            else:
                st.session_state["user_id"], st.session_state["role"], _, st.session_state["name"] = user
                st.session_state["page"] = "dashboard"
                st.rerun()
        else:
            st.error("❌ Wrong username or password.")

# ---------------- DASHBOARD -----------------
elif st.session_state["page"] == "dashboard":
    st.title(f"📊 Dashboard - Welcome, {st.session_state['name']}")
    role = st.session_state["role"]
    user_id = st.session_state["user_id"]

    tabs = st.tabs(["🏢 Departments", "👥 Users", "📋 Tasks", "🗂 Kanban", "📈 Reports"])

    # -------- TAB: DEPARTMENTS (Admin only) ---------
    if role == "admin":
        with tabs[0]:
            st.header("🏢 Manage Departments")
            new_dept = st.text_input("Add New Department")
            if st.button("Add Department"):
                add_department(new_dept)
                st.success(f"✅ Added department: {new_dept}")
                st.rerun()
            st.subheader("📋 Existing Departments:")
            depts = get_departments()
            for dept in depts:
                st.write(f"- {dept[1]}")

    # -------- TAB: USERS (Admin & Manager) ---------
    if role in ["admin", "manager"]:
        with tabs[1]:
            st.header("👥 Manage Users")
            if role == "admin":
                st.subheader("⏳ Pending Users for Approval")
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

            st.subheader("📋 All Approved Users")
            approved_users = get_all_users()
            for u in approved_users:
                st.write(f"- {u[1]} ({u[2]}, Dept: {u[3]})")

    # -------- TAB: TASKS ---------
    with tabs[2]:
        st.header("📋 Task Overview")
        tasks = get_all_tasks()
        df_tasks = pd.DataFrame(tasks, columns=["ID", "Title", "Description", "Priority", "Status", "Start Date", "Due Date", "Assigned To", "Department"])
        if not df_tasks.empty:
            df_tasks["Status"] = df_tasks["Status"].map({
                "To Do": "🔴 To Do",
                "In Progress": "🟡 In Progress",
                "Done": "🟢 Done"
            })
            st.dataframe(df_tasks[["Title", "Priority", "Status", "Start Date", "Due Date", "Assigned To", "Department"]])
        else:
            st.info("📭 No tasks yet.")

        st.subheader("📝 Add New Task")
        task_title = st.text_input("Task Title")
        task_description = st.text_area("Description")
        task_priority = st.selectbox("Priority", ["High", "Medium", "Low"])
        task_start_date = st.date_input("Start Date", date.today())
        task_due_date = st.date_input("Due Date", date.today())
        assigned_users = get_all_users()
        if assigned_users:
            user_labels = [f"{u[1]} ({u[2]})" for u in assigned_users]
            selected_label = st.selectbox("Assign To", user_labels)
            selected_index = user_labels.index(selected_label)
            assigned_to_id = assigned_users[selected_index][0]
            department_id = assigned_users[selected_index][3]

            if st.button("Add Task"):
                add_task(task_title, task_description, task_priority,
                         task_start_date.strftime("%Y-%m-%d"),
                         task_due_date.strftime("%Y-%m-%d"),
                         assigned_to_id, user_id, department_id)
                st.success("✅ Task added!")
                st.rerun()
        else:
            st.warning("⚠ No users available. Please add users first.")

    # -------- TAB: KANBAN ---------
    with tabs[3]:
        st.header("🗂 Kanban View (coming soon...)")
        st.info("🚧 Feature in progress")

    # -------- TAB: REPORTS ---------
    with tabs[4]:
        st.header("📈 Reports")
        summary = get_tasks_summary()
        if summary:
            fig = px.pie(names=list(summary.keys()), values=list(summary.values()), title="Task Status Distribution")
            st.plotly_chart(fig)
            bar_data = pd.DataFrame.from_dict(summary, orient="index", columns=["Count"])
            fig_bar = px.bar(bar_data, x=bar_data.index, y="Count", title="Task Status Bar Chart")
            st.plotly_chart(fig_bar)
        else:
            st.info("📭 No tasks to report.")
