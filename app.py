"""
Streamlit HRMS System - Main entry point.
Professional HRMS with role-based access, dashboard, and modular pages.
Run: streamlit run app.py
"""
import streamlit as st
import os
import sys

# Ensure project root is on path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database.db import init_db
from utils.auth import is_logged_in, get_current_role, get_current_name, clear_session, get_current_user_id
from models.notification import get_unread_count
from models.user_session import log_logout

# Initialize database and tables
init_db()

# Page config
st.set_page_config(
    page_title="Streamlit HRMS System",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="expanded",
)

# Load custom CSS and Font Awesome for icons
st.markdown(
    '<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css" crossorigin="anonymous">',
    unsafe_allow_html=True,
)
CSS_PATH = os.path.join(os.path.dirname(__file__), "assets", "style.css")
if os.path.exists(CSS_PATH):
    with open(CSS_PATH, "r", encoding="utf-8") as f:
        content = f.read()
    # Remove @import FA from CSS since we load it above
    content = content.replace("@import url('https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css');", "")
    st.markdown(f"<style>{content}</style>", unsafe_allow_html=True)


def render_login_or_register():
    """Redirect to login page logic (import and run)."""
    from views.login import main as login_main
    login_main()
    return


def sidebar_nav():
    """Premium sidebar: logo, user card, nav menu, notifications, logout."""
    with st.sidebar:
        st.markdown(
            '<div class="sidebar-logo">'
            '<i class="fa fa-building"></i>'
            '<span>Streamlit HRMS</span></div>',
            unsafe_allow_html=True,
        )
        if not is_logged_in():
            return None
        name = (get_current_name() or "User").strip()
        role = (get_current_role() or "").strip()
        role_display = role.upper() if role else "USER"
        st.markdown(
            f'<div class="sidebar-user-card">'
            f'<div class="name"><i class="fa fa-user-circle" style="margin-right:6px; color:#4CAF50;"></i>{name}</div>'
            f'<div class="role">{role_display}</div></div>',
            unsafe_allow_html=True,
        )

        try:
            from streamlit_option_menu import option_menu
            selected = option_menu(
                menu_title="Navigation",
                options=[
                    "Dashboard",
                    "Employees",
                    "Attendance",
                    "Attendance Calendar",
                    "Worked Hours",
                    "Leave",
                    "Notifications",
                ],
                icons=["house", "people", "calendar-check", "calendar3", "clock", "calendar-x", "bell"],
                default_index=0,
                styles={
                    "container": {"padding": "0", "margin": "0"},
                    "nav-link": {
                        "font-size": "14px",
                        "padding": "0.6rem 1rem",
                        "border-radius": "8px",
                        "margin": "2px 0",
                    },
                    "nav-link-selected": {
                        "background": "linear-gradient(135deg, #4CAF50 0%, #388E3C 100%)",
                        "color": "white",
                        "font-weight": "500",
                    },
                    "icon": {"font-size": "1rem"},
                },
            )
        except ImportError:
            selected = st.radio(
                "Menu",
                ["Dashboard", "Employees", "Attendance", "Attendance Calendar", "Worked Hours", "Leave", "Notifications"],
                label_visibility="collapsed",
            )

        user_id = get_current_user_id()
        role = get_current_role()
        unread = get_unread_count(user_id, role) if user_id and role else 0
        notif_class = "sidebar-notif has-unread" if unread > 0 else "sidebar-notif"
        badge = f' <span class="badge">{unread}</span>' if unread > 0 else ""
        st.markdown(
            f'<div class="{notif_class}">'
            f'<i class="fa fa-bell"></i>'
            f'<span>Notifications{badge}</span></div>',
            unsafe_allow_html=True,
        )
        st.markdown("---")
        if st.button("Logout", use_container_width=True):
            if get_current_role() == "employee":
                log_logout(get_current_user_id())
            clear_session()
            st.rerun()
        return selected


def main_content(selected):
    """Render the selected page."""
    if selected == "Dashboard":
        from views.dashboard import main as dash_main
        dash_main()
    elif selected == "Employees":
        from views.employee_module import main as emp_main
        emp_main()
    elif selected == "Attendance":
        from views.attendance_module import main as att_main
        att_main()
    elif selected == "Attendance Calendar":
        from views.attendance_calendar import main as cal_main
        cal_main()
    elif selected == "Worked Hours":
        from views.worked_hours import main as wh_main
        wh_main()
    elif selected == "Leave":
        from views.leave_module import main as leave_main
        leave_main()
    elif selected == "Notifications":
        from views.notification import main as notif_main
        notif_main()
    else:
        from views.dashboard import main as dash_main
        dash_main()


def main():
    if not is_logged_in():
        render_login_or_register()
        return
    selected = sidebar_nav()
    if selected:
        main_content(selected)


if __name__ == "__main__":
    main()
