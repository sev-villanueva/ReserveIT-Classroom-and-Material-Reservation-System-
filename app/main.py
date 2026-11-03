"""Dashboard, room catalog, and material catalog."""
from flask import Blueprint, abort, flash, redirect, render_template, request, session, url_for
from psycopg2 import errors

from .auth import login_required, staff_required
from .db import fetch_all, fetch_one, tx
from .util import parse_date, parse_time, to_int

bp = Blueprint("main", __name__)

ROOM_TYPES = ["CLASSROOM", "LABORATORY", "CONFERENCE"]
MATERIAL_CATEGORIES = ["AV_EQUIPMENT", "FURNITURE", "SUPPLIES"]


@bp.route("/")
@login_required
def dashboard():
    acc = session["account"]
    if acc["type"] == "user":
        upcoming = fetch_all(
            """SELECT r.reservation_id, r.reservation_date, r.start_time, r.end_time, r.status,
                      rm.room_name, rm.building
               FROM reservation r JOIN room rm ON rm.room_id = r.room_id
               WHERE r.user_id = %s AND r.reservation_date >= CURRENT_DATE
                 AND r.status IN ('PENDING', 'APPROVED')
               ORDER BY r.reservation_date, r.start_time""",
            (acc["id"],),
        )
        owed = fetch_one(
            """SELECT COALESCE(SUM(p.amount), 0) AS total
               FROM penalty p JOIN reservation r ON r.reservation_id = p.reservation_id
               WHERE r.user_id = %s AND p.paid_status = 'UNPAID'""",
            (acc["id"],),
        )["total"]
        return render_template("dashboard_user.html", upcoming=upcoming, owed=owed)

    counts = {row["status"]: row["n"] for row in fetch_all(
        "SELECT status, COUNT(*) AS n FROM reservation GROUP BY status")}
    pending = fetch_all(
        """SELECT r.reservation_id, r.reservation_date, r.start_time, r.end_time, r.purpose,
                  rm.room_name, u.first_name || ' ' || u.last_name AS requester
           FROM reservation r
           JOIN room rm ON rm.room_id = r.room_id
           JOIN app_user u ON u.user_id = r.user_id
           WHERE r.status = 'PENDING' ORDER BY r.reservation_date, r.start_time LIMIT 10""")
    upcoming = fetch_all(
        """SELECT r.reservation_id, r.reservation_date, r.start_time, r.end_time,
                  rm.room_name, u.first_name || ' ' || u.last_name AS requester
           FROM reservation r
           JOIN room rm ON rm.room_id = r.room_id
           JOIN app_user u ON u.user_id = r.user_id
           WHERE r.status = 'APPROVED' AND r.reservation_date >= CURRENT_DATE
           ORDER BY r.reservation_date, r.start_time LIMIT 10""")
    top_rooms = fetch_all(
        """SELECT rm.room_name, rm.building, COUNT(*) AS n
           FROM reservation r JOIN room rm ON rm.room_id = r.room_id
           WHERE r.status IN ('APPROVED', 'COMPLETED')
           GROUP BY rm.room_id ORDER BY n DESC, rm.room_name LIMIT 5""")
    top_materials = fetch_all(
        """SELECT m.material_name, SUM(x.quantity_requested)::int AS n
           FROM reservation_material x
           JOIN material m ON m.material_id = x.material_id
           JOIN reservation r ON r.reservation_id = x.reservation_id
           WHERE r.status IN ('APPROVED', 'COMPLETED')
           GROUP BY m.material_id ORDER BY n DESC, m.material_name LIMIT 5""")
    unpaid = fetch_one(
        """SELECT COALESCE(SUM(amount), 0) AS total, COUNT(*) AS n
           FROM penalty WHERE paid_status = 'UNPAID'""")
    return render_template("dashboard_staff.html", counts=counts, pending=pending, upcoming=upcoming,
                           top_rooms=top_rooms, top_materials=top_materials, unpaid=unpaid)


# ---------------------------------------------------------------- rooms
@bp.route("/rooms")
@login_required
def rooms():
    day = parse_date(request.args.get("date"))
    start = parse_time(request.args.get("start"))
    end = parse_time(request.args.get("end"))
    check = bool(day and start and end and end > start)
    if (request.args.get("date") or request.args.get("start") or request.args.get("end")) and not check:
        flash("To check availability, enter a date, a start time, and an end time that is later than the start.", "error")

    if check:
        rows = fetch_all(
            """SELECT rm.*,
                      (rm.status = 'AVAILABLE' AND NOT EXISTS (
                          SELECT 1 FROM reservation r
                          WHERE r.room_id = rm.room_id AND r.status = 'APPROVED'
                            AND r.reservation_date = %s AND r.start_time < %s AND r.end_time > %s)
                      ) AS is_free
               FROM room rm ORDER BY rm.building, rm.room_name""",
            (day, end, start),
        )
    else:
        rows = fetch_all("SELECT rm.*, NULL::boolean AS is_free FROM room rm ORDER BY rm.building, rm.room_name")
    return render_template("rooms.html", rooms=rows, check=check, date=request.args.get("date", ""),
                           start=request.args.get("start", ""), end=request.args.get("end", ""))


def _room_from_form(f):
    name, building = f.get("room_name", "").strip(), f.get("building", "").strip()
    capacity, rtype = to_int(f.get("capacity")), f.get("room_type")
    problems = []
    if not name or len(name) > 50:
        problems.append("Enter a room name of up to 50 characters.")
    if not building or len(building) > 50:
        problems.append("Enter a building name of up to 50 characters.")
    if capacity is None or capacity <= 0:
        problems.append("Capacity must be a whole number greater than 0.")
    if rtype not in ROOM_TYPES:
        problems.append("Choose a room type.")
    return (name, building, capacity, rtype), problems


