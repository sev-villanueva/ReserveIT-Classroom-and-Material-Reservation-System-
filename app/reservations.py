"""Reservation requests, staff approval workflow, and penalties."""
from flask import Blueprint, abort, current_app, flash, redirect, render_template, request, session, url_for
from psycopg2 import errors

from .auth import login_required, staff_required, user_required
from .db import fetch_all, fetch_one, tx
from .util import is_past, parse_date, parse_time, to_int

bp = Blueprint("reservations", __name__)

STATUSES = ["PENDING", "APPROVED", "REJECTED", "CANCELLED", "COMPLETED"]
PENALTY_REASONS = ["NO_SHOW", "DAMAGED_MATERIAL", "LATE_RETURN"]


class RuleError(Exception):
    """A business rule stopped the action; the message is shown to the person."""


def _get_reservation(rid):
    r = fetch_one(
        """SELECT r.*, rm.room_name, rm.building, u.first_name || ' ' || u.last_name AS requester,
                  u.email AS requester_email, s.full_name AS reviewer
           FROM reservation r
           JOIN room rm ON rm.room_id = r.room_id
           JOIN app_user u ON u.user_id = r.user_id
           LEFT JOIN staff s ON s.staff_id = r.staff_id
           WHERE r.reservation_id = %s""", (rid,))
    if not r:
        abort(404)
    acc = session["account"]
    if acc["type"] == "user" and r["user_id"] != acc["id"]:
        abort(403, "You can only view your own reservations.")
    return r


def _release_materials(cur, rid):
    """Return a reservation's units to the available count (cancel after approval, or completion)."""
    cur.execute(
        """UPDATE material m SET available_quantity = m.available_quantity + x.quantity_requested
           FROM reservation_material x
           WHERE x.material_id = m.material_id AND x.reservation_id = %s""", (rid,))


# ------------------------------------------------------------------ list
@bp.route("/reservations")
@login_required
def index():
    acc = session["account"]
    status = request.args.get("status", "")
    where, params = [], []
    if acc["type"] == "user":
        where.append("r.user_id = %s")
        params.append(acc["id"])
    if status in STATUSES:
        where.append("r.status = %s")
        params.append(status)
    sql = """SELECT r.reservation_id, r.reservation_date, r.start_time, r.end_time, r.purpose, r.status,
                    rm.room_name, rm.building, u.first_name || ' ' || u.last_name AS requester
             FROM reservation r
             JOIN room rm ON rm.room_id = r.room_id
             JOIN app_user u ON u.user_id = r.user_id"""
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += " ORDER BY r.reservation_date DESC, r.start_time DESC"
    return render_template("reservations.html", reservations=fetch_all(sql, params),
                           statuses=STATUSES, selected=status)


# ------------------------------------------------------------------- new
def _unpaid_total(user_id):
    return fetch_one(
        """SELECT COALESCE(SUM(p.amount), 0) AS total
           FROM penalty p JOIN reservation r ON r.reservation_id = p.reservation_id
           WHERE r.user_id = %s AND p.paid_status = 'UNPAID'""", (user_id,))["total"]


def _check_request(form, user_id, materials):
    """Return (clean values, list of problems) for a new reservation request."""
    problems = []
    me = fetch_one("SELECT status FROM app_user WHERE user_id = %s", (user_id,))
    if not me or me["status"] != "ACTIVE":
        problems.append("Your account is suspended, so you cannot submit new reservations. Contact the department office.")
    threshold = current_app.config["PENALTY_THRESHOLD"]
    owed = _unpaid_total(user_id)
    if owed > threshold:
        problems.append(f"You have ₱{owed:,.2f} in unpaid penalties, which is above the ₱{threshold:,.2f} limit. "
                        "Settle them with the staff office before reserving again.")

    room_id = to_int(form.get("room_id"))
    day, start, end = parse_date(form.get("reservation_date")), parse_time(form.get("start_time")), parse_time(form.get("end_time"))
    purpose = form.get("purpose", "").strip()
    room = fetch_one("SELECT status FROM room WHERE room_id = %s", (room_id,)) if room_id else None

    if not room:
        problems.append("Choose a room.")
    elif room["status"] != "AVAILABLE":
        problems.append("That room is under maintenance and cannot be reserved.")
    if not day or not start or not end:
        problems.append("Enter a date, a start time, and an end time.")
    elif end <= start:
        problems.append("The end time must be later than the start time.")
    elif is_past(day, start):
        problems.append("You cannot reserve a date and time that has already passed.")
    if not purpose or len(purpose) > 255:
        problems.append("Describe the purpose in up to 255 characters.")

    if room and day and start and end and end > start and room["status"] == "AVAILABLE":
        clash = fetch_one(
            """SELECT 1 FROM reservation WHERE room_id = %s AND status = 'APPROVED' AND reservation_date = %s
               AND start_time < %s AND end_time > %s""", (room_id, day, end, start))
        if clash:
            problems.append("That room already has an approved reservation overlapping this time. Pick another time or room.")

    items = []
    for m in materials:
        raw = form.get(f"qty_{m['material_id']}", "").strip()
        if raw in ("", "0"):
            continue
        qty = to_int(raw)
        if qty is None or qty < 0:
            problems.append(f"Enter a whole number for {m['material_name']}.")
        elif qty > m["available_quantity"]:
            problems.append(f"Only {m['available_quantity']} {m['material_name']} available, but you asked for {qty}.")
        else:
            items.append((m["material_id"], qty))
    return (room_id, day, start, end, purpose, items), problems


