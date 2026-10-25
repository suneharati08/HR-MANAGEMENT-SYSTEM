"""User session (login/logout) tracking for worked hours."""
from datetime import datetime, date, timedelta, time
from database.db import get_session
from database.db_models import UserSession, Employee


def log_login(employee_id: int) -> UserSession:
    """Record login time for an employee. Call when employee signs in."""
    session = get_session()
    try:
        rec = UserSession(employee_id=employee_id, login_at=datetime.now())
        session.add(rec)
        session.commit()
        session.refresh(rec)
        return rec
    finally:
        session.close()


def log_logout(employee_id: int) -> bool:
    """Set logout time and duration for the latest open session. Call when employee logs out."""
    session = get_session()
    try:
        open_session = (
            session.query(UserSession)
            .filter(
                UserSession.employee_id == employee_id,
                UserSession.logout_at.is_(None),
            )
            .order_by(UserSession.login_at.desc())
            .first()
        )
        if not open_session:
            return False
        logout_at = datetime.now()
        open_session.logout_at = logout_at
        delta = logout_at - open_session.login_at
        open_session.duration_minutes = delta.total_seconds() / 60.0
        session.commit()
        return True
    finally:
        session.close()


def get_sessions_for_employee(employee_id: int, from_date: date = None, to_date: date = None):
    """Get all sessions (with logout) for an employee, optionally filtered by date range (by login_at date)."""
    session = get_session()
    try:
        q = session.query(UserSession).filter(UserSession.employee_id == employee_id)
        if from_date:
            # Start of from_date (00:00:00)
            start_datetime = datetime.combine(from_date, time.min)
            q = q.filter(UserSession.login_at >= start_datetime)
        if to_date:
            # End of to_date (23:59:59.999999)
            end_datetime = datetime.combine(to_date, time.max)
            q = q.filter(UserSession.login_at <= end_datetime)
        return q.order_by(UserSession.login_at.desc()).all()
    finally:
        session.close()


def get_all_employees_sessions(from_date: date = None, to_date: date = None):
    """Get all employees' sessions (for HR). Returns list of UserSession with employee joined."""
    session = get_session()
    try:
        q = session.query(UserSession).join(Employee)
        if from_date:
            # Start of from_date (00:00:00)
            start_datetime = datetime.combine(from_date, time.min)
            q = q.filter(UserSession.login_at >= start_datetime)
        if to_date:
            # End of to_date (23:59:59.999999)
            end_datetime = datetime.combine(to_date, time.max)
            q = q.filter(UserSession.login_at <= end_datetime)
        return q.order_by(UserSession.login_at.desc()).all()
    finally:
        session.close()


def get_daily_totals_for_employee(employee_id: int, from_date: date = None, to_date: date = None):
    """
    For each day, sum duration_minutes for that employee.
    Returns list of dicts: { date, total_minutes, total_hours, sessions_count }.
    """
    sessions = get_sessions_for_employee(employee_id, from_date=from_date, to_date=to_date)
    by_date = {}
    for s in sessions:
        if s.logout_at is None or s.duration_minutes is None:
            continue
        d = s.login_at.date() if hasattr(s.login_at, "date") else date(s.login_at.year, s.login_at.month, s.login_at.day)
        if d not in by_date:
            by_date[d] = {"total_minutes": 0.0, "sessions": []}
        by_date[d]["total_minutes"] += s.duration_minutes
        by_date[d]["sessions"].append(s)
    result = []
    for d, v in sorted(by_date.items(), reverse=True):
        result.append({
            "date": d,
            "total_minutes": v["total_minutes"],
            "total_hours": round(v["total_minutes"] / 60.0, 2),
            "sessions_count": len(v["sessions"]),
            "sessions": v["sessions"],
        })
    return result
