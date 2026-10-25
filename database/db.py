"""
Database configuration and session management for Streamlit HRMS.
Uses SQLAlchemy ORM with SQLite.
"""
import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.pool import StaticPool

# Database path - relative to project root
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "hrms.db")
DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
    echo=False,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
ScopedSession = scoped_session(SessionLocal)


def get_db():
    """Get a new database session. Caller should close after use."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Create all tables. Call after importing all models."""
    from database.db_models import Base, HR, Department, Role, Employee, Attendance, Leave, Notification, UserSession
    Base.metadata.create_all(bind=engine)
    # Migration: add receiver_type to notification if missing (so HR vs employee see only their notifications)
    with engine.connect() as conn:
        try:
            conn.execute(text(
                "ALTER TABLE notification ADD COLUMN receiver_type VARCHAR(20) NOT NULL DEFAULT 'employee'"
            ))
            conn.commit()
        except Exception:
            pass  # column already exists
        try:
            conn.execute(text(
                "UPDATE notification SET receiver_type = 'hr' WHERE sender_type = 'employee'"
            ))
            conn.commit()
        except Exception:
            pass


def get_session():
    """Return a session for use in Streamlit (single-threaded)."""
    return SessionLocal()
