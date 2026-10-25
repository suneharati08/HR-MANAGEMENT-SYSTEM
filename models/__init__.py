"""Models package - re-exports from database for convenience."""
from database.db_models import (
    Base,
    HR,
    Department,
    Role,
    Employee,
    Attendance,
    Leave,
    Notification,
)

__all__ = [
    "Base",
    "HR",
    "Department",
    "Role",
    "Employee",
    "Attendance",
    "Leave",
    "Notification",
]