@bp.route("/reservations/new", methods=["GET", "POST"])
@user_required
def new():
    acc = session["account"]
    rooms = fetch_all("SELECT room_id, room_name, building, capacity FROM room WHERE status = 'AVAILABLE' ORDER BY building, room_name")
    materials = fetch_all("SELECT * FROM material WHERE available_quantity > 0 ORDER BY category, material_name")
    if request.method == "POST":
        values, problems = _check_request(request.form, acc["id"], materials)
        if not problems:
            room_id, day, start, end, purpose, items = values
            with tx() as cur:
                cur.execute(
                    """INSERT INTO reservation (user_id, room_id, reservation_date, start_time, end_time, purpose)
                       VALUES (%s, %s, %s, %s, %s, %s) RETURNING reservation_id""",
                    (acc["id"], room_id, day, start, end, purpose))
                rid = cur.fetchone()["reservation_id"]
                for material_id, qty in items:
                    cur.execute("INSERT INTO reservation_material (reservation_id, material_id, quantity_requested) VALUES (%s, %s, %s)",
                                (rid, material_id, qty))
            flash("Request submitted. Staff will review it, and you can follow its status here.", "ok")
            return redirect(url_for("reservations.detail", rid=rid))
        for p in problems:
            flash(p, "error")
    return render_template("reservation_form.html", rooms=rooms, materials=materials, form=request.form)


# ---------------------------------------------------------------- detail
@bp.route("/reservations/<int:rid>")
@login_required
def detail(rid):
    r = _get_reservation(rid)
    items = fetch_all(
        """SELECT m.material_name, x.quantity_requested FROM reservation_material x
           JOIN material m ON m.material_id = x.material_id WHERE x.reservation_id = %s ORDER BY m.material_name""", (rid,))
    penalty = fetch_one("SELECT * FROM penalty WHERE reservation_id = %s", (rid,))
    return render_template("reservation_detail.html", r=r, items=items, penalty=penalty, reasons=PENALTY_REASONS)


# ---------------------------------------------------------------- actions
@bp.post("/reservations/<int:rid>/approve")
@staff_required
def approve(rid):
    staff_id = session["account"]["id"]
    try:
        with tx() as cur:
            cur.execute("SELECT status FROM reservation WHERE reservation_id = %s FOR UPDATE", (rid,))
            r = cur.fetchone()
            if not r:
                abort(404)
            if r["status"] != "PENDING":
                raise RuleError("Only pending reservations can be approved.")
            cur.execute("SELECT status FROM staff WHERE staff_id = %s", (staff_id,))
            if cur.fetchone()["status"] != "ACTIVE":
                raise RuleError("Your staff account is inactive.")
            cur.execute(
                """SELECT x.material_id, x.quantity_requested, m.available_quantity, m.material_name
                   FROM reservation_material x JOIN material m ON m.material_id = x.material_id
                   WHERE x.reservation_id = %s ORDER BY x.material_id FOR UPDATE OF m""", (rid,))
            for it in cur.fetchall():
                if it["quantity_requested"] > it["available_quantity"]:
                    raise RuleError(f"Not enough {it['material_name']}: {it['available_quantity']} available, "
                                    f"{it['quantity_requested']} requested.")
                cur.execute("UPDATE material SET available_quantity = available_quantity - %s WHERE material_id = %s",
                            (it["quantity_requested"], it["material_id"]))
            cur.execute("UPDATE reservation SET status = 'APPROVED', staff_id = %s WHERE reservation_id = %s", (staff_id, rid))
        flash("Reservation approved.", "ok")
    except RuleError as e:
        flash(str(e), "error")
    except errors.ExclusionViolation:
        flash("Cannot approve: another approved reservation already uses this room at an overlapping time.", "error")
    return redirect(url_for("reservations.detail", rid=rid))


