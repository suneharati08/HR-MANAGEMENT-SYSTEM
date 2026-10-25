"""
Attendance Module: HR can add/view attendance for all; Employee can add/view own only.
"""
import streamlit as st
from datetime import date, timedelta
import pandas as pd
from utils.auth import is_logged_in, require_hr, get_current_user_id, get_current_role
from models.employee import get_employees_for_dropdown
from models.attendance import (
    add_attendance,
    get_attendance_by_employee_and_date,
    get_attendance_for_employee,
    get_attendance_on_date,
)
from models.leave import get_leaves_for_employee


def attendance_entry():
    require_hr()
    st.markdown(
        '<p style="font-size:1.35rem; font-weight:600; color:#1e293b; margin-bottom:0.5rem;">'
        '<i class="fa fa-calendar-check" style="color:#4CAF50; margin-right:8px;"></i>Attendance Entry</p>',
        unsafe_allow_html=True,
    )
    employees = get_employees_for_dropdown()
    if not employees:
        st.warning("Add employees first.")
        return
    emp_options = {f"{e.name} ({e.email})": e.id for e in employees}
    with st.form("att_form"):
        att_date = st.date_input("Date", value=date.today())
        emp_sel = st.selectbox("Employee", list(emp_options.keys()))
        status = st.selectbox("Status", ["Active", "WFH", "Inactive"])
        present_status = st.selectbox("Present", ["Present", "Absent"])
        working_hours = st.number_input("Working hours", min_value=0.0, max_value=24.0, value=8.0, step=0.5)
        if st.form_submit_button("Add"):
            emp_id = emp_options[emp_sel]
            existing = get_attendance_by_employee_and_date(emp_id, att_date)
            if existing:
                st.warning("Attendance for this employee on this date already exists. Edit not implemented in form; use DB if needed.")
            else:
                add_attendance(emp_id, att_date, status, present_status, working_hours)
                st.success("Attendance added.")
    if st.button("Go to Attendance Dashboard"):
        st.session_state["att_page"] = "dashboard"
        st.rerun()


def attendance_dashboard():
    require_hr()
    st.markdown(
        '<p style="font-size:1.35rem; font-weight:600; color:#1e293b; margin-bottom:0.5rem;">'
        '<i class="fa fa-chart-bar" style="color:#4CAF50; margin-right:8px;"></i>Attendance Dashboard</p>',
        unsafe_allow_html=True,
    )
    employees = get_employees_for_dropdown()
    if not employees:
        st.info("No employees.")
        return
    emp_sel = st.selectbox(
        "Select Employee",
        [f"{e.name} ({e.email})" for e in employees],
        key="att_emp_sel",
    )
    emp_id = employees[[f"{e.name} ({e.email})" for e in employees].index(emp_sel)].id
    today = date.today()
    from_d = date(today.year, today.month, 1)
    att_list = get_attendance_for_employee(emp_id, from_date=from_d, to_date=today)
    leaves = get_leaves_for_employee(emp_id)
    approved_leaves = [l for l in leaves if l.status == "Approved"]
    # Working days in month so far
    total_working_days = 0
    d = from_d
    while d <= today:
        if d.weekday() < 5:
            total_working_days += 1
        d += timedelta(days=1)
    present_days = sum(1 for a in att_list if a.present_status == "Present")
    absent_days = sum(1 for a in att_list if a.present_status == "Absent")
    leave_days_this_month = 0
    for l in approved_leaves:
        if l.from_date.year == today.year and l.from_date.month == today.month:
            leave_days_this_month += l.total_days
    st.metric("Total working days (month so far)", total_working_days)
    st.metric("Present days", present_days)
    st.metric("Absent days", absent_days)
    st.metric("Leave days (this month)", leave_days_this_month)
    if att_list:
        df = pd.DataFrame([
            {"Date": a.date, "Status": a.status, "Present": a.present_status, "Hours": a.working_hours}
            for a in att_list[:31]
        ])
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("No attendance records for this period.")
    if st.button("Back to Attendance Entry"):
        st.session_state["att_page"] = "entry"
        st.rerun()


def employee_attendance_entry():
    """Employee: mark own attendance only (no other employees)."""
    emp_id = get_current_user_id()
    if not emp_id:
        st.warning("Please login first.")
        return
    st.markdown(
        '<p style="font-size:1.35rem; font-weight:600; color:#1e293b; margin-bottom:0.5rem;">'
        '<i class="fa fa-calendar-plus" style="color:#4CAF50; margin-right:8px;"></i>Mark My Attendance</p>',
        unsafe_allow_html=True,
    )
    with st.form("emp_att_form"):
        att_date = st.date_input("Date", value=date.today())
        status = st.selectbox("Status", ["Active", "WFH", "Inactive"])
        present_status = st.selectbox("Present", ["Present", "Absent"])
        working_hours = st.number_input("Working hours", min_value=0.0, max_value=24.0, value=8.0, step=0.5)
        if st.form_submit_button("Submit"):
            existing = get_attendance_by_employee_and_date(emp_id, att_date)
            if existing:
                st.warning("You already have attendance recorded for this date.")
            else:
                add_attendance(emp_id, att_date, status, present_status, working_hours)
                st.success("Your attendance has been recorded.")
    if st.button("View My Attendance"):
        st.session_state["att_page"] = "dashboard"
        st.rerun()


def employee_attendance_view():
    """Employee view: own attendance only (read-only dashboard)."""
    emp_id = get_current_user_id()
    if not emp_id:
        st.warning("Please login first.")
        return
    st.markdown(
        '<p style="font-size:1.35rem; font-weight:600; color:#1e293b; margin-bottom:0.5rem;">'
        '<i class="fa fa-calendar-check" style="color:#4CAF50; margin-right:8px;"></i>My Attendance</p>',
        unsafe_allow_html=True,
    )
    if st.button("Mark My Attendance"):
        st.session_state["att_page"] = "entry"
        st.rerun()
    st.markdown("---")
    today = date.today()
    from_d = date(today.year, today.month, 1)
    att_list = get_attendance_for_employee(emp_id, from_date=from_d, to_date=today)
    leaves = get_leaves_for_employee(emp_id)
    approved_leaves = [l for l in leaves if l.status == "Approved"]
    total_working_days = 0
    d = from_d
    while d <= today:
        if d.weekday() < 5:
            total_working_days += 1
        d += timedelta(days=1)
    present_days = sum(1 for a in att_list if a.present_status == "Present")
    absent_days = sum(1 for a in att_list if a.present_status == "Absent")
    leave_days_this_month = 0
    for l in approved_leaves:
        if l.from_date.year == today.year and l.from_date.month == today.month:
            leave_days_this_month += l.total_days
    st.metric("Total working days (month so far)", total_working_days)
    st.metric("Present days", present_days)
    st.metric("Absent days", absent_days)
    st.metric("Leave days (this month)", leave_days_this_month)
    if att_list:
        df = pd.DataFrame([
            {"Date": a.date, "Status": a.status, "Present": a.present_status, "Hours": a.working_hours}
            for a in att_list[:31]
        ])
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("No attendance records for this period.")


def main():
    if not is_logged_in():
        st.warning("Please login first.")
        return
    role = get_current_role()
    if role == "employee":
        page = st.session_state.get("att_page", "entry")
        if page == "dashboard":
            employee_attendance_view()
        else:
            employee_attendance_entry()
        return
    page = st.session_state.get("att_page", "entry")
    if page == "dashboard":
        attendance_dashboard()
    else:
        attendance_entry()
