"""Authentication utilities: password hashing and session helpers."""
import hashlib
import streamlit as st

SESSION_USER_ID = "user_id"
SESSION_ROLE = "role"
SESSION_EMAIL = "email"
SESSION_NAME = "name"


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def verify_password(password: str, hashed: str) -> bool:
    return hash_password(password) == hashed


def set_session(user_id, role: str, email: str, name: str):
    st.session_state[SESSION_USER_ID] = user_id
    st.session_state[SESSION_ROLE] = role
    st.session_state[SESSION_EMAIL] = email
    st.session_state[SESSION_NAME] = name


def clear_session():
    for key in [SESSION_USER_ID, SESSION_ROLE, SESSION_EMAIL, SESSION_NAME]:
        if key in st.session_state:
            del st.session_state[key]


def is_logged_in():
    return st.session_state.get(SESSION_USER_ID) is not None and st.session_state.get(SESSION_ROLE)


def get_current_user_id():
    return st.session_state.get(SESSION_USER_ID)


def get_current_role():
    return st.session_state.get(SESSION_ROLE)


def get_current_email():
    return st.session_state.get(SESSION_EMAIL)


def get_current_name():
    return st.session_state.get(SESSION_NAME)


def require_hr():
    if get_current_role() != "hr":
        st.error("Access denied. HR only.")
        st.stop()


def require_employee():
    if get_current_role() != "employee":
        st.error("Access denied. Employee only.")
        st.stop()
