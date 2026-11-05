"""End-to-end check of ReserveIT's main workflow and business rules.

Run on a seeded database (python manage.py reset-db) with:  python tests/smoke_test.py
It adds a few rows each run, so use a development database only.
"""
import random
import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import create_app  # noqa: E402
from app.db import connect  # noqa: E402

app = create_app()
app.config["TESTING"] = True
PW = "ChangeMe123!"
passed = 0


def check(label, cond):
    global passed
    if not cond:
        print(f"FAIL: {label}")
        sys.exit(1)
    passed += 1
    print(f"  ok  {label}")


class Browser:
    def __init__(self):
        self.c = app.test_client()

    def token(self):
        self.c.get("/login")
        with self.c.session_transaction() as s:
            s.setdefault("_csrf", "t" * 32)
            return s["_csrf"]

    def get(self, url, **kw):
        return self.c.get(url, **kw)

    def post(self, url, data=None, **kw):
        data = dict(data or {})
        data["_csrf"] = self.token()
        return self.c.post(url, data=data, follow_redirects=True, **kw)

    def login(self, email):
        r = self.post("/login", {"email": email, "password": PW})
        return r


def one(sql, params=()):
    conn = connect()
    with conn.cursor() as cur:
        cur.execute(sql, params)
        row = cur.fetchone()
    conn.close()
    return row


def stock(name):
    return one("SELECT available_quantity AS n FROM material WHERE material_name = %s", (name,))["n"]


def latest_reservation(purpose):
    return one("SELECT reservation_id AS id, status FROM reservation WHERE purpose = %s ORDER BY 1 DESC", (purpose,))


tag = random.randint(1000, 9999)
day = (date.today() + timedelta(days=random.randint(200, 3000))).isoformat()
room_id = one("SELECT room_id AS id FROM room WHERE room_name = 'Room 102'")["id"]
projector = one("SELECT material_id AS id FROM material WHERE material_name = 'Projector'")["id"]


def request_room(b, purpose, start, end, qty=1, d=None):
    return b.post("/reservations/new", {
        "room_id": room_id, "reservation_date": d or day, "start_time": start, "end_time": end,
        "purpose": purpose, f"qty_{projector}": qty})


print("Login and access control")
anon = Browser()
check("anonymous visitor is sent to login", "Log in" in anon.get("/", follow_redirects=True).get_data(as_text=True))
bad = Browser(); r = bad.post("/login", {"email": "student@reserveit.test", "password": "wrong"})
check("wrong password shows an error", "Email or password is incorrect" in r.get_data(as_text=True))
check("POST without CSRF token is refused", app.test_client().post("/login", data={"email": "a", "password": "b"}).status_code == 400)

student, student2, staff, admin = Browser(), Browser(), Browser(), Browser()
for b, email in [(student, "student@reserveit.test"), (student2, "student2@reserveit.test"),
                 (staff, "staff@reserveit.test"), (admin, "admin@reserveit.test")]:
    check(f"{email} can log in", "Log out" in b.login(email).get_data(as_text=True))

for url in ["/", "/rooms", "/materials", "/reservations", "/reservations/new", "/penalties"]:
    check(f"student can open {url}", student.get(url).status_code == 200)
for url in ["/", "/rooms", "/materials", "/reservations", "/penalties", "/rooms/new", "/materials/new"]:
    check(f"staff can open {url}", staff.get(url).status_code == 200)
check("student blocked from /admin", student.get("/admin/").status_code == 403)
check("student blocked from adding rooms", student.get("/rooms/new").status_code == 403)
check("staff (non-admin) blocked from /admin", staff.get("/admin/").status_code == 403)
check("admin can open /admin", admin.get("/admin/").status_code == 200)
check("staff cannot submit a request (requesters only)", staff.get("/reservations/new").status_code == 403)

print("Registration")
email = f"new{tag}@reserveit.test"
reg = {"first_name": "Nina", "last_name": "Test", "email": email, "password": "longenough1", "role": "STUDENT",
       "department_id": one("SELECT department_id AS id FROM department ORDER BY 1")["id"]}
check("new user can register", "Account created" in Browser().post("/register", reg).get_data(as_text=True))
check("duplicate email is rejected", "already exists" in Browser().post("/register", reg).get_data(as_text=True))
check("short password is rejected", "at least 8" in Browser().post("/register", {**reg, "email": "x@y.z", "password": "abc"}).get_data(as_text=True))

print("Reservation rules")
past = (date.today() - timedelta(days=1)).isoformat()
check("past date is rejected", "already passed" in request_room(student, f"past{tag}", "09:00", "10:00", d=past).get_data(as_text=True))
check("end before start is rejected", "later than the start" in request_room(student, f"rev{tag}", "11:00", "10:00").get_data(as_text=True))
avail = stock("Projector")
check("more than available is rejected", "available" in request_room(student, f"big{tag}", "09:00", "10:00", qty=avail + 5).get_data(as_text=True))
check("nothing saved by failed requests", latest_reservation(f"big{tag}") is None)

r = request_room(student, f"A{tag}", "09:00", "11:00", qty=2)
check("valid request is accepted", "Request submitted" in r.get_data(as_text=True))
a = latest_reservation(f"A{tag}")["id"]
check("new request starts as PENDING", latest_reservation(f"A{tag}")["status"] == "PENDING")
check("pending request does not hold stock", stock("Projector") == avail)
request_room(student2, f"B{tag}", "10:00", "12:00", qty=1)
b_id = latest_reservation(f"B{tag}")["id"]
check("overlapping request can be filed while both are pending", b_id != a)
check("student cannot view someone else's reservation", student2.get(f"/reservations/{a}").status_code == 403)
check("student cannot approve", student.post(f"/reservations/{a}/approve").status_code == 403)

