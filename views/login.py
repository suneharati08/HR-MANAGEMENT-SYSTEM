"""
Login and HR Registration - Professional compact card UI.
"""
import streamlit as st
from models.hr import get_hr_by_email, get_hr_count, create_hr
from models.employee import get_employee_by_email
from models.user_session import log_login
from utils.auth import (
    hash_password,
    verify_password,
    set_session,
    is_logged_in,
)


def _inject_login_page_styles():
    st.markdown(
        """
        <style>
        [data-testid="stSidebar"] { display: none !important; }
        /* Force login into a narrow box card - target Streamlit's main content */
        section[data-testid="stAppViewContainer"] > div:first-child { max-width: 440px !important; margin: 0 auto !important; }
        section.main { max-width: 440px !important; margin-left: auto !important; margin-right: auto !important; }
        .main .block-container { max-width: 440px !important; }
        </style>
        """,
        unsafe_allow_html=True,
    )
    st.markdown('<div class="login-page-marker"></div>', unsafe_allow_html=True)


def _login_card_header(title: str, subtitle: str):
    st.markdown(
        '<div class="login-logo">'
        '<div class="login-logo-icon"><i class="fa fa-building"></i></div>'
        f'<div class="login-title">{title}</div>'
        f'<div class="login-subtitle">{subtitle}</div></div>',
        unsafe_allow_html=True,
    )


def render_hr_registration():
    _inject_login_page_styles()
    _login_card_header("HR Registration", "Create your HR account")
    with st.form("hr_register_form"):
        name = st.text_input("Full name", placeholder="Your name", label_visibility="visible")
        email = st.text_input("Email", placeholder="name@company.com", label_visibility="visible")
        contact = st.text_input("Contact (optional)", placeholder="Phone", label_visibility="visible")
        password = st.text_input("Password", type="password", placeholder="Password", label_visibility="visible")
        submitted = st.form_submit_button("Create account")
        if submitted:
            if not (name and name.strip()):
                st.error("Please enter your name.")
                return
            if not (email and email.strip()):
                st.error("Please enter your email.")
                return
            if not (password and password.strip()):
                st.error("Please enter a password.")
                return
            email = email.strip()
            existing = get_hr_by_email(email)
            if existing:
                st.error("This email is already registered as HR.")
                return
            hashed = hash_password(password)
            create_hr(name.strip(), email, (contact or "").strip(), hashed)
            st.success("Account created. You can now sign in.")
            st.balloons()
            st.rerun()
    st.markdown(
        '<p class="login-footer">First-time setup — create your HR account to get started</p>',
        unsafe_allow_html=True,
    )


def render_login():
    _inject_login_page_styles()
    _login_card_header("Streamlit HRMS", "Sign in to your account")
    with st.form("login_form"):
        email = st.text_input("Email", placeholder="Your email", label_visibility="visible")
        password = st.text_input("Password", type="password", placeholder="Password", label_visibility="visible")
        submitted = st.form_submit_button("Sign in")
        if submitted:
            if not (email and email.strip()):
                st.error("Please enter your email.")
                return
            if not (password and password.strip()):
                st.error("Please enter your password.")
                return
            email = email.strip()
            hr = get_hr_by_email(email)
            if hr and verify_password(password, hr.password):
                set_session(hr.id, "hr", hr.email, hr.name)
                st.success(f"Welcome back, {hr.name}!")
                st.rerun()
                return
            emp = get_employee_by_email(email)
            if emp and verify_password(password, emp.password):
                set_session(emp.id, "employee", emp.email, emp.name)
                log_login(emp.id)
                st.success(f"Welcome back, {emp.name}!")
                st.rerun()
                return
            st.error("Invalid email or password.")
    st.markdown(
        '<p class="login-footer">Secure sign in — Streamlit HRMS</p>',
        unsafe_allow_html=True,
    )


def main():
    if is_logged_in():
        st.info("You are already logged in. Use the sidebar to navigate.")
        return
    hr_count = get_hr_count()
    if hr_count == 0:
        render_hr_registration()
    else:
        render_login()
