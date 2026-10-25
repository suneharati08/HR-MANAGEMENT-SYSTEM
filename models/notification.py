"""Notification model operations."""
from database.db import get_session
from database.db_models import Notification


def create_notification(sender_id: int, receiver_id: int, sender_type: str, message: str, ref_leave_id: int = None, receiver_type: str = None):
    """receiver_type: 'hr' or 'employee' - who should see this. If None, inferred from sender_type (opposite)."""
    if receiver_type is None:
        receiver_type = "employee" if sender_type == "hr" else "hr"
    session = get_session()
    try:
        n = Notification(
            sender_id=sender_id,
            receiver_id=receiver_id,
            receiver_type=receiver_type,
            sender_type=sender_type,
            message=message,
            status="Unread",
            ref_leave_id=ref_leave_id,
        )
        session.add(n)
        session.commit()
        session.refresh(n)
        return n
    finally:
        session.close()


def get_notifications_for_user(receiver_id: int, role: str, limit=50):
    """Only return notifications for this user: same receiver_id AND receiver_type matches role (hr/employee)."""
    session = get_session()
    try:
        return (
            session.query(Notification)
            .filter(
                Notification.receiver_id == receiver_id,
                Notification.receiver_type == role,
            )
            .order_by(Notification.created_at.desc())
            .limit(limit)
            .all()
        )
    finally:
        session.close()


def get_unread_count(receiver_id: int, role: str = None):
    """Unread count for this user. Pass role so we only count notifications meant for hr or employee."""
    session = get_session()
    try:
        q = session.query(Notification).filter(Notification.receiver_id == receiver_id, Notification.status == "Unread")
        if role:
            q = q.filter(Notification.receiver_type == role)
        return q.count()
    finally:
        session.close()


def mark_as_read(notification_id: int):
    session = get_session()
    try:
        n = session.query(Notification).filter(Notification.id == notification_id).first()
        if n:
            n.status = "Read"
            session.commit()
        return n
    finally:
        session.close()


def mark_all_as_read(receiver_id: int, role: str = None):
    session = get_session()
    try:
        q = session.query(Notification).filter(
            Notification.receiver_id == receiver_id,
            Notification.status == "Unread",
        )
        if role:
            q = q.filter(Notification.receiver_type == role)
        q.update({"status": "Read"})
        session.commit()
    finally:
        session.close()
