import streamlit as st
import pandas as pd
from datetime import datetime, time
from database import *
from datetime import timezone, timedelta
from streamlit_autorefresh import st_autorefresh
import time as tm


IST = timezone(timedelta(hours=5, minutes=30))

# =====================================================
# INIT
# =====================================================
create_tables()
initialize_default_data()

st.set_page_config(page_title="CTPL Employee Checklist System", layout="wide")
st.header("CTPL Employee Daily Checklist System")



# =====================================================
# AUTO REFRESH (10 sec)
# =====================================================
st_autorefresh(interval=10000, limit=None, key="refresh")


# =====================================================
# HELPERS
# =====================================================
def format_datetime(value):
    if not value:
        return "-"
    try:
        return pd.to_datetime(value).strftime("%d %b %Y %H:%M:%S")
    except:
        return value


def get_quarter(dt_str):
    if not dt_str:
        return "Not Completed"

    try:
        t = datetime.fromisoformat(dt_str).time()
    except:
        return "Invalid"

    if time(8, 0) <= t < time(11, 0):
        return "Q1 (8AM-11AM)"
    elif time(11, 0) <= t < time(13, 0):
        return "Q2 (11AM-1PM)"
    elif time(14, 0) <= t < time(16, 0):
        return "Q3 (2PM-4PM)"
    elif time(16, 0) <= t < time(18, 0):
        return "Q4 (4PM-6PM)"
    elif (time(18,0) <= t < time(23,59,59)) or (time(0,0) <= t < time(8,0)):
        return "Q5 (Outside Hours)"
    else:
        return "Invalid"


# =====================================================
# STATUS COLORS
# =====================================================
def color_status(status, current_time):
    if status == "Pending" and current_time >= time(18, 0):
        return '<div style="background:red;color:white;padding:5px;border-radius:6px;text-align:center;">🔴 OVERDUE</div>'

    elif status == "Completed":
        return '<div style="background:green;color:white;padding:5px;border-radius:6px;text-align:center;">✔ Completed</div>'

    elif status == "Pending":
        return '<div style="background:orange;color:black;padding:5px;border-radius:6px;text-align:center;">⏳ Pending</div>'

    return status


# =====================================================
# QUARTER COLORS
# =====================================================
def color_quarter(q):
    if q.startswith("Q1"):
        return '<div style="background:#3498db;color:white;padding:5px;border-radius:6px;text-align:center;">Q1 (8AM-11AM)</div>'
    elif q.startswith("Q2"):
        return '<div style="background:#9b59b6;color:white;padding:5px;border-radius:6px;text-align:center;">Q2 (11AM-1PM)</div>'
    elif q.startswith("Q3"):
        return '<div style="background:#f39c12;color:white;padding:5px;border-radius:6px;text-align:center;">Q3 (2PM-4PM)</div>'
    elif q.startswith("Q4"):
        return '<div style="background:#1abc9c;color:white;padding:5px;border-radius:6px;text-align:center;">Q4 (4PM-6PM)</div>'
    elif q.startswith("Q5"):
        return '<div style="background:gray;color:white;padding:5px;border-radius:6px;text-align:center;">Q5 (Outside Hours)</div>'
    else:
        return '<div style="background:gray;color:white;padding:5px;border-radius:6px;text-align:center;">N/A</div>'


# =====================================================
# LOGIN
# =====================================================
st.sidebar.header("Login")

employee_name = st.sidebar.text_input("Employee Name")
password = st.sidebar.text_input("Password", type="password")

if st.sidebar.button("Login"):
    user = login(employee_name, password)

    if user:
        st.session_state["user"] = user
        st.success("Login successful")
    else:
        st.error("Invalid credentials")


