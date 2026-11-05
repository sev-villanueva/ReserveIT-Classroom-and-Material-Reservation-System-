"""Checks that each database account can do what it needs and is refused everything else.

Run after setup (setup-roles, init-db, seed) with:  python tests/access_test.py

It uses the passwords in .env: DB_PASSWORD (app), DB_OWNER_PASSWORD, DB_REPORT_PASSWORD, DB_DBA_PASSWORD.
Every statement runs inside a transaction that is rolled back, so no data is changed.
"""
import os
import sys
from pathlib import Path

import psycopg2
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
load_dotenv()

from app.db import connect  # noqa: E402

ACCOUNTS = {
    "app": (os.getenv("DB_USER", "reserveit_app"), os.getenv("DB_PASSWORD", "")),
    "reporter": ("reserveit_reporter", os.getenv("DB_REPORT_PASSWORD", "")),
    "dba": ("reserveit_dba", os.getenv("DB_DBA_PASSWORD", "")),
    "owner": (os.getenv("DB_OWNER_USER", "reserveit_owner"), os.getenv("DB_OWNER_PASSWORD", "")),
}

ALLOW, DENY = "allowed", "denied"

# (account, what is being tried, SQL, expected result). "WHERE false" tests the privilege without touching rows.
CASES = [
    # --- web application account
    ("app", "read rooms", "SELECT * FROM room", ALLOW),
    ("app", "read login data (password_hash) for sign-in", "SELECT email, password_hash FROM app_user", ALLOW),
    ("app", "register a new user", "INSERT INTO department (department_name) VALUES ('access-test')", ALLOW),
    ("app", "suspend or reactivate an account (status column)", "UPDATE app_user SET status = status WHERE false", ALLOW),
    ("app", "approve a reservation (status, staff_id)", "UPDATE reservation SET status = status, staff_id = staff_id WHERE false", ALLOW),
    ("app", "mark a penalty paid", "UPDATE penalty SET paid_status = paid_status, paid_date = paid_date WHERE false", ALLOW),
    ("app", "edit and delete rooms", "DELETE FROM room WHERE false", ALLOW),
    ("app", "delete a material", "DELETE FROM material WHERE false", ALLOW),
    ("app", "change a user's password hash", "UPDATE app_user SET password_hash = 'x' WHERE false", DENY),
    ("app", "change a reservation's purpose or date", "UPDATE reservation SET purpose = 'x' WHERE false", DENY),
    ("app", "change a penalty amount", "UPDATE penalty SET amount = 0 WHERE false", DENY),
    ("app", "delete reservations", "DELETE FROM reservation WHERE false", DENY),
    ("app", "delete penalties", "DELETE FROM penalty WHERE false", DENY),
    ("app", "delete user accounts", "DELETE FROM app_user WHERE false", DENY),
    ("app", "delete staff accounts", "DELETE FROM staff WHERE false", DENY),
    ("app", "delete departments", "DELETE FROM department WHERE false", DENY),
    ("app", "edit reservation line items", "UPDATE reservation_material SET quantity_requested = 1 WHERE false", DENY),
    ("app", "empty a table", "TRUNCATE room", DENY),
    ("app", "create a table", "CREATE TABLE zz_access_test (id int)", DENY),
    ("app", "drop a table", "DROP TABLE penalty", DENY),
    ("app", "create a role", "CREATE ROLE zz_access_role", DENY),
    ("app", "create a database", "CREATE DATABASE zz_access_db", DENY),
    # --- read-only reporting account
    ("reporter", "read reservations", "SELECT * FROM reservation", ALLOW),
    ("reporter", "read penalties", "SELECT * FROM penalty", ALLOW),
    ("reporter", "read user names and status", "SELECT user_id, first_name, last_name, role, status FROM app_user", ALLOW),
    ("reporter", "read password hashes", "SELECT password_hash FROM app_user", DENY),
    ("reporter", "read staff password hashes", "SELECT password_hash FROM staff", DENY),
    ("reporter", "read user email addresses", "SELECT email FROM app_user", DENY),
    ("reporter", "insert data", "INSERT INTO department (department_name) VALUES ('access-test')", DENY),
    ("reporter", "update data", "UPDATE room SET capacity = capacity WHERE false", DENY),
    ("reporter", "delete data", "DELETE FROM room WHERE false", DENY),
    ("reporter", "create a table", "CREATE TABLE zz_access_test (id int)", DENY),
    # --- maintenance (DBA) account
    ("dba", "read everything", "SELECT * FROM app_user", ALLOW),
    ("dba", "correct data", "UPDATE reservation SET purpose = purpose WHERE false", ALLOW),
    ("dba", "remove bad records", "DELETE FROM penalty WHERE false", ALLOW),
    ("dba", "change the table structure", "ALTER TABLE room ADD COLUMN zz_test int", DENY),
    ("dba", "create a table", "CREATE TABLE zz_access_test (id int)", DENY),
    ("dba", "drop a table", "DROP TABLE penalty", DENY),
    ("dba", "create a role", "CREATE ROLE zz_access_role", DENY),
    # --- owner account (setup only)
    ("owner", "create and change tables", "CREATE TABLE zz_access_test (id int)", ALLOW),
    ("owner", "create a role", "CREATE ROLE zz_access_role", DENY),
    ("owner", "create a database", "CREATE DATABASE zz_access_db", DENY),
]


