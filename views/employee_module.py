"""
Employee Management Module: Full access for HR and Employee (listing, add, edit, delete, Department Master, Role Master).
"""
import streamlit as st
import pandas as pd
from utils.auth import is_logged_in, get_current_user_id
from models.employee import (
    get_all_employees,
    get_employee_by_id,
    get_departments,
    get_roles,
    create_employee,
    update_employee,
    delete_employee,
    add_department,
    delete_department,
    add_role,
    delete_role,
)
from utils.auth import hash_password

try:
    from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, DataReturnMode
    HAS_AGGRID = True
except ImportError:
    HAS_AGGRID = False


def listing_page():
    # Page marker for CSS
    st.markdown('<div class="page-emp-listing"></div>', unsafe_allow_html=True)

    employees = get_all_employees()
    dept_map = {d.id: d.name for d in get_departments()}
    role_map = {r.id: r.name for r in get_roles()}
    total = len(employees)

    # Header: title + total count badge
    st.markdown(
        '<div class="emp-listing-header">'
        '<h2 class="emp-listing-title"><i class="fa fa-users"></i>Employee Listing</h2>'
        f'<span class="emp-listing-count"><i class="fa fa-users"></i> {total} Employee{"s" if total != 1 else ""}</span>'
        '</div>',
        unsafe_allow_html=True,
    )

    # Action toolbar: all roles can Add Employee, Department Master, Role Master
    st.markdown('<div class="emp-toolbar-wrap"></div>', unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("Add Employee", use_container_width=True):
            st.session_state["emp_module_page"] = "add"
            st.rerun()
    with col2:
        if st.button("Department Master", use_container_width=True):
            st.session_state["emp_module_page"] = "department"
            st.rerun()
    with col3:
        if st.button("Role Master", use_container_width=True):
            st.session_state["emp_module_page"] = "role"
            st.rerun()

    if not employees:
        st.markdown(
            '<div class="emp-empty-state">'
            '<i class="fa fa-users-slash"></i>'
            '<p>No employees yet</p>'
            '<span class="hint">Click "Add Employee" above to add your first employee.</span>'
            '</div>',
            unsafe_allow_html=True,
        )
        return

    # Section title
    st.markdown(
        f'<p class="emp-table-section"><i class="fa fa-list"></i>All Employees ({total})</p>',
        unsafe_allow_html=True,
    )

    data = []
    for e in employees:
        data.append({
            "ID": e.id,
            "Employee Name": e.name,
            "Department": dept_map.get(e.department_id) or "—",
            "Role": role_map.get(e.role_id) or "—",
            "Contact": e.contact or "—",
            "Email": e.email,
        })
    df = pd.DataFrame(data)

    if HAS_AGGRID:
        gb = GridOptionsBuilder.from_dataframe(df)
        gb.configure_column("ID", hide=True)
        gb.configure_column("Employee Name", width=180)
        gb.configure_column("Department", width=120)
        gb.configure_column("Role", width=100)
        gb.configure_column("Contact", width=120)
        gb.configure_column("Email", width=200)
        gb.configure_selection(selection_mode="single", use_checkbox=False)
        gb.configure_grid_options(domLayout="normal", rowHeight=40, headerHeight=44)
        grid_options = gb.build()
        grid_response = AgGrid(
            df,
            gridOptions=grid_options,
            update_mode=GridUpdateMode.SELECTION_CHANGED,
            data_return_mode=DataReturnMode.AS_INPUT,
            fit_columns_on_grid_load=False,
            theme="streamlit",
            height=max(280, min(520, 44 + len(df) * 42)),
        )
        selected = grid_response.get("selected_rows", [])
        if hasattr(selected, "to_dict"):
            selected = selected.to_dict("records") if not selected.empty else []
        if selected:
            first = selected[0]
            emp_id = first.get("ID") if isinstance(first, dict) else getattr(first, "ID", None)
            if emp_id is not None:
                st.markdown(
                    '<p style="font-size:0.85rem; color:#64748b; margin:0.6rem 0 0.35rem;">'
                    '<i class="fa fa-hand-pointer" style="color:#4CAF50; margin-right:6px;"></i>Selected row — Edit or Delete</p>',
                    unsafe_allow_html=True,
                )
                ac1, ac2, ac3 = st.columns([1, 1, 4])
                with ac1:
                    if st.button("Edit", key="edit_emp", type="primary"):
                        st.session_state["emp_edit_id"] = emp_id
                        st.session_state["emp_module_page"] = "edit"
                        st.rerun()
                with ac2:
                    if st.button("Delete", key="del_emp"):
                        delete_employee(emp_id)
                        st.success("Employee deleted.")
                        st.rerun()
    else:
        st.dataframe(df, use_container_width=True, hide_index=True)
        emp_id = st.number_input("Employee ID to edit/delete", min_value=1, value=1, step=1)
        c1, c2 = st.columns(2)
        with c1:
            if st.button("Edit"):
                st.session_state["emp_edit_id"] = emp_id
                st.session_state["emp_module_page"] = "edit"
                st.rerun()
        with c2:
            if st.button("Delete"):
                if delete_employee(emp_id):
                    st.success("Employee deleted.")
                else:
                    st.error("Employee not found.")
                st.rerun()


def add_employee_page():
    """Add Employee: allowed for both HR and Employee."""
    st.subheader("Add Employee")
    departments = get_departments()
    roles = get_roles()
    dept_options = ["Select Department"] + [d.name for d in departments]
    role_options = ["Select Role"] + [r.name for r in roles]
    dept_id_map = {d.name: d.id for d in departments}
    role_id_map = {r.name: r.id for r in roles}

    if "add_emp_rows" not in st.session_state:
        st.session_state["add_emp_rows"] = [
            {"name": "", "email": "", "contact": "", "department": "Select Department", "role": "Select Role", "password": ""}
        ]

    rows = st.session_state["add_emp_rows"]
    for i, row in enumerate(rows):
        with st.expander(f"Employee {i + 1}", expanded=True):
            c1, c2 = st.columns(2)
            with c1:
                name = st.text_input("Employee Name", value=row["name"], key=f"an{i}")
                email = st.text_input("Email", value=row["email"], key=f"ae{i}")
                contact = st.text_input("Contact", value=row["contact"], key=f"ac{i}")
            with c2:
                dept = st.selectbox("Department", dept_options, index=dept_options.index(row["department"]) if row["department"] in dept_options else 0, key=f"ad{i}")
                role = st.selectbox("Role", role_options, index=role_options.index(row["role"]) if row["role"] in role_options else 0, key=f"ar{i}")
                password = st.text_input("Password", type="password", value=row["password"], key=f"ap{i}")
            rows[i] = {"name": name, "email": email, "contact": contact, "department": dept, "role": role, "password": password}
            if st.button("Remove", key=f"rem{i}"):
                rows.pop(i)
                st.rerun()

    if st.button("Add another employee"):
        rows.append({"name": "", "email": "", "contact": "", "department": "Select Department", "role": "Select Role", "password": ""})
        st.rerun()

    if st.button("Save all"):
        errors = []
        saved = 0
        for i, r in enumerate(rows):
            if not (r.get("name") or r.get("email") or r.get("password")):
                continue  # skip empty rows
            if not r["name"] or not r["email"] or not r["password"]:
                errors.append(f"Row {i+1}: Name, Email and Password required.")
                continue
            dept_id = dept_id_map.get(r["department"]) if r["department"] != "Select Department" else None
            role_id = role_id_map.get(r["role"]) if r["role"] != "Select Role" else None
            try:
                create_employee(
                    r["name"], r["email"], r["contact"],
                    dept_id, role_id, hash_password(r["password"])
                )
                saved += 1
            except Exception as ex:
                errors.append(f"Row {i+1}: {ex}")
        if errors:
            for e in errors:
                st.error(e)
        if saved > 0 and not errors:
            st.success(f"{saved} employee(s) added successfully.")
            st.session_state["add_emp_rows"] = [{"name": "", "email": "", "contact": "", "department": "Select Department", "role": "Select Role", "password": ""}]
            st.session_state["emp_module_page"] = "list"
            st.rerun()
        elif saved > 0:
            st.success(f"{saved} employee(s) added. Please fix errors above for remaining rows.")

    if st.button("Back to list"):
        st.session_state["emp_module_page"] = "list"
        st.rerun()


def edit_employee_page():
    emp_id = st.session_state.get("emp_edit_id")
    if not emp_id:
        st.session_state["emp_module_page"] = "list"
        st.rerun()
        return
    emp = get_employee_by_id(emp_id)
    if not emp:
        st.error("Employee not found.")
        st.session_state["emp_module_page"] = "list"
        st.rerun()
        return
    st.subheader("Edit Employee")
    departments = get_departments()
    roles = get_roles()
    dept_options = [d.name for d in departments]
    role_options = [r.name for r in roles]
    dept_id_map = {d.name: d.id for d in departments}
    role_id_map = {r.name: r.id for r in roles}
    current_dept = next((d.name for d in departments if d.id == emp.department_id), None) or (dept_options[0] if dept_options else None)
    current_role = next((r.name for r in roles if r.id == emp.role_id), None) or (role_options[0] if role_options else None)

    with st.form("edit_emp_form"):
        name = st.text_input("Employee Name", value=emp.name)
        email = st.text_input("Email", value=emp.email)
        contact = st.text_input("Contact", value=emp.contact or "")
        dept = st.selectbox("Department", dept_options, index=dept_options.index(current_dept) if current_dept and current_dept in dept_options else 0)
        role = st.selectbox("Role", role_options, index=role_options.index(current_role) if current_role and current_role in role_options else 0)
        new_password = st.text_input("New password (leave blank to keep current)", type="password")
        submitted = st.form_submit_button("Update")
        if submitted:
            dept_id = dept_id_map.get(dept) if dept else None
            role_id = role_id_map.get(role) if role else None
            update_employee(emp_id, name, email, contact, dept_id, role_id, hash_password(new_password) if new_password else None)
            st.success("Employee updated.")
            del st.session_state["emp_edit_id"]
            st.session_state["emp_module_page"] = "list"
            st.rerun()
    if st.button("Cancel"):
        del st.session_state["emp_edit_id"]
        st.session_state["emp_module_page"] = "list"
        st.rerun()


def department_master():
    st.subheader("Department Master")
    with st.form("add_dept"):
        new_name = st.text_input("Department name")
        if st.form_submit_button("Add"):
            if new_name and new_name.strip():
                try:
                    add_department(new_name.strip())
                    st.success("Department added.")
                except Exception as e:
                    st.error(str(e))
            st.rerun()
    depts = get_departments()
    if not depts:
        st.info("No departments yet.")
        return
    for d in depts:
        c1, c2 = st.columns([3, 1])
        with c1:
            st.write(d.name)
        with c2:
            if st.button("Delete", key=f"deldept{d.id}"):
                delete_department(d.id)
                st.success("Deleted.")
                st.rerun()
    if st.button("Back to list"):
        st.session_state["emp_module_page"] = "list"
        st.rerun()


def role_master():
    st.subheader("Role Master")
    with st.form("add_role"):
        new_name = st.text_input("Role name")
        if st.form_submit_button("Add"):
            if new_name and new_name.strip():
                try:
                    add_role(new_name.strip())
                    st.success("Role added.")
                except Exception as e:
                    st.error(str(e))
            st.rerun()
    roles = get_roles()
    if not roles:
        st.info("No roles yet.")
        return
    for r in roles:
        c1, c2 = st.columns([3, 1])
        with c1:
            st.write(r.name)
        with c2:
            if st.button("Delete", key=f"delrole{r.id}"):
                delete_role(r.id)
                st.success("Deleted.")
                st.rerun()
    if st.button("Back to list"):
        st.session_state["emp_module_page"] = "list"
        st.rerun()


def main():
    if not is_logged_in():
        st.warning("Please login first.")
        return
    page = st.session_state.get("emp_module_page", "list")
    if page == "add":
        add_employee_page()
    elif page == "edit":
        edit_employee_page()
    elif page == "department":
        department_master()
    elif page == "role":
        role_master()
    else:
        listing_page()
