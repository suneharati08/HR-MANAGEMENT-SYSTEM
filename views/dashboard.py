"""
Dashboard: HR and Employee dashboards with modern metrics and Plotly analytics charts.
"""
import streamlit as st
from datetime import date, timedelta
import pandas as pd
from utils.auth import is_logged_in, get_current_role, get_current_user_id, require_hr, require_employee
from models.employee import get_all_employees
from models.attendance import (
    count_present_today,
    count_absent_today,
    get_attendance_for_employee,
)
from models.leave import count_pending_leaves, get_leave_stats_for_employee

# Plotly for modern charts
try:
    import plotly.express as px
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False


def _metric_card_style():
    """Inject subtle spacing for metric row."""
    st.markdown(
        "<style>.stMetric { margin-bottom: 0.5rem; }</style>",
        unsafe_allow_html=True,
    )


def _chart_card(title: str):
    """Section title for a chart card."""
    st.markdown(
        f'<p class="dashboard-section-title">'
        f'<i class="fa fa-chart-bar" style="color:#4CAF50; margin-right:8px;"></i>{title}</p>',
        unsafe_allow_html=True,
    )


def hr_dashboard():
    require_hr()
    today = date.today()
    total_employees = len(get_all_employees())
    present_today = count_present_today(today)
    absent_today = count_absent_today(today)
    pending_leaves = count_pending_leaves()

    st.markdown(
        '<p style="font-size:1.5rem; font-weight:600; color:#1e293b; margin-bottom:0.5rem;">'
        '<i class="fa fa-chart-line" style="color:#4CAF50; margin-right:8px;"></i>HR Dashboard</p>',
        unsafe_allow_html=True,
    )
    _metric_card_style()

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Employees", total_employees, help="Total registered employees")
    with col2:
        st.metric("Present Today", present_today, help="Marked present today")
    with col3:
        st.metric("Absent Today", absent_today, help="Marked absent today")
    with col4:
        st.metric("Pending Leave Requests", pending_leaves, help="Awaiting approval")

    st.markdown("<br>", unsafe_allow_html=True)

    # Attendance overview (last 7 days) - Plotly bar chart
    try:
        from database.db import get_session
        from database.db_models import Attendance
        session = get_session()
        start = today - timedelta(days=7)
        rows = session.query(Attendance).filter(Attendance.date >= start).all()
        session.close()
        if rows:
            df = pd.DataFrame([
                {"date": r.date, "present": 1 if r.present_status == "Present" else 0, "status": r.status}
                for r in rows
            ])
            by_date = df.groupby("date").agg({"present": "sum", "status": "count"}).reset_index()
            by_date.columns = ["date", "Present", "Total"]
            by_date["date"] = pd.to_datetime(by_date["date"]).dt.strftime("%a %d %b")

            if HAS_PLOTLY:
                fig = go.Figure()
                fig.add_trace(
                    go.Bar(
                        x=by_date["date"],
                        y=by_date["Present"],
                        name="Present",
                        marker_color="#4CAF50",
                        marker_line_color="#388E3C",
                        marker_line_width=1,
                    )
                )
                fig.add_trace(
                    go.Bar(
                        x=by_date["date"],
                        y=by_date["Total"],
                        name="Total marked",
                        marker_color="#94a3b8",
                        marker_line_color="#64748b",
                        marker_line_width=1,
                        opacity=0.7,
                    )
                )
                fig.update_layout(
                    barmode="group",
                    height=320,
                    margin=dict(l=40, r=40, t=40, b=60),
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    font=dict(size=12, color="#1e293b"),
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                    xaxis=dict(showgrid=False, zeroline=False),
                    yaxis=dict(showgrid=True, gridcolor="rgba(0,0,0,0.06)", zeroline=False),
                    showlegend=True,
                )
                _chart_card("Attendance overview (last 7 days)")
                st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": True, "displaylogo": False})
            else:
                _chart_card("Attendance overview (last 7 days)")
                st.bar_chart(by_date.set_index("date"))
        else:
            _chart_card("Attendance overview (last 7 days)")
            st.info("No attendance data in the last 7 days.")
    except Exception:
        _chart_card("Attendance overview (last 7 days)")
        st.warning("Could not load attendance chart.")

    # Leave overview - Plotly
    try:
        from database.db import get_session
        from database.db_models import Leave
        session = get_session()
        leaves = session.query(Leave).all()
        session.close()
        if leaves:
            df_leave = pd.DataFrame([{"status": l.status} for l in leaves])
            count_by_status = df_leave.groupby("status").size().reset_index(name="count")
            status_order = ["Pending", "Approved", "Rejected"]
            count_by_status["status"] = pd.Categorical(count_by_status["status"], categories=status_order, ordered=True)
            count_by_status = count_by_status.sort_values("status")

            if HAS_PLOTLY:
                colors = {"Pending": "#f59e0b", "Approved": "#4CAF50", "Rejected": "#ef4444"}
                count_by_status["color"] = count_by_status["status"].map(colors)
                fig2 = go.Figure(
                    data=[
                        go.Bar(
                            x=count_by_status["status"],
                            y=count_by_status["count"],
                            marker_color=count_by_status["color"],
                            marker_line_color="rgba(0,0,0,0.1)",
                            marker_line_width=1,
                            text=count_by_status["count"],
                            textposition="outside",
                            textfont=dict(size=14, color="#1e293b"),
                        )
                    ]
                )
                fig2.update_layout(
                    height=300,
                    margin=dict(l=40, r=40, t=40, b=50),
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    font=dict(size=12, color="#1e293b"),
                    xaxis=dict(showgrid=False, zeroline=False),
                    yaxis=dict(showgrid=True, gridcolor="rgba(0,0,0,0.06)", zeroline=False),
                    showlegend=False,
                )
                _chart_card("Leave overview")
                st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar": True, "displaylogo": False})
            else:
                _chart_card("Leave overview")
                st.bar_chart(count_by_status.set_index("status"))
        else:
            _chart_card("Leave overview")
            st.info("No leave data yet.")
    except Exception:
        _chart_card("Leave overview")
        st.info("No leave data yet.")