print("Approval workflow")
staff.post(f"/reservations/{a}/approve")
check("staff approval sets APPROVED", latest_reservation(f"A{tag}")["status"] == "APPROVED")
check("approval takes materials out of stock", stock("Projector") == avail - 2)
check("reviewer is recorded", one("SELECT staff_id AS s FROM reservation WHERE reservation_id=%s", (a,))["s"] is not None)
r = staff.post(f"/reservations/{b_id}/approve")
check("overlapping second approval is blocked", "overlapping" in r.get_data(as_text=True))
check("blocked approval left B pending", latest_reservation(f"B{tag}")["status"] == "PENDING")
check("blocked approval left stock unchanged", stock("Projector") == avail - 2)
r = request_room(student2, f"C{tag}", "09:30", "10:30")
check("new request over an approved booking is refused", "overlapping" in r.get_data(as_text=True))
rooms_page = staff.get(f"/rooms?date={day}&start=10:00&end=10:30").get_data(as_text=True)
check("room availability search shows the booked room", "Already booked then" in rooms_page)
check("availability search shows other rooms free", "Free at that time" in rooms_page)

print("Cancel, complete, penalties")
staff.post(f"/reservations/{b_id}/reject")
check("staff can reject a pending request", latest_reservation(f"B{tag}")["status"] == "REJECTED")
student.post(f"/reservations/{a}/cancel")
check("owner can cancel an approved reservation", latest_reservation(f"A{tag}")["status"] == "CANCELLED")
check("cancelling returns materials to stock", stock("Projector") == avail)

request_room(student, f"D{tag}", "13:00", "14:00", qty=1)
d_id = latest_reservation(f"D{tag}")["id"]
staff.post(f"/reservations/{d_id}/approve")
staff.post(f"/reservations/{d_id}/complete")
check("completing marks COMPLETED", latest_reservation(f"D{tag}")["status"] == "COMPLETED")
check("completing returns materials", stock("Projector") == avail)
staff.post(f"/reservations/{d_id}/penalty", {"reason": "LATE_RETURN", "amount": "300"})
check("penalty is recorded", one("SELECT COUNT(*) AS n FROM penalty WHERE reservation_id=%s", (d_id,))["n"] == 1)
r = staff.post(f"/reservations/{d_id}/penalty", {"reason": "NO_SHOW", "amount": "50"})
check("second penalty on same reservation is refused", "already has a penalty" in r.get_data(as_text=True))
check("student sees their penalty", "Late return" in student.get("/penalties").get_data(as_text=True))
check("student cannot issue penalties", student.post(f"/reservations/{d_id}/penalty", {"reason": "NO_SHOW", "amount": "1"}).status_code == 403)

print("Penalty limit")
pid = one("SELECT penalty_id AS id FROM penalty WHERE reservation_id=%s", (d_id,))["id"]
request_room(student, f"E{tag}", "15:00", "16:00", qty=0)
e_id = latest_reservation(f"E{tag}")["id"]
staff.post(f"/reservations/{e_id}/approve"); staff.post(f"/reservations/{e_id}/complete")
staff.post(f"/reservations/{e_id}/penalty", {"reason": "DAMAGED_MATERIAL", "amount": "300"})
r = request_room(student, f"F{tag}", "17:00", "18:00", qty=0)
check("unpaid penalties above the limit block new requests", "unpaid penalties" in r.get_data(as_text=True))
check("blocked request was not saved", latest_reservation(f"F{tag}") is None)
staff.post(f"/penalties/{pid}/pay")
check("marking paid records paid_date", one("SELECT paid_date AS d FROM penalty WHERE penalty_id=%s", (pid,))["d"] is not None)
r = request_room(student, f"G{tag}", "17:00", "18:00", qty=0)
check("requests work again once the total is under the limit", "Request submitted" in r.get_data(as_text=True))
# Clean up so the test can be run again without tripping the penalty limit
staff.post(f"/penalties/{one('SELECT penalty_id AS id FROM penalty WHERE reservation_id=%s', (e_id,))['id']}/pay")

print("Admin and inventory")
check("admin can add a department", "Department added" in admin.post("/admin/departments", {"department_name": f"Dept {tag}"}).get_data(as_text=True))
check("admin can create staff", "Staff account created" in admin.post("/admin/staff", {"full_name": "Pat Test", "email": f"pat{tag}@reserveit.test", "password": "longenough1", "role": "STAFF"}).get_data(as_text=True))
uid = one("SELECT user_id AS id FROM app_user WHERE email='student2@reserveit.test'")["id"]
admin.post(f"/admin/users/{uid}/status")
r = request_room(student2, f"H{tag}", "09:00", "10:00", qty=0)
check("suspended user cannot reserve", "suspended" in r.get_data(as_text=True))
admin.post(f"/admin/users/{uid}/status")
staff.post("/materials/new", {"material_name": f"Item{tag}", "category": "SUPPLIES", "total_quantity": "5"})
mid = one("SELECT material_id AS id FROM material WHERE material_name=%s", (f"Item{tag}",))["id"]
check("staff can add a material", mid is not None)
staff.post(f"/materials/{mid}/edit", {"material_name": f"Item{tag}", "category": "SUPPLIES", "total_quantity": "8"})
check("editing total shifts available too", one("SELECT available_quantity AS n FROM material WHERE material_id=%s", (mid,))["n"] == 8)
staff.post(f"/materials/{mid}/delete")
check("unused material can be deleted", one("SELECT COUNT(*) AS n FROM material WHERE material_id=%s", (mid,))["n"] == 0)
r = staff.post(f"/rooms/{room_id}/delete")
check("room with history cannot be deleted", "cannot be deleted" in r.get_data(as_text=True))

print(f"\nAll {passed} checks passed.")
