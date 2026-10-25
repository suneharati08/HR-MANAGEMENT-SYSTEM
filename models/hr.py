"""HR model operations."""
from database.db import get_session
from database.db_models import HR


def get_hr_by_email(email: str):
    session = get_session()
    try:
        return session.query(HR).filter(HR.email == email).first()
    finally:
        session.close()


def get_hr_count():
    session = get_session()
    try:
        return session.query(HR).count()
    finally:
        session.close()


def create_hr(name: str, email: str, contact: str, hashed_password: str):
    session = get_session()
    try:
        hr = HR(name=name, email=email, contact=contact, password=hashed_password)
        session.add(hr)
        session.commit()
        session.refresh(hr)
        return hr
    finally:
        session.close()
