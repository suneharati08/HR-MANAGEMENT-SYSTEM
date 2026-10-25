"""Attendance model operations."""
from datetime import date
from database.db import get_session
from database.db_models import Attendance, Employee


def add_attendance(employee_id: int, dt: date, status: str, present_status: str, working_hours: float):
    session = get_session()
    try:
        att = Attendance(
            employee_id=employee_id,
            date=dt,
            status=status,
            present_status=present_status,
            working_hours=working_hours or 0.0,
        )
        session.add(att)
        session.commit()
        session.refresh(att)
        return att
    finally:
        session.close()


def get_attendance_by_employee_and_date(employee_id: int, dt: date):
    session = get_session()
    try:
        return (
            session.query(Attendance)
            .filter(Attendance.employee_id == employee_id, Attendance.date == dt)
            .first()
        )
    finally:
        session.close()


def get_attendance_for_employee(employee_id: int, from_date=None, to_date=None):
    session = get_session()
    try:
        q = session.query(Attendance).filter(Attendance.employee_id == employee_id)
        if from_date:
            q = q.filter(Attendance.date >= from_date)
        if to_date:
            q = q.filter(Attendance.date <= to_date)
        return q.order_by(Attendance.date.desc()).all()
    finally:
        session.close()


def get_attendance_on_date(dt: date):
    session = get_session()
    try:
        return (
            session.query(Attendance)
            .filter(Attendance.date == dt)
            .all()
        )
    finally:
        session.close()


def get_all_attendance(from_date=None, to_date=None):
    session = get_session()
    try:
        q = session.query(Attendance).join(Employee)
        if from_date:
            q = q.filter(Attendance.date >= from_date)
        if to_date:
            q = q.filter(Attendance.date <= to_date)
        return q.order_by(Attendance.date.desc()).all()
    finally:
        session.close()


def count_present_today(dt: date):
    session = get_session()
    try:
        return (
            session.query(Attendance)
            .filter(Attendance.date == dt, Attendance.present_status == "Present")
            .count()
        )
    finally:
        session.close()


def count_absent_today(dt: date):
    session = get_session()
    try:
        return (
            session.query(Attendance)
            .filter(Attendance.date == dt, Attendance.present_status == "Absent")
            .count()
        )
    finally:
        session.close()
