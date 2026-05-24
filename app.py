import streamlit as st
import pandas as pd
from datetime import datetime, time
from database import *

# =====================================================
# INIT
# =====================================================
create_tables()
initialize_default_data()

st.set_page_config(page_title="CTPL Employee Checklist System", layout="wide")
st.title("CTPL Employee Daily Checklist System")


# =====================================================
# AUTO REFRESH (10 sec)
# =====================================================
st.markdown("""
<script>
setTimeout(function(){
    window.location.reload();
}, 10000);
</script>
""", unsafe_allow_html=True)


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

    if time(9, 0) <= t < time(11, 0):
        return "Q1 (8AM-11AM)"
    elif time(11, 0) <= t < time(13, 0):
        return "Q2 (11AM-1PM)"
    elif time(14, 0) <= t < time(16, 0):
        return "Q3 (2PM-4PM)"
    elif time(16, 0) <= t < time(18, 0):
        return "Q4 (4PM-6PM)"
    else:
        return "Outside Hours"


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
        return '<div style="background:#3498db;color:white;padding:5px;border-radius:6px;text-align:center;">Q1</div>'
    elif q.startswith("Q2"):
        return '<div style="background:#9b59b6;color:white;padding:5px;border-radius:6px;text-align:center;">Q2</div>'
    elif q.startswith("Q3"):
        return '<div style="background:#f39c12;color:white;padding:5px;border-radius:6px;text-align:center;">Q3</div>'
    elif q.startswith("Q4"):
        return '<div style="background:#1abc9c;color:white;padding:5px;border-radius:6px;text-align:center;">Q4</div>'
    else:
        return '<div style="background:gray;color:white;padding:5px;border-radius:6px;text-align:center;">N/A</div>'


# =====================================================
# LOGIN
# =====================================================
st.sidebar.header("Login")

employee_name = st.sidebar