# =====================================================
# SESSION
# =====================================================
if "user" in st.session_state:

    user = st.session_state["user"]
    user_id = user[0]
    role = user[4]

    current_time = datetime.now(IST).time()
    overdue_time = time(18, 0)
   
    # =================================================
    # ADMIN DASHBOARD
    # =================================================
    if role == "admin":
        
        # =====================================================
        # EMPLOYEE ENROLLMENT
        # =====================================================
        st.sidebar.markdown("---")
        st.sidebar.subheader("Employee Enrollment")

        new_employee_name = st.sidebar.text_input(
            "New Employee Name"
        )

        new_department = st.sidebar.text_input(
            "Department"
        )

        new_password = st.sidebar.text_input(
            "Create Password",
            type="password"
        )

        if st.sidebar.button("Enroll Employee"):

            if (
                new_employee_name
                and new_department
                and new_password
            ):

                success, message = register_employee(
                    new_employee_name,
                    new_department,
                    new_password
                )

                if success:
                    st.sidebar.success(message)
                else:
                    st.sidebar.error(message)

            else:
                st.sidebar.warning("Please fill all fields")


        # =================================================
        # DATA
        # =================================================
        data = get_all_employee_status()

        df = pd.DataFrame(data, columns=[
            "Employee ID",
            "Employee Name",
            "Department",
            "Task",
            "Status",
            "Created Time",
            "Completed Time"
            ])

        df = df.dropna(subset=["Employee Name"])

        # =================================================
        # RAW COLUMNS (IMPORTANT)
        # =================================================
        df["Status_raw"] = df["Status"]
        df["Quarter_raw"] = df["Completed Time"].apply(get_quarter)

        page = st.sidebar.radio("Navigation", ["Admin Dashboard","Done"])
        if page == "Admin Dashboard":
            st.header("Admin Dashboard")

            # =================================================
            # REFRESH CONTROLS
            # =================================================
            col1, col2 = st.columns([1, 5])

            with col1:
                if st.button("🔄 Refresh"):
                    st.rerun()

            with col2:
                st.caption("Auto-refresh every 10 seconds enabled")
           

            
            # =================================================
            # OVERDUE LOGIC (RESTORED)
            # =================================================
            overdue_tasks = df[
                (df["Status_raw"] == "Pending") &
                (current_time >= overdue_time)
            ]

            if current_time >= overdue_time:
                if not overdue_tasks.empty:
                    st.error(
                        f"🚨 ALERT: {len(overdue_tasks)} overdue tasks detected after 6 PM!"
                    )
                    st.warning("Pending tasks must be completed immediately.")

            # =================================================
            # SORT OPTIONS
            # =================================================
            sort_option = st.selectbox(
                "Sort Options",
                [
                    "Employee Name (A-Z)",
                    "Pending First",
                
                ]
            )

            if sort_option == "Employee Name (A-Z)":
                df = df.sort_values(by=["Employee Name", "Task"])

            elif sort_option == "Pending First":
                df["sort_key"] = df["Status_raw"].apply(
                    lambda x: 0 if x == "Pending" else 1
                )
                df = df.sort_values(by=["sort_key", "Employee Name"])
                df.drop(columns=["sort_key"], inplace=True)


            # =================================================
            # UI FORMATTING
            # =================================================
            df["Status"] = df["Status_raw"].apply(
                lambda x: color_status(x, current_time)
            )

            df["Quarter"] = df["Quarter_raw"].apply(color_quarter)

            #df["Task"] = df.apply( lambda r: f'<div> {r}</div>', axis=1 )

            df["Created Time"] = df["Created Time"].apply(format_datetime)
            df["Completed Time"] = df["Completed Time"].apply(format_datetime)

            # =================================================
            # TABLE
            # =================================================
            st.subheader("All Tasks")

            # =================================================
            # DISPLAY DATAFRAME (HIDE RAW COLUMNS ONLY IN UI)
            # =================================================
            #df.drop(df[df["Status_raw"]=="Completed"].index,inplace=True)
            display_df = df[df["Status_raw"] != "Completed"].copy()
            display_df = display_df[
                [
                    col for col in display_df.columns
                    if col not in ["Status_raw", "Quarter_raw", "Completed Time", "Quarter"]
                ]
            ]
	
	
            st.write(
                display_df.to_html(
                    escape=False,
                    index=False
                ),
                unsafe_allow_html=True
            )
            
        elif page == "Done":

            st.markdown("## 📊 Task Completion Quarter-wise Breakdown")
            # =================================================
            # REFRESH CONTROLS
            # =================================================
            col1, col2 = st.columns([1, 5])

            with col1:
                if st.button("🔄 Refresh"):
                    st.rerun()

            with col2:
                st.caption("Auto-refresh every 10 seconds enabled")
                        

            # =================================================
            # QUARTER BREAKDOWN
            # =================================================

            quarters = [
                "Q1 (8AM-11AM)",
                "Q2 (11AM-1PM)",
                "Q3 (2PM-4PM)",
                "Q4 (4PM-6PM)",
                "Q5 (Outside Hours)"
            ]
            df["Created Time"] = df["Created Time"].apply(format_datetime)
            df["Completed Time"] = df["Completed Time"].apply(format_datetime)

            for q in quarters:

                st.markdown(color_quarter(q), unsafe_allow_html=True)

                subset = df[df["Quarter_raw"].str.contains(q.split()[0])][
                    ["Employee Name", "Task", "Created Time","Completed Time"]
                    ]

                if subset.empty:
                    st.write("No tasks")
                else:
                    st.write(
                        subset.to_html(
                            escape=False,
                            index=False
                        ),
                        unsafe_allow_html=True
                    )

    # =================================================
    # EMPLOYEE DASHBOARD
    # =================================================
    else:
        st.session_state.last_action_time = tm.time()
        st.header("Employee Dashboard")
        # =================================================
        # REFRESH CONTROLS
        # =================================================
        col1, col2 = st.columns([1, 5])

        with col1:
            if st.button("🔄 Refresh"):
                st.rerun()

        with col2:
            st.caption("Auto-refresh every 10 seconds enabled")



        task_input = st.text_input("Enter task")
        
        if st.button("Add Task"):
            if task_input:
                checklist_id = get_or_create_checklist(user_id)
                add_task(checklist_id, task_input)
                st.rerun()

        tasks = get_tasks(user_id)
        st.subheader("Today's Tasks")
        header1, header2, header3, header4, header5, header6=st.columns([2,4,4,3,3,4])
        header1.write("**TASK ID**")
        header2.write("**TASK DESCRIPTION**")
        header3.write("**STATUS**")
        header4.write("**CREATED TIME**")
        header5.write("**COMPLETED TIME**")
        header6.write("**DONE STATUS**")
      
        for task_id, task_desc, status, created, completed in tasks:

            col1, col2, col3, col4, col5,col6= st.columns([2,4, 4, 3, 3, 4])

            with col1:
                st.write(task_id)
            with col2:
                st.write(task_desc)
            with col3:  
                st.markdown(
                      color_status(status, current_time),
                    unsafe_allow_html=True
                )

            with col4:
                st.write(format_datetime(created))
            with col5:
                st.write(format_datetime(completed))

            with col6:
                if status == "Pending":
                    st.markdown("""<style>
                        div.stButton > button {border: 2px solid  #ccc;
                        border-radius: 6px;
                        }
                        </style>
                        """, unsafe_allow_html=True)
                    if st.button(f"Click Done Task{task_id}"):
                        if (tm.time() - st.session_state.last_action_time) < 5:
                            st.warning("Wait before completing another task")
                            #st.stop()
                            tm.sleep(5)
                            complete_task(task_id)
                            st.session_state.last_action_time = tm.time()
                            st.rerun()
                        else:
                            complete_task(task_id)
                            st.session_state.last_action_time = tm.time()
                            st.rerun()
                else:
                        st.write("✔")


    # =====================================================
    # LOGOUT
    # =====================================================
    st.sidebar.markdown("---")

    if st.sidebar.button("Logout"):
        st.session_state.clear()
        st.rerun()
