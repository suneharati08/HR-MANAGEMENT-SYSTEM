"""
Central SQLAlchemy model definitions for Streamlit HRMS.
All table schemas in one place for clarity and to avoid circular imports.
"""
from datetime import datetime, date
from sqlalchemy import (
    Column, Integer, String, Float, Date, DateTime, ForeignKey, Text, Enum as SQLEnum
)
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class HR(Base):
    __tablename__ = "hr"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    email = Column(String(120), unique=True, nullable=False)
    contact = Column(String(20), nullable=True)
    password = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class Department(Base):
    __tablename__ = "department"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, unique=True)


class Role(Base):
    __tablename__ = "role"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, unique=True)


class Employee(Base):
    __tablename__ = "employee"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    email = Column(String(120), unique=True, nullable=False)
    department_id = Column(Integer, ForeignKey("department.id"), nullable=True)
    role_id = Column(Integer, ForeignKey("role.id"), nullable=True)
    contact = Column(String(20), nullable=True)
    password = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    department = relationship("Department", backref="employees")
    role = relationship("Role", backref="employees")


class Attendance(Base):
    __tablename__ = "attendance"
    id = Column(Integer, primary_key=True, autoincrement=True)
    employee_id = Column(Integer, ForeignKey("employee.id"), nullable=False)
    date = Column(Date, nullable=False)
    status = Column(String(20), nullable=False)  # Active, WFH, Inactive
    present_status = Column(String(20), nullable=False)  # Present, Absent
    working_hours = Column(Float, default=0.0)
    employee = relationship("Employee", backref="attendances")


class Leave(Base):
    __tablename__ = "leave"
    id = Column(Integer, primary_key=True, autoincrement=True)
    employee_id = Column(Integer, ForeignKey("employee.id"), nullable=False)
    department_id = Column(Integer, ForeignKey("department.id"), nullable=True)
    from_date = Column(Date, nullable=False)
    to_date = Column(Date, nullable=False)
    total_days = Column(Integer, nullable=False)
    reason = Column(Text, nullable=True)
    status = Column(String(20), nullable=False, default="Pending")  # Pending, Approved, Rejected
    hr_comment = Column(Text, nullable=True)
    employee = relationship("Employee", backref="leaves")
    department = relationship("Department", backref="leaves")


class Notification(Base):
    __tablename__ = "notification"
    id = Column(Integer, primary_key=True, autoincrement=True)
    sender_id = Column(Integer, nullable=True)  # employee_id or hr id
    receiver_id = Column(Integer, nullable=False)  # hr id or employee id
    receiver_type = Column(String(20), nullable=False)  # "hr" or "employee" - who should see this
    sender_type = Column(String(20), nullable=False)  # "hr" or "employee"
    message = Column(Text, nullable=False)
    status = Column(String(20), nullable=False, default="Unread")  # Unread, Read
    created_at = Column(DateTime, default=datetime.utcnow)
    ref_leave_id = Column(Integer, nullable=True)  # optional link to leave


class UserSession(Base):
    """Tracks employee login/logout for worked hours (app usage time)."""
    __tablename__ = "user_session"
    id = Column(Integer, primary_key=True, autoincrement=True)
    employee_id = Column(Integer, ForeignKey("employee.id"), nullable=False)
    login_at = Column(DateTime, nullable=False)
    logout_at = Column(DateTime, nullable=True)
    duration_minutes = Column(Float, nullable=True)  # (logout_at - login_at) in minutes
    employee = relationship("Employee", backref="user_sessions")