def attempt(account, sql, autocommit=False):
    user, password = ACCOUNTS[account]
    conn = connect(user, password)
    conn.autocommit = autocommit
    try:
        with conn.cursor() as cur:
            cur.execute(sql)
        return ALLOW
    except psycopg2.errors.InsufficientPrivilege:
        return DENY
    except psycopg2.Error as exc:
        return f"unexpected error: {str(exc).strip().splitlines()[0]}"
    finally:
        if not autocommit:
            conn.rollback()
        conn.close()


def main():
    missing = [a for a, (u, p) in ACCOUNTS.items() if not p]
    if missing:
        sys.exit("Missing passwords in .env for: " + ", ".join(missing) +
                 " (need DB_PASSWORD, DB_OWNER_PASSWORD, DB_REPORT_PASSWORD, DB_DBA_PASSWORD)")

    failures = 0
    checks = 0
    # CREATE DATABASE cannot run inside a transaction block, so it runs with autocommit on
    rows = [(a, d, s, e, attempt(a, s, autocommit=s.startswith("CREATE DATABASE"))) for a, d, s, e in CASES]

    current = None
    for account, description, _sql, expected, got in rows:
        if account != current:
            current = account
            print(f"\n{account} account ({ACCOUNTS[account][0]})")
        ok = got == expected
        failures += not ok
        checks += 1
        print(f"  {'PASS' if ok else 'FAIL'}  {description}: expected {expected}, got {got}")

    print("\nAccount settings")
    conn = connect(*ACCOUNTS["owner"])
    with conn.cursor() as cur:
        names = [u for u, _ in ACCOUNTS.values()]
        cur.execute("SELECT rolname, rolsuper, rolcreatedb, rolcreaterole FROM pg_roles WHERE rolname = ANY(%s)", (names,))
        for r in cur.fetchall():
            ok = not (r["rolsuper"] or r["rolcreatedb"] or r["rolcreaterole"])
            failures += not ok
            checks += 1
            print(f"  {'PASS' if ok else 'FAIL'}  {r['rolname']} is not a superuser and cannot create roles or databases")
        cur.execute("""SELECT NOT EXISTS (SELECT 1 FROM pg_database d, aclexplode(d.datacl) a
                       WHERE d.datname = current_database() AND a.grantee = 0 AND a.privilege_type = 'CONNECT') AS ok""")
        ok = cur.fetchone()["ok"]
        failures += not ok
        checks += 1
        print(f"  {'PASS' if ok else 'FAIL'}  the PUBLIC pseudo-role cannot connect to the database")
        cur.execute("SELECT DISTINCT tableowner FROM pg_tables WHERE schemaname = 'public'")
        owners = [r["tableowner"] for r in cur.fetchall()]
        ok = owners == [ACCOUNTS["owner"][0]]
        failures += not ok
        checks += 1
        print(f"  {'PASS' if ok else 'FAIL'}  all tables are owned by {ACCOUNTS['owner'][0]} (found: {', '.join(owners)})")
    conn.close()

    print(f"\n{'All ' + str(checks) + ' access checks passed.' if not failures else str(failures) + ' check(s) FAILED.'}")
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