def employee_dashboard():
    require_employee()
    emp_id = get_current_user_id()
    today = date.today()
    month, year = today.month, today.year

    st.markdown(
        '<p style="font-size:1.5rem; font-weight:600; color:#1e293b; margin-bottom:0.5rem;">'
        '<i class="fa fa-user" style="color:#4CAF50; margin-right:8px;"></i>Employee Dashboard</p>',
        unsafe_allow_html=True,
    )
    _metric_card_style()

    stats = get_leave_stats_for_employee(emp_id, month=month, year=year)
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Leave taken this month", stats["total_days"], help="Total days in current month")
    with col2:
        st.metric("Pending", stats["pending"], help="Pending leave requests")
    with col3:
        st.metric("Approved", stats["approved"], help="Approved leaves")
    with col4:
        st.metric("Rejected", stats["rejected"], help="Rejected leaves")

    att_list = get_attendance_for_employee(
        emp_id,
        from_date=date(year, month, 1),
        to_date=today,
    )
    present_days = sum(1 for a in att_list if a.present_status == "Present")
    absent_days = sum(1 for a in att_list if a.present_status == "Absent")

    st.markdown("<br>", unsafe_allow_html=True)
    _chart_card("My attendance this month")
    c1, c2 = st.columns(2)
    with c1:
        st.metric("Present days", present_days)
    with c2:
        st.metric("Absent days", absent_days)

    # Optional: small donut or bar for leave breakdown
    if HAS_PLOTLY and (stats["pending"] + stats["approved"] + stats["rejected"] > 0):
        st.markdown("<br>", unsafe_allow_html=True)
        _chart_card("Leave status breakdown")
        fig = go.Figure(
            data=[
                go.Pie(
                    labels=["Pending", "Approved", "Rejected"],
                    values=[stats["pending"], stats["approved"], stats["rejected"]],
                    hole=0.55,
                    marker_colors=["#f59e0b", "#4CAF50", "#ef4444"],
                    textinfo="label+value",
                    textposition="outside",
                    hoverinfo="label+percent",
                )
            ]
        )
        fig.update_layout(
            height=280,
            margin=dict(l=20, r=20, t=30, b=20),
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(size=12, color="#1e293b"),
            showlegend=True,
            legend=dict(orientation="h", yanchor="bottom", y=0, xanchor="center", x=0.5),
        )
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False, "displaylogo": False})


def main():
    if not is_logged_in():
        st.warning("Please login first.")
        return
    role = get_current_role()
    if role == "hr":
        hr_dashboard()
    else:
        employee_dashboard()
