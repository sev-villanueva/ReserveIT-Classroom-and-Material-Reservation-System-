from functools import wraps

from flask import Blueprint, abort, flash, redirect, render_template, request, session, url_for
from psycopg2 import errors
from werkzeug.security import check_password_hash, generate_password_hash

from .db import fetch_all, fetch_one, tx

bp = Blueprint("auth", __name__)


def role_required(check):
    """Build a decorator that only lets logged-in accounts passing `check` through."""

    def decorator(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            acc = session.get("account")
            if not acc:
                return redirect(url_for("auth.login", next=request.path))
            if not check(acc):
                abort(403, "Your account does not have access to this page.")
            return view(*args, **kwargs)

        return wrapped

    return decorator


login_required = role_required(lambda a: True)
user_required = role_required(lambda a: a["type"] == "user")
staff_required = role_required(lambda a: a["type"] == "staff")
admin_required = role_required(lambda a: a["type"] == "staff" and a["role"] == "ADMIN")


def _safe_next(target):
    return target if target and target.startswith("/") and not target.startswith("//") else None


@bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        staff = fetch_one(
            "SELECT staff_id, full_name, password_hash, role, status FROM staff WHERE email = %s",
            (email,),
        )
        if staff and check_password_hash(staff["password_hash"], password):
            if staff["status"] != "ACTIVE":
                flash("This staff account is inactive. Ask an administrator to reactivate it.", "error")
                return render_template("login.html")
            session.clear()
            session["account"] = {"type": "staff", "id": staff["staff_id"],
                                  "name": staff["full_name"], "role": staff["role"]}
            return redirect(_safe_next(request.args.get("next")) or url_for("main.dashboard"))

        user = fetch_one(
            "SELECT user_id, first_name, last_name, password_hash, role FROM app_user WHERE email = %s",
            (email,),
        )
        if user and check_password_hash(user["password_hash"], password):
            session.clear()
            session["account"] = {"type": "user", "id": user["user_id"],
                                  "name": f"{user['first_name']} {user['last_name']}", "role": user["role"]}
            return redirect(_safe_next(request.args.get("next")) or url_for("main.dashboard"))

        flash("Email or password is incorrect.", "error")
    return render_template("login.html")


@bp.post("/logout")
def logout():
    session.clear()
    return redirect(url_for("auth.login"))


@bp.route("/register", methods=["GET", "POST"])
def register():
    departments = fetch_all("SELECT department_id, department_name FROM department ORDER BY department_name")
    if request.method == "POST":
        f = request.form
        first, last = f.get("first_name", "").strip(), f.get("last_name", "").strip()
        email, password = f.get("email", "").strip().lower(), f.get("password", "")
        role, dept = f.get("role", ""), f.get("department_id", "")

        problems = []
        if not first or not last:
            problems.append("Enter your first and last name.")
        if "@" not in email or len(email) > 100:
            problems.append("Enter a valid email address.")
        if len(password) < 8:
            problems.append("Use a password with at least 8 characters.")
        if role not in ("STUDENT", "FACULTY"):
            problems.append("Choose whether you are a student or faculty member.")
        if not dept.isdigit():
            problems.append("Choose your department.")

        if not problems:
            try:
                with tx() as cur:
                    cur.execute(
                        """INSERT INTO app_user (first_name, last_name, email, password_hash, role, department_id)
                           VALUES (%s, %s, %s, %s, %s, %s)""",
                        (first, last, email, generate_password_hash(password, method="pbkdf2:sha256"),
                         role, int(dept)),
                    )
                flash("Account created. You can log in now.", "ok")
                return redirect(url_for("auth.login"))
            except errors.UniqueViolation:
                problems.append("An account with that email already exists.")
            except errors.ForeignKeyViolation:
                problems.append("That department does not exist.")
        for p in problems:
            flash(p, "error")
        return render_template("register.html", departments=departments, form=f)
    return render_template("register.html", departments=departments, form={})
