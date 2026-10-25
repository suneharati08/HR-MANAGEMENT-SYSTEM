"""
Notification page: list notifications, mark as read.
"""
import streamlit as st
from utils.auth import is_logged_in, get_current_user_id, get_current_role
from models.notification import get_notifications_for_user, mark_as_read, mark_all_as_read, get_unread_count


def main():
    if not is_logged_in():
        st.warning("Please login first.")
        return
    user_id = get_current_user_id()
    role = get_current_role()
    st.markdown(
        '<p style="font-size:1.35rem; font-weight:600; color:#1e293b; margin-bottom:0.5rem;">'
        '<i class="fa fa-bell" style="color:#4CAF50; margin-right:8px;"></i>Notifications</p>',
        unsafe_allow_html=True,
    )
    notifications = get_notifications_for_user(user_id, role)
    if st.button("Mark all as read"):
        mark_all_as_read(user_id, role)
        st.success("All marked as read.")
        st.rerun()
    if not notifications:
        st.info("No notifications.")
        return
    for n in notifications:
        if n.status == "Unread":
            icon_html = '<i class="fas fa-circle" style="color:#4CAF50; font-size:0.35rem; vertical-align:middle; margin-right:8px;"></i>'
        else:
            icon_html = '<i class="far fa-circle" style="color:#94a3b8; font-size:0.35rem; vertical-align:middle; margin-right:8px;"></i>'
        with st.container():
            st.markdown(f'{icon_html} **{n.message}**', unsafe_allow_html=True)
            st.caption(str(n.created_at) if n.created_at else "")
            if n.status == "Unread":
                if st.button("Mark read", key=f"read_{n.id}"):
                    mark_as_read(n.id)
                    st.rerun()
            st.divider()
