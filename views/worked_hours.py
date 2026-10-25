"""
Worked Hours (Work Monitor): Time spent on the application per employee.
Employee: sees own monitor — by date, total hours, login/logout times.
HR: sees all employees — select employee to see same; view all sessions with employee name.
"""
import streamlit as st
import pandas as pd
from datetime import date, timedelta, datetime
from utils.auth import is_logged_in, get_current_user_id, get_current_role
from models.employee import get_employees_for_dropdown, get_employee_by_id
from models.user_session import (
    get_sessions_for_employee,
    get_daily_totals_for_employee,
    get_all_employees_sessions,
)


def _fmt_dt(dt):
    if dt is None:
        return "—"
    if hasattr(dt, "strftime"):
        return dt.strftime("%d %b %Y %I:%M %p")
    return str(dt)


def _fmt_duration(minutes):
    """Format duration (in minutes) as 'X hr Y min Z sec' for readability."""
    if minutes is None or minutes < 0:
        return "—"
    total_secs = int(round(minutes * 60))
    hours = total_secs // 3600
    mins = (total_secs % 3600) // 60
    secs = total_secs % 60
    parts = []
    if hours > 0:
        parts.append(f"{hours} hr")
    if mins > 0 or (hours == 0 and secs == 0):
        parts.append(f"{mins} min")
    if secs > 0 or (hours == 0 and mins == 0):
        parts.append(f"{secs} sec")
    return " ".join(parts) if parts else "0 sec"


def main():
    if not is_logged_in():
        st.warning("Please login first.")
        return

    role = get_current_role()
    user_id = get_current_user_id()

    st.markdown(
        '<p style="font-size:1.5rem; font-weight:600; color:#1e293b; margin-bottom:0.5rem;">'
        '<i class="fa fa-clock" style="color:#4CAF50; margin-right:8px;"></i>Worked Hours Monitor</p>',
        unsafe_allow_html=True,
    )

    # Date range filter - default to current month (1st to last day)
    today = date.today()
    first_of_month = today.replace(day=1)
    # Compute last day of current month
    if today.month == 12:
        last_of_month = today.replace(day=31)
    else:
        next_month_first = today.replace(month=today.month + 1, day=1)
        last_of_month = next_month_first - timedelta(days=1)
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        from_date = st.date_input("From date", value=first_of_month, key="wh_from")
    with col_f2:
        to_date = st.date_input("To date", value=last_of_month, key="wh_to")
    if from_date > to_date:
        st.error("From date must be before or equal to To date.")
        return

    if role == "hr":
        employees = get_employees_for_dropdown()
        if not employees:
            st.warning("No employees found.")
            return
        emp_options = {f"{e.name} ({e.email})": e.id for e in employees}
        emp_sel = st.selectbox("Select Employee", list(emp_options.keys()), key="wh_emp_sel")
        emp_id = emp_options[emp_sel]
        emp_name = next((e.name for e in employees if e.id == emp_id), "")
    else:
        emp_id = user_id
        emp = get_employee_by_id(emp_id)
        emp_name = emp.name if emp else ""

    st.markdown(
        f'<p style="font-size:1rem; color:#64748b;">Showing hours for: <strong>{emp_name}</strong></p>',
        unsafe_allow_html=True,
    )

    # Daily totals (per date)
    daily = get_daily_totals_for_employee(emp_id, from_date=from_date, to_date=to_date)
    if not daily:
        st.info("No worked hours recorded for this period. Login and logout to track time.")
    else:
        st.markdown(
            '<p style="font-size:1.1rem; font-weight:600; color:#1e293b;">'
            '<i class="fa fa-chart-bar" style="color:#4CAF50;"></i> Total hours by date</p>',
            unsafe_allow_html=True,
        )
        rows = []
        for d in daily:
            rows.append({
                "Date": d["date"],
                "Time worked": _fmt_duration(d["total_minutes"]),
                "Sessions": d["sessions_count"],
            })
        df_daily = pd.DataFrame(rows)
        st.dataframe(df_daily, use_container_width=True, hide_index=True)

        st.markdown(
            '<p style="font-size:1.1rem; font-weight:600; color:#1e293b; margin-top:1rem;">'
            '<i class="fa fa-list" style="color:#4CAF50;"></i> Session details (Login / Logout / Duration)</p>',
            unsafe_allow_html=True,
        )
        all_sessions = []
        for d in daily:
            for s in d["sessions"]:
                all_sessions.append({
                    "Date": s.login_at.date() if hasattr(s.login_at, "date") else s.login_at,
                    "Login": _fmt_dt(s.login_at),
                    "Logout": _fmt_dt(s.logout_at),
                    "Duration": _fmt_duration(s.duration_minutes),
                })
        if all_sessions:
            df_sess = pd.DataFrame(all_sessions)
            st.dataframe(df_sess, use_container_width=True, hide_index=True)

    # HR: optional view of all employees' sessions
    if role == "hr":
        st.markdown("---")
        st.markdown(
            '<p style="font-size:1.1rem; font-weight:600; color:#1e293b;">'
            '<i class="fa fa-users" style="color:#4CAF50;"></i> All employees — recent sessions</p>',
            unsafe_allow_html=True,
        )
        all_sessions = get_all_employees_sessions(from_date=from_date, to_date=to_date)
        if not all_sessions:
            st.info("No sessions in this period.")
        else:
            emp_map = {e.id: e.name for e in get_employees_for_dropdown()}
            rows = []
            for s in all_sessions[:100]:
                rows.append({
                    "Employee": emp_map.get(s.employee_id, s.employee_id),
                    "Login": _fmt_dt(s.login_at),
                    "Logout": _fmt_dt(s.logout_at),
                    "Duration": _fmt_duration(s.duration_minutes),
                })
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
