"""Administrator tools: departments, staff accounts, and requester accounts."""
from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from psycopg2 import errors
from werkzeug.security import generate_password_hash

from .auth import admin_required
from .db import fetch_all, tx

bp = Blueprint("admin", __name__, url_prefix="/admin")


@bp.route("/")
@admin_required
def index():
    return render_template(
        "admin.html",
        departments=fetch_all("""SELECT d.*, COUNT(u.user_id) AS members FROM department d
                                 LEFT JOIN app_user u ON u.department_id = d.department_id
                                 GROUP BY d.department_id ORDER BY d.department_name"""),
        staff=fetch_all("SELECT staff_id, full_name, email, role, status FROM staff ORDER BY full_name"),
        users=fetch_all("""SELECT u.user_id, u.first_name, u.last_name, u.email, u.role, u.status, d.department_name
                           FROM app_user u JOIN department d ON d.department_id = u.department_id
                           ORDER BY u.last_name, u.first_name"""),
    )


@bp.post("/departments")
@admin_required
def add_department():
    name = request.form.get("department_name", "").strip()
    if not name or len(name) > 100:
        flash("Enter a department name of up to 100 characters.", "error")
    else:
        try:
            with tx() as cur:
                cur.execute("INSERT INTO department (department_name) VALUES (%s)", (name,))
            flash("Department added.", "ok")
        except errors.UniqueViolation:
            flash("That department already exists.", "error")
    return redirect(url_for("admin.index"))


@bp.post("/staff")
@admin_required
def add_staff():
    f = request.form
    name, email, password, role = f.get("full_name", "").strip(), f.get("email", "").strip().lower(), f.get("password", ""), f.get("role")
    if not name or "@" not in email or len(password) < 8 or role not in ("STAFF", "ADMIN"):
        flash("Enter a name, a valid email, a role, and a password of at least 8 characters.", "error")
    else:
        try:
            with tx() as cur:
                cur.execute("INSERT INTO staff (full_name, email, password_hash, role) VALUES (%s, %s, %s, %s)",
                            (name, email, generate_password_hash(password, method="pbkdf2:sha256"), role))
            flash("Staff account created.", "ok")
        except errors.UniqueViolation:
            flash("A staff account with that email already exists.", "error")
    return redirect(url_for("admin.index"))


@bp.post("/staff/<int:staff_id>/status")
@admin_required
def toggle_staff(staff_id):
    if staff_id == session["account"]["id"]:
        flash("You cannot deactivate your own account.", "error")
    else:
        with tx() as cur:
            cur.execute("""UPDATE staff SET status = CASE WHEN status = 'ACTIVE' THEN 'INACTIVE' ELSE 'ACTIVE' END
                           WHERE staff_id = %s""", (staff_id,))
        flash("Staff status updated.", "ok")
    return redirect(url_for("admin.index"))


@bp.post("/users/<int:user_id>/status")
@admin_required
def toggle_user(user_id):
    with tx() as cur:
        cur.execute("""UPDATE app_user SET status = CASE WHEN status = 'ACTIVE' THEN 'SUSPENDED' ELSE 'ACTIVE' END
                       WHERE user_id = %s""", (user_id,))
    flash("Account status updated.", "ok")
    return redirect(url_for("admin.index"))
