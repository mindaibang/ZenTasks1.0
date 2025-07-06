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
    st.title("📝 Register")
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
            st.error("⚠ Username exists!")

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

    tabs = st.tabs(["📋 Task Overview", "📝 Add Task", "📈 Reports"])

    # -------- TAB: TASK OVERVIEW ---------
    with tabs[0]:
        st.header("📋 Task Overview")
        tasks = get_all_tasks()
        df_tasks = pd.DataFrame(tasks, columns=["ID", "Title", "Description", "Priority", "Status", "Start Date", "Due Date", "Assigned To", "Department"])
        if not df_tasks.empty:
            df_tasks["Status Color"] = df_tasks["Status"].map({
                "To Do": "🔴 To Do",
                "In Progress": "🟡 In Progress",
                "Done": "🟢 Done"
            })
            st.dataframe(df_tasks[["Title", "Priority", "Status Color", "Start Date", "Due Date", "Assigned To", "Department"]])
        else:
            st.info("📭 No tasks yet.")

    # -------- TAB: ADD TASK ---------
    with tabs[1]:
        st.header("📝 Add New Task")
        task_title = st.text_input("Task Title")
        task_description = st.text_area("Description")
        task_priority = st.selectbox("Priority", ["High", "Medium", "Low"])
        task_start_date = st.date_input("Start Date", date.today())
        task_due_date = st.date_input("Due Date", date.today())
        assigned_users = get_all_users()
        if assigned_users:
            assigned_to = st.selectbox("Assign To", assigned_users, format_func=lambda u: f"{u[1]} ({u[2]})")
            if st.button("Add Task"):
                add_task(task_title, task_description, task_priority,
                         task_start_date.strftime("%Y-%m-%d"),
                         task_due_date.strftime("%Y-%m-%d"),
                         assigned_to[0], user_id, assigned_to[3])
                st.success("✅ Task added!")
                st.experimental_rerun()
        else:
            st.warning("⚠ No users available.")

    # -------- TAB: REPORTS ---------
    with tabs[2]:
        st.header("📈 Reports")
        summary = get_tasks_summary()
        if summary:
            fig = px.pie(names=list(summary.keys()), values=list(summary.values()), title="Task Status Distribution")
            st.plotly_chart(fig)
        else:
            st.info("📭 No tasks to report.")