@bp.route("/rooms/new", methods=["GET", "POST"])
@staff_required
def room_new():
    if request.method == "POST":
        values, problems = _room_from_form(request.form)
        if not problems:
            try:
                with tx() as cur:
                    cur.execute("INSERT INTO room (room_name, building, capacity, room_type) VALUES (%s, %s, %s, %s)", values)
                flash("Room added.", "ok")
                return redirect(url_for("main.rooms"))
            except errors.UniqueViolation:
                problems.append("That building already has a room with this name.")
        for p in problems:
            flash(p, "error")
    return render_template("room_form.html", room=request.form, types=ROOM_TYPES, editing=False)


@bp.route("/rooms/<int:room_id>/edit", methods=["GET", "POST"])
@staff_required
def room_edit(room_id):
    room = fetch_one("SELECT * FROM room WHERE room_id = %s", (room_id,))
    if not room:
        abort(404)
    if request.method == "POST":
        values, problems = _room_from_form(request.form)
        if not problems:
            try:
                with tx() as cur:
                    cur.execute("""UPDATE room SET room_name=%s, building=%s, capacity=%s, room_type=%s
                                   WHERE room_id=%s""", values + (room_id,))
                flash("Room updated.", "ok")
                return redirect(url_for("main.rooms"))
            except errors.UniqueViolation:
                problems.append("That building already has a room with this name.")
        for p in problems:
            flash(p, "error")
        room = request.form
    return render_template("room_form.html", room=room, types=ROOM_TYPES, editing=True, room_id=room_id)


@bp.post("/rooms/<int:room_id>/status")
@staff_required
def room_status(room_id):
    with tx() as cur:
        cur.execute(
            """UPDATE room SET status = CASE WHEN status = 'AVAILABLE' THEN 'UNDER_MAINTENANCE' ELSE 'AVAILABLE' END
               WHERE room_id = %s RETURNING status""", (room_id,))
        row = cur.fetchone()
    if not row:
        abort(404)
    flash("Room is now under maintenance and cannot be reserved." if row["status"] == "UNDER_MAINTENANCE"
          else "Room is available for reservations again.", "ok")
    return redirect(url_for("main.rooms"))


@bp.post("/rooms/<int:room_id>/delete")
@staff_required
def room_delete(room_id):
    try:
        with tx() as cur:
            cur.execute("DELETE FROM room WHERE room_id = %s", (room_id,))
        flash("Room deleted.", "ok")
    except errors.ForeignKeyViolation:
        flash("This room has reservation history and cannot be deleted. Mark it as under maintenance to retire it.", "error")
    return redirect(url_for("main.rooms"))


# ------------------------------------------------------------ materials
@bp.route("/materials")
@login_required
def materials():
    rows = fetch_all("SELECT * FROM material ORDER BY category, material_name")
    return render_template("materials.html", materials=rows)


def _material_from_form(f):
    name, category = f.get("material_name", "").strip(), f.get("category")
    total = to_int(f.get("total_quantity"))
    problems = []
    if not name or len(name) > 100:
        problems.append("Enter a material name of up to 100 characters.")
    if category not in MATERIAL_CATEGORIES:
        problems.append("Choose a category.")
    if total is None or total < 0:
        problems.append("Total quantity must be a whole number, 0 or more.")
    return (name, category, total), problems


@bp.route("/materials/new", methods=["GET", "POST"])
@staff_required
def material_new():
    if request.method == "POST":
        values, problems = _material_from_form(request.form)
        if not problems:
            try:
                with tx() as cur:
                    cur.execute("""INSERT INTO material (material_name, category, total_quantity, available_quantity)
                                   VALUES (%s, %s, %s, %s)""", values + (values[2],))
                flash("Material added.", "ok")
                return redirect(url_for("main.materials"))
            except errors.UniqueViolation:
                problems.append("A material with that name already exists.")
        for p in problems:
            flash(p, "error")
    return render_template("material_form.html", material=request.form, categories=MATERIAL_CATEGORIES, editing=False)


@bp.route("/materials/<int:material_id>/edit", methods=["GET", "POST"])
@staff_required
def material_edit(material_id):
    material = fetch_one("SELECT * FROM material WHERE material_id = %s", (material_id,))
    if not material:
        abort(404)
    if request.method == "POST":
        values, problems = _material_from_form(request.form)
        if not problems:
            name, category, new_total = values
            # Changing the total shifts the available count by the same amount, so reserved units stay reserved.
            new_available = material["available_quantity"] + (new_total - material["total_quantity"])
            if new_available < 0:
                problems.append(f"{material['total_quantity'] - material['available_quantity']} units are currently "
                                "reserved, so the total cannot go below that.")
            else:
                try:
                    with tx() as cur:
                        cur.execute("""UPDATE material SET material_name=%s, category=%s, total_quantity=%s,
                                       available_quantity=%s WHERE material_id=%s""",
                                    (name, category, new_total, new_available, material_id))
                    flash("Material updated.", "ok")
                    return redirect(url_for("main.materials"))
                except errors.UniqueViolation:
                    problems.append("A material with that name already exists.")
        for p in problems:
            flash(p, "error")
        material = request.form
    return render_template("material_form.html", material=material, categories=MATERIAL_CATEGORIES,
                           editing=True, material_id=material_id)


@bp.post("/materials/<int:material_id>/delete")
@staff_required
def material_delete(material_id):
    try:
        with tx() as cur:
            cur.execute("DELETE FROM material WHERE material_id = %s", (material_id,))
        flash("Material deleted.", "ok")
    except errors.ForeignKeyViolation:
        flash("This material appears in past reservations and cannot be deleted. Set its total quantity to 0 to retire it.", "error")
    return redirect(url_for("main.materials"))
