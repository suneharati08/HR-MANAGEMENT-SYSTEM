"""Employee model operations."""
from database.db import get_session
from database.db_models import Employee, Department, Role


def get_all_employees():
    session = get_session()
    try:
        return (
            session.query(Employee)
            .outerjoin(Department, Employee.department_id == Department.id)
            .outerjoin(Role, Employee.role_id == Role.id)
            .all()
        )
    finally:
        session.close()


def get_employee_by_id(emp_id: int):
    session = get_session()
    try:
        return session.query(Employee).filter(Employee.id == emp_id).first()
    finally:
        session.close()


def get_employee_by_email(email: str):
    session = get_session()
    try:
        return session.query(Employee).filter(Employee.email == email).first()
    finally:
        session.close()


def create_employee(name, email, contact, department_id, role_id, hashed_password):
    session = get_session()
    try:
        emp = Employee(
            name=name,
            email=email,
            contact=contact or "",
            department_id=department_id or None,
            role_id=role_id or None,
            password=hashed_password,
        )
        session.add(emp)
        session.commit()
        session.refresh(emp)
        return emp
    finally:
        session.close()


def update_employee(emp_id, name, email, contact, department_id, role_id, password=None):
    session = get_session()
    try:
        emp = session.query(Employee).filter(Employee.id == emp_id).first()
        if not emp:
            return None
        emp.name = name
        emp.email = email
        emp.contact = contact or ""
        emp.department_id = department_id or None
        emp.role_id = role_id or None
        if password:
            emp.password = password
        session.commit()
        session.refresh(emp)
        return emp
    finally:
        session.close()


def delete_employee(emp_id: int):
    session = get_session()
    try:
        emp = session.query(Employee).filter(Employee.id == emp_id).first()
        if emp:
            session.delete(emp)
            session.commit()
            return True
        return False
    finally:
        session.close()


def get_departments():
    session = get_session()
    try:
        return session.query(Department).order_by(Department.name).all()
    finally:
        session.close()


def get_roles():
    session = get_session()
    try:
        return session.query(Role).order_by(Role.name).all()
    finally:
        session.close()


def add_department(name: str):
    session = get_session()
    try:
        dept = Department(name=name.strip())
        session.add(dept)
        session.commit()
        session.refresh(dept)
        return dept
    finally:
        session.close()


def delete_department(dept_id: int):
    session = get_session()
    try:
        dept = session.query(Department).filter(Department.id == dept_id).first()
        if dept:
            session.delete(dept)
            session.commit()
            return True
        return False
    finally:
        session.close()


def add_role(name: str):
    session = get_session()
    try:
        role = Role(name=name.strip())
        session.add(role)
        session.commit()
        session.refresh(role)
        return role
    finally:
        session.close()


def delete_role(role_id: int):
    session = get_session()
    try:
        role = session.query(Role).filter(Role.id == role_id).first()
        if role:
            session.delete(role)
            session.commit()
            return True
        return False
    finally:
        session.close()


def get_employees_for_dropdown():
    session = get_session()
    try:
        return session.query(Employee).order_by(Employee.name).all()
    finally:
        session.close()
