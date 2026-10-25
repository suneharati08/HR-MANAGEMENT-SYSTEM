"""Leave model operations."""
from datetime import date, datetime
from database.db import get_session
from database.db_models import Leave, Employee, Department


def create_leave(employee_id: int, department_id: int, from_date: date, to_date: date, total_days: int, reason: str):
    session = get_session()
    try:
        leave = Leave(
            employee_id=employee_id,
            department_id=department_id,
            from_date=from_date,
            to_date=to_date,
            total_days=total_days,
            reason=reason or "",
            status="Pending",
        )
        session.add(leave)
        session.commit()
        session.refresh(leave)
        return leave
    finally:
        session.close()


def get_all_leaves():
    session = get_session()
    try:
        return (
            session.query(Leave)
            .outerjoin(Employee, Leave.employee_id == Employee.id)
            .outerjoin(Department, Leave.department_id == Department.id)
            .order_by(Leave.from_date.desc())
            .all()
        )
    finally:
        session.close()


def get_leaves_for_employee(employee_id: int):
    session = get_session()
    try:
        return (
            session.query(Leave)
            .filter(Leave.employee_id == employee_id)
            .order_by(Leave.from_date.desc())
            .all()
        )
    finally:
        session.close()


def get_leave_by_id(leave_id: int):
    session = get_session()
    try:
        return session.query(Leave).filter(Leave.id == leave_id).first()
    finally:
        session.close()


def update_leave_status(leave_id: int, status: str, hr_comment: str = None):
    session = get_session()
    try:
        leave = session.query(Leave).filter(Leave.id == leave_id).first()
        if not leave:
            return None
        leave.status = status
        if hr_comment is not None:
            leave.hr_comment = hr_comment
        session.commit()
        session.refresh(leave)
        return leave
    finally:
        session.close()


def count_pending_leaves():
    session = get_session()
    try:
        return session.query(Leave).filter(Leave.status == "Pending").count()
    finally:
        session.close()


def _normalize_status(s):
    """Normalize status for comparison (case-insensitive, strip)."""
    return (s or "").strip().lower()


def _month_year_from_date(d):
    """Get (month, year) from from_date; works with date object or SQLite string."""
    if d is None:
        return None, None
    if hasattr(d, "month") and hasattr(d, "year"):
        return d.month, d.year
    if isinstance(d, str):
        try:
            # "YYYY-MM-DD" or "YYYY-MM-DD HH:MM:SS"
            s = d.strip()[:10]
            if len(s) == 10 and s[4] == "-" and s[7] == "-":
                return int(s[5:7]), int(s[0:4])
        except (ValueError, TypeError):
            pass
    return None, None


def get_leave_stats_for_employee(employee_id: int, month: int = None, year: int = None):
    """Return leave stats for an employee. If month/year given, filter by from_date in that month.
    total_days = sum of days for approved leaves only (in period). pending/approved/rejected = count of requests."""
    session = get_session()
    try:
        q = session.query(Leave).filter(Leave.employee_id == employee_id)
        leaves = q.all()
        # Filter by month/year; support both date objects and SQLite date strings
        if month is not None and year is not None:
            m, y = int(month), int(year)
            leaves = [l for l in leaves if _month_year_from_date(l.from_date) == (m, y)]
        # Only count approved days as "leave taken"
        total = sum(l.total_days for l in leaves if _normalize_status(l.status) == "approved")
        pending = sum(1 for l in leaves if _normalize_status(l.status) == "pending")
        approved = sum(1 for l in leaves if _normalize_status(l.status) == "approved")
        rejected = sum(1 for l in leaves if _normalize_status(l.status) == "rejected")
        return {"total_days": total, "pending": pending, "approved": approved, "rejected": rejected}
    finally:
        session.close()
