"""
Leave Management: Employee request, HR listing (approve/reject), Employee leave dashboard.
"""
import streamlit as st
from datetime import date, timedelta
from utils.auth import is_logged_in, get_current_role, get_current_user_id, require_hr, require_employee
from models.employee import get_employee_by_id, get_departments, get_all_employees
from models.leave import (
    create_leave,
    get_all_leaves,
    get_leaves_for_employee,
    get_leave_by_id,
    update_leave_status,
    get_leave_stats_for_employee,
)
from models.notification import create_notification


def employee_leave_request():
    require_employee()
    emp_id = get_current_user_id()
    emp = get_employee_by_id(emp_id)
    if not emp:
        st.error("Employee not found.")
        return
    st.markdown(
        '<p style="font-size:1.35rem; font-weight:600; color:#1e293b; margin-bottom:0.5rem;">'
        '<i class="fa fa-calendar-plus" style="color:#4CAF50; margin-right:8px;"></i>Apply for Leave</p>',
        unsafe_allow_html=True,
    )
    dept_name = "-"
    if emp.department_id:
        depts = get_departments()
        dept_name = next((d.name for d in depts if d.id == emp.department_id), "-")
    st.text_input("Employee Name", value=emp.name, disabled=True)
    st.text_input("Department", value=dept_name, disabled=True)
    from_date = st.date_input("From Date", value=date.today())
    to_date = st.date_input("To Date", value=date.today())
    if to_date < from_date:
        st.error("To date must be >= From date.")
        return
    total_days = (to_date - from_date).days + 1
    st.metric("Total leave days", total_days)
    reason = st.text_area("Reason", placeholder="Reason for leave")
    if st.button("Submit"):
        if not reason or not reason.strip():
            st.error("Please enter a reason.")
            return
        leave = create_leave(
            emp_id, emp.department_id, from_date, to_date, total_days, reason.strip()
        )
        # Notify HR (receiver_id: we need an HR id; use first HR)
        from database.db import get_session
        from database.db_models import HR
        session = get_session()
        hr_list = session.query(HR).limit(1).all()
        session.close()
        if hr_list:
            create_notification(
                sender_id=emp_id,
                receiver_id=hr_list[0].id,
                sender_type="employee",
                message=f"Leave request from {emp.name} ({from_date} to {to_date}, {total_days} days). Reason: {reason[:50]}...",
                ref_leave_id=leave.id,
                receiver_type="hr",
            )
        st.success("Leave request submitted. HR will be notified.")
        st.balloons()


def hr_leave_listing():
    require_hr()
    from database.db import get_session
    from database.db_models import HR
    session = get_session()
    hr_list = session.query(HR).limit(1).all()
    session.close()
    hr_id = hr_list[0].id if hr_list else 0

    st.markdown(
        '<p style="font-size:1.35rem; font-weight:600; color:#1e293b; margin-bottom:0.5rem;">'
        '<i class="fa fa-clipboard-list" style="color:#4CAF50; margin-right:8px;"></i>Leave Requests</p>',
        unsafe_allow_html=True,
    )
    leaves = get_all_leaves()
    employees = {e.id: e for e in get_all_employees()}
    depts = {d.id: d.name for d in get_departments()}
    if not leaves:
        st.info("No leave requests.")
        return
    for lv in leaves:
        emp = employees.get(lv.employee_id)
        emp_name = emp.name if emp else "-"
        dept_name = depts.get(lv.department_id, "-")
        with st.expander(f"{emp_name} | {lv.from_date} to {lv.to_date} | {lv.status}", expanded=(lv.status == "Pending")):
            st.write(f"**Department:** {dept_name} | **Days:** {lv.total_days}")
            st.write(f"**Reason:** {lv.reason or '-'}")
            if lv.status == "Pending":
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("Approve", key=f"app_{lv.id}"):
                        update_leave_status(lv.id, "Approved")
                        if emp:
                            create_notification(
                                sender_id=hr_id,
                                receiver_id=lv.employee_id,
                                sender_type="hr",
                                message=f"Your leave ({lv.from_date} to {lv.to_date}) has been Approved.",
                                ref_leave_id=lv.id,
                                receiver_type="employee",
                            )
                        st.success("Approved.")
                        st.rerun()
                with col2:
                    if st.button("Reject", key=f"rej_{lv.id}"):
                        st.session_state[f"reject_leave_id"] = lv.id
                if st.session_state.get("reject_leave_id") == lv.id:
                    comment = st.text_area("Rejection comment", key=f"comment_{lv.id}")
                    if st.button("Confirm Reject", key=f"conf_rej_{lv.id}"):
                        update_leave_status(lv.id, "Rejected", comment)
                        if emp:
                            create_notification(
                                sender_id=hr_id,
                                receiver_id=lv.employee_id,
                                sender_type="hr",
                                message=f"Your leave ({lv.from_date} to {lv.to_date}) has been Rejected. Comment: {comment}",
                                ref_leave_id=lv.id,
                                receiver_type="employee",
                            )
                        del st.session_state["reject_leave_id"]
                        st.rerun()
            else:
                if lv.hr_comment:
                    st.write(f"**HR Comment:** {lv.hr_comment}")


def employee_leave_dashboard():
    require_employee()
    emp_id = get_current_user_id()
    today = date.today()
    stats = get_leave_stats_for_employee(emp_id, month=today.month, year=today.year)
    st.markdown(
        '<p style="font-size:1.35rem; font-weight:600; color:#1e293b; margin-bottom:0.5rem;">'
        '<i class="fa fa-calendar-alt" style="color:#4CAF50; margin-right:8px;"></i>My Leave Dashboard</p>',
        unsafe_allow_html=True,
    )
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Leave taken this month", stats["total_days"])
    with col2:
        st.metric("Pending", stats["pending"])
    with col3:
        st.metric("Approved", stats["approved"])
    with col4:
        st.metric("Rejected", stats["rejected"])
    leaves = get_leaves_for_employee(emp_id)
    if leaves:
        import pandas as pd
        df = pd.DataFrame([
            {"From": l.from_date, "To": l.to_date, "Days": l.total_days, "Reason": (l.reason or "")[:40], "Status": l.status}
            for l in leaves[:20]
        ])
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("No leave records.")


def main():
    if not is_logged_in():
        st.warning("Please login first.")
        return
    role = get_current_role()
    if role == "hr":
        hr_leave_listing()
    else:
        # Tabs: Request Leave | My Leave Dashboard
        tab1, tab2 = st.tabs(["Apply for Leave", "My Leave Dashboard"])
        with tab1:
            employee_leave_request()
        with tab2:
            employee_leave_dashboard()
