import streamlit as st
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder, JsCode
from utils import *
from datetime import date

# ---------------- INIT -----------------
create_tables()
ensure_admin_exists()
st.set_page_config(page_title="Task Manager", layout="wide")

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
        st.header("📋 Task Overview (Excel-like)")
        tasks = get_all_tasks()
        df_tasks = pd.DataFrame(tasks, columns=["ID", "Title", "Description", "Priority", "Status", "Start Date", "Due Date", "Assigned To", "Department"])

        # Progress Bar Renderer
        progress_renderer = JsCode("""
        function(params) {
            let value = 0;
            if(params.value === 'Done') { value = 100; }
            else if(params.value === 'In Progress') { value = 50; }
            else { value = 0; }
            return '<div style="width:100%;background:#ddd"><div style="width:' + value + '%;background:#76c7c0;height:10px"></div></div>';
        }
        """)

        # Ag-Grid Options
        gb = GridOptionsBuilder.from_dataframe(df_tasks)
        gb.configure_pagination()
        gb.configure_column("Status", editable=True, cellEditor='agSelectCellEditor', cellEditorParams={'values': ['To Do', 'In Progress', 'Done']})
        gb.configure_column("Priority", cellEditor='agSelectCellEditor', cellEditorParams={'values': ['High', 'Medium', 'Low']})
        gb.configure_column("Progress", valueGetter='data.Status', cellRenderer=progress_renderer)
        grid_options = gb.build()

        grid_response = AgGrid(df_tasks, gridOptions=grid_options, height=500, width='100%', reload_data=True)
        updated_df = grid_response['data']
        save_task_updates(updated_df)

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
        st.header("📈 Reports (Pie Chart)")
        summary = get_tasks_summary()
        if summary:
            st.write(summary)
        else:
            st.info("📭 No tasks to report.")
