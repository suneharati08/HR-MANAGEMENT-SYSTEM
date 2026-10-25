"""
Attendance Calendar: Big calendar view with present/absent per day.
HR: dropdown to select any employee. Employee: sees own calendar only.
Click on a date to see full details (date, present/absent, worked hrs, status, etc.).
"""
import streamlit as st
import calendar
from datetime import date, timedelta
from utils.auth import is_logged_in, get_current_user_id, get_current_role
from models.employee import get_employees_for_dropdown
from models.attendance import get_attendance_for_employee, get_attendance_by_employee_and_date


def _month_range(year: int, month: int):
    """First and last date of the month."""
    first = date(year, month, 1)
    last_day = calendar.monthrange(year, month)[1]
    last = date(year, month, last_day)
    return first, last


def _build_calendar_grid(year: int, month: int):
    """Returns a list of 6 rows (weeks), each row is 7 elements (weekday 0=Mon). Use 0 for empty cell."""
    cal = calendar.Calendar(firstweekday=0)  # Monday = 0
    weeks = cal.monthdayscalendar(year, month)
    # Pad to 6 rows for consistent layout
    while len(weeks) < 6:
        weeks.append([0] * 7)
    return weeks


def main():
    if not is_logged_in():
        st.warning("Please login first.")
        return

    role = get_current_role()
    user_id = get_current_user_id()

    st.markdown(
        '<p style="font-size:1.5rem; font-weight:600; color:#1e293b; margin-bottom:0.5rem;">'
        '<i class="fa fa-calendar-days" style="color:#4CAF50; margin-right:8px;"></i>Attendance Calendar</p>',
        unsafe_allow_html=True,
    )

    # Employee selector: HR sees dropdown, Employee sees only self
    if role == "hr":
        employees = get_employees_for_dropdown()
        if not employees:
            st.warning("No employees found.")
            return
        emp_options = {f"{e.name} ({e.email})": e.id for e in employees}
        emp_sel = st.selectbox("Select Employee", list(emp_options.keys()), key="cal_emp_sel")
        emp_id = emp_options[emp_sel]
    else:
        emp_id = user_id
        emp_sel = None

    # Month/Year navigation
    if "cal_year" not in st.session_state:
        st.session_state["cal_year"] = date.today().year
    if "cal_month" not in st.session_state:
        st.session_state["cal_month"] = date.today().month

    col_nav1, col_nav2, col_nav3 = st.columns([1, 2, 1])
    with col_nav1:
        if st.button("◀ Previous Month", use_container_width=True):
            if st.session_state["cal_month"] == 1:
                st.session_state["cal_month"] = 12
                st.session_state["cal_year"] -= 1
            else:
                st.session_state["cal_month"] -= 1
            st.rerun()
    with col_nav2:
        month_name = date(st.session_state["cal_year"], st.session_state["cal_month"], 1).strftime("%B %Y")
        st.markdown(
            f'<p style="text-align:center; font-size:1.25rem; font-weight:600; color:#1e293b;">{month_name}</p>',
            unsafe_allow_html=True,
        )
    with col_nav3:
        if st.button("Next Month ▶", use_container_width=True):
            if st.session_state["cal_month"] == 12:
                st.session_state["cal_month"] = 1
                st.session_state["cal_year"] += 1
            else:
                st.session_state["cal_month"] += 1
            st.rerun()

    year = st.session_state["cal_year"]
    month = st.session_state["cal_month"]
    first, last = _month_range(year, month)
    attendances = get_attendance_for_employee(emp_id, from_date=first, to_date=last)
    att_by_date = {}
    for a in attendances:
        att_by_date[a.date] = a

    # Legend
    st.markdown(
        '<div style="display:flex; gap:1.5rem; margin-bottom:1rem; flex-wrap:wrap;">'
        '<span style="display:inline-flex; align-items:center; gap:6px;"><span style="width:20px; height:20px; background:#4CAF50; border-radius:4px;"></span> Present</span>'
        '<span style="display:inline-flex; align-items:center; gap:6px;"><span style="width:20px; height:20px; background:#f44336; border-radius:4px;"></span> Absent</span>'
        '<span style="display:inline-flex; align-items:center; gap:6px;"><span style="width:20px; height:20px; background:#e0e0e0; border-radius:4px;"></span> No record</span>'
        '</div>',
        unsafe_allow_html=True,
    )

    # Weekday headers (Mon–Sun)
    weekdays = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    header_cols = st.columns(7)
    for i, wd in enumerate(weekdays):
        with header_cols[i]:
            st.markdown(
                f'<p style="text-align:center; font-weight:600; color:#64748b; font-size:0.85rem;">{wd}</p>',
                unsafe_allow_html=True,
            )

    # Which day was clicked (set below when a day button is pressed)
    if "cal_selected_date" not in st.session_state:
        st.session_state["cal_selected_date"] = None

    weeks = _build_calendar_grid(year, month)
    for week in weeks:
        cols = st.columns(7)
        for i, day in enumerate(week):
            with cols[i]:
                if day == 0:
                    st.markdown('<div style="height:72px;"></div>', unsafe_allow_html=True)
                    continue
                d = date(year, month, day)
                att = att_by_date.get(d)
                if att:
                    label = "P" if att.present_status == "Present" else "A"
                    if att.present_status == "Present":
                        bg_color = "#4CAF50"
                        text_color = "white"
                    else:
                        bg_color = "#f44336"
                        text_color = "white"
                else:
                    label = "-"
                    bg_color = "#e0e0e0"
                    text_color = "#555"
                # Colored box showing day and P/A/-
                st.markdown(
                    f'<div style="background:{bg_color}; color:{text_color}; border-radius:8px; padding:8px; '
                    f'text-align:center; font-weight:600; font-size:0.95rem; margin-bottom:4px;">'
                    f'{day} <span style="font-size:0.75rem; opacity:0.95;">({label})</span></div>',
                    unsafe_allow_html=True,
                )
                if st.button(
                    "View",
                    key=f"cal_{year}_{month}_{day}",
                    use_container_width=True,
                    type="secondary",
                ):
                    st.session_state["cal_selected_date"] = d
                    st.rerun()

    # Details for selected date
    st.markdown("---")
    selected_date = st.session_state.get("cal_selected_date")
    if selected_date:
        st.markdown(
            f'<p style="font-size:1.1rem; font-weight:600; color:#1e293b;">'
            f'<i class="fa fa-info-circle" style="color:#4CAF50;"></i> Details for {selected_date.strftime("%A, %d %B %Y")}</p>',
            unsafe_allow_html=True,
        )
        att = get_attendance_by_employee_and_date(emp_id, selected_date)
        if att:
            st.markdown(
                f'<div style="background:#f8fafc; padding:1rem; border-radius:8px; border-left:4px solid #4CAF50;">'
                f'<p><strong>Date:</strong> {att.date}</p>'
                f'<p><strong>Present / Absent:</strong> {att.present_status}</p>'
                f'<p><strong>Status:</strong> {att.status}</p>'
                f'<p><strong>Worked hours:</strong> {att.working_hours}</p>'
                f'</div>',
                unsafe_allow_html=True,
            )
        else:
            st.info("No attendance record for this date.")
        if st.button("Clear selection"):
            st.session_state["cal_selected_date"] = None
            st.rerun()