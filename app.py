import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import plotly.express as px
from st_aggrid import AgGrid, GridOptionsBuilder
from utils import *
from datetime import date

# ✅ Init DB + Admin mặc định
create_tables()
ensure_admin_exists()

st.set_page_config(page_title="Task Manager", layout="wide")
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
    user_id = st.session_state["user_id"]
    st.sidebar.success(f"👤 {st.session_state['full_name']} ({role})")

    st.title("📊 Dashboard")

    # Define tabs based on role
    tabs = []
    if role == "admin":
        tabs = st.tabs(["🏢 Departments", "👥 Users", "📝 Tasks", "📈 Reports"])
    elif role == "manager":
        tabs = st.tabs(["👥 Users", "📝 Tasks", "📈 Reports"])
    else:  # member
        tabs = st.tabs(["📝 My Tasks"])

    # ---------- Departments Tab (Admin Only) ----------
    if role == "admin":
        with tabs[0]:
            st.header("🏢 Manage Departments")
            new_dept = st.text_input("Add New Department")
            if st.button("Add Department"):
                add_department(new_dept)
                st.success(f"✅ Added department: {new_dept}")
                st.rerun()

            st.write("📋 Existing Departments:")
            for dept in get_departments():
                st.write(f"- {dept[1]}")

    # ---------- Users Tab (Admin & Manager) ----------
    if role in ["admin", "manager"]:
        with tabs[1 if role == "admin" else 0]:
            st.header("👥 Manage Users")
            if role == "admin":
                pending_users = get_pending_users()
                st.subheader("Pending Users for Approval")
                if pending_users:
                    for user in pending_users:
                        st.write(f"- **{user[2]}** ({user[1]}, {user[3]})")
                        if st.button(f"✅ Approve {user[1]}", key=f"approve_{user[0]}"):
                            approve_user(user[0])
                            st.success(f"✅ Approved {user[1]}")
                            st.rerun()
                else:
                    st.info("✅ No pending users.")

            st.subheader("All Approved Users")
            users = get_all_users()
            if role == "manager":
                users = [u for u in users if u[3] == get_user_department(user_id)]
            if users:
                for u in users:
                    st.write(f"- {u[1]} ({u[2]}, {u[3]})")
            else:
                st.info("📭 No users found.")

    # ---------- Tasks Tab ----------
    if role in ["admin", "manager"]:
        with tabs[2 if role == "admin" else 1]:
            st.header("📝 Manage Tasks")
            # Add Task Form
            task_title = st.text_input("Task Title")
            task_description = st.text_area("Description")
            task_priority = st.selectbox("Priority", ["High", "Medium", "Low"])
            task_start_date = st.date_input("Start Date", date.today())
            task_due_date = st.date_input("Due Date", date.today())
            assigned_users = get_all_users()
            if role == "manager":
                assigned_users = [u for u in assigned_users if u[3] == get_user_department(user_id)]
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
                    user_id,  # created_by
                    assigned_to[3]  # department_id
                )
                st.success(f"✅ Task '{task_title}' added.")
                st.rerun()

            # Excel-like Grid
            st.subheader("📋 Task Overview")
            tasks = get_all_tasks()
            if role == "manager":
                tasks = [t for t in tasks if t[8] == get_user_department(user_id)]
            df_tasks = pd.DataFrame(tasks, columns=["ID", "Title", "Description", "Priority", "Status", "Start Date", "Due Date", "Assigned To", "Department"])
            if not df_tasks.empty:
                gb = GridOptionsBuilder.from_dataframe(df_tasks)
                gb.configure_pagination()
                gb.configure_default_column(editable=True, groupable=True)
                gb.configure_column("Status", cellEditor='agSelectCellEditor', cellEditorParams={'values': ['To Do', 'In Progress', 'Done']})
                grid_options = gb.build()

                grid_response = AgGrid(df_tasks, gridOptions=grid_options, height=400, width='100%', reload_data=True)

                updated_df = grid_response['data']
                save_task_updates(updated_df)
            else:
                st.info("📭 No tasks found.")

    if role == "member":
        with tabs[0]:
            st.header("📝 My Tasks")
            tasks = get_tasks_for_user(user_id)
            if tasks:
                df_tasks = pd.DataFrame(tasks, columns=["ID", "Title", "Description", "Priority", "Status", "Start Date", "Due Date"])
                st.dataframe(df_tasks)
            else:
                st.info("📭 No tasks assigned.")

    # ---------- Reports Tab ----------
    if role in ["admin", "manager"]:
        with tabs[3 if role == "admin" else 2]:
            st.header("📈 Reports")
            summary = get_tasks_summary()
            if role == "manager":
                summary = get_tasks_summary_by_department(get_user_department(user_id))
            if summary:
                st.subheader("📊 Task Status Pie Chart")
                fig1, ax1 = plt.subplots()
                ax1.pie(summary.values(), labels=summary.keys(), autopct='%1.1f%%')
                st.pyplot(fig1)

                st.subheader("📅 Task Timeline (Gantt Chart)")
                df_gantt = get_tasks_as_df()
                fig2 = px.timeline(
                    df_gantt,
                    x_start="Start Date",
                    x_end="Due Date",
                    y="Assigned To",
                    color="Status",
                    title="Task Progress Timeline"
                )
                fig2.update_yaxes(autorange="reversed")
                st.plotly_chart(fig2)
            else:
                st.info("📭 No tasks to report.")