@bp.post("/reservations/<int:rid>/reject")
@staff_required
def reject(rid):
    with tx() as cur:
        cur.execute("""UPDATE reservation SET status = 'REJECTED', staff_id = %s
                       WHERE reservation_id = %s AND status = 'PENDING' RETURNING 1""", (session["account"]["id"], rid))
        done = cur.fetchone()
    flash("Reservation rejected." if done else "Only pending reservations can be rejected.", "ok" if done else "error")
    return redirect(url_for("reservations.detail", rid=rid))


@bp.post("/reservations/<int:rid>/cancel")
@login_required
def cancel(rid):
    r = _get_reservation(rid)  # also blocks users from touching other people's reservations
    if r["status"] not in ("PENDING", "APPROVED"):
        flash("Only pending or approved reservations can be cancelled.", "error")
        return redirect(url_for("reservations.detail", rid=rid))
    acc = session["account"]
    with tx() as cur:
        cur.execute("SELECT status FROM reservation WHERE reservation_id = %s FOR UPDATE", (rid,))
        was = cur.fetchone()["status"]
        if was == "APPROVED":
            _release_materials(cur, rid)
        # staff_id keeps its reviewer if there was one; a cancelled request may have none
        cur.execute("UPDATE reservation SET status = 'CANCELLED' WHERE reservation_id = %s", (rid,))
    flash("Reservation cancelled." + (" Reserved materials were returned to stock." if was == "APPROVED" else ""), "ok")
    return redirect(url_for("reservations.detail", rid=rid))


@bp.post("/reservations/<int:rid>/complete")
@staff_required
def complete(rid):
    with tx() as cur:
        cur.execute("SELECT status FROM reservation WHERE reservation_id = %s FOR UPDATE", (rid,))
        r = cur.fetchone()
        if not r:
            abort(404)
        if r["status"] != "APPROVED":
            flash("Only approved reservations can be marked completed.", "error")
            return redirect(url_for("reservations.detail", rid=rid))
        _release_materials(cur, rid)
        cur.execute("UPDATE reservation SET status = 'COMPLETED' WHERE reservation_id = %s", (rid,))
    flash("Marked as completed. Borrowed materials are back in stock.", "ok")
    return redirect(url_for("reservations.detail", rid=rid))


# -------------------------------------------------------------- penalties
@bp.post("/reservations/<int:rid>/penalty")
@staff_required
def issue_penalty(rid):
    r = _get_reservation(rid)
    reason = request.form.get("reason")
    try:
        amount = round(float(request.form.get("amount", "")), 2)
    except ValueError:
        amount = -1
    if r["status"] not in ("APPROVED", "COMPLETED"):
        flash("Penalties can only be issued for approved or completed reservations.", "error")
    elif reason not in PENALTY_REASONS or amount < 0 or amount > 99999999:
        flash("Choose a reason and enter an amount of 0 or more.", "error")
    else:
        try:
            with tx() as cur:
                cur.execute("INSERT INTO penalty (reservation_id, reason, amount) VALUES (%s, %s, %s)", (rid, reason, amount))
            flash("Penalty recorded.", "ok")
        except errors.UniqueViolation:
            flash("This reservation already has a penalty. Only one is allowed per reservation.", "error")
    return redirect(url_for("reservations.detail", rid=rid))


@bp.post("/penalties/<int:pid>/pay")
@staff_required
def mark_paid(pid):
    with tx() as cur:
        cur.execute("""UPDATE penalty SET paid_status = 'PAID', paid_date = CURRENT_DATE
                       WHERE penalty_id = %s AND paid_status = 'UNPAID' RETURNING reservation_id""", (pid,))
        row = cur.fetchone()
    flash("Penalty marked as paid." if row else "That penalty was already paid.", "ok" if row else "error")
    return redirect(request.form.get("back") if (request.form.get("back") or "").startswith("/") else url_for("reservations.penalties"))


@bp.route("/penalties")
@login_required
def penalties():
    acc = session["account"]
    sql = """SELECT p.*, r.reservation_date, rm.room_name, u.first_name || ' ' || u.last_name AS requester
             FROM penalty p
             JOIN reservation r ON r.reservation_id = p.reservation_id
             JOIN room rm ON rm.room_id = r.room_id
             JOIN app_user u ON u.user_id = r.user_id"""
    params = ()
    if acc["type"] == "user":
        sql += " WHERE r.user_id = %s"
        params = (acc["id"],)
    sql += " ORDER BY (p.paid_status = 'PAID'), p.issue_date DESC"
    return render_template("penalties.html", penalties=fetch_all(sql, params))
