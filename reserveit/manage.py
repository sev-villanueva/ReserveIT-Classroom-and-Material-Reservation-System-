"""Command-line helper for ReserveIT.

  python manage.py setup-roles   create the database roles and accounts (asks for the postgres password once)
  python manage.py init-db       create the tables, then apply the privileges
  python manage.py seed          load sample data
  python manage.py grants        re-apply the privileges in database/grants.sql
  python manage.py check         test the app account's connection
  python manage.py reset-db      DROP everything, then rebuild the tables, privileges, and sample data
  python manage.py run           start the web app at http://127.0.0.1:5000

Which account does what (details in docs/user-roles.md):
  setup-roles          PostgreSQL superuser (DB_SUPERUSER, default postgres), password typed when asked
  init-db / seed / grants / reset-db   owner account (DB_OWNER_USER / DB_OWNER_PASSWORD)
  check / run          normal app account (DB_USER / DB_PASSWORD)
"""
import getpass
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

from app.db import connect  # noqa: E402  (needs .env loaded first)

SQL_DIR = Path(__file__).parent / "database"


def env(name, default=""):
    return os.getenv(name, default)


def owner_connection():
    """The account that owns the tables. Falls back to the app account only if DB_OWNER_USER is not set."""
    user = env("DB_OWNER_USER")
    if user:
        return connect(user, env("DB_OWNER_PASSWORD"))
    print("Note: DB_OWNER_USER is not set in .env, so the normal app account is being used for setup.")
    return connect()


def superuser_connection():
    user = env("DB_SUPERUSER", "postgres")
    password = env("DB_SUPERUSER_PASSWORD") or getpass.getpass(
        f"Password for PostgreSQL superuser '{user}' (used for this step only, not saved): ")
    return connect(user, password)


def run_sql(conn, filename, params=None, replace=None):
    text = (SQL_DIR / filename).read_text(encoding="utf-8")
    for old, new in (replace or {}).items():
        text = text.replace(old, new)
    with conn.cursor() as cur:
        cur.execute(text, params) if params else cur.execute(text)
    conn.commit()
    print(f"OK: ran database/{filename}")


def roles_exist(conn):
    with conn.cursor() as cur:
        cur.execute("SELECT 1 FROM pg_roles WHERE rolname = 'app_runtime_grp'")
        return cur.fetchone() is not None


def apply_grants(conn):
    if roles_exist(conn):
        run_sql(conn, "grants.sql")
    else:
        print("Skipped database/grants.sql because the roles do not exist yet.\n"
              "Run: python manage.py setup-roles   and then: python manage.py grants")


def setup_roles():
    names = {"DB_OWNER_PASSWORD": "owner_pw", "DB_PASSWORD": "app_pw",
             "DB_REPORT_PASSWORD": "report_pw", "DB_DBA_PASSWORD": "dba_pw"}
    missing = [n for n in names if not env(n)]
    if missing:
        raise SystemExit("Add these lines to your .env file first (choose any password for each): " + ", ".join(missing))
    quoted_db = '"' + env("DB_NAME", "ReserveIT").replace('"', '""') + '"'
    conn = superuser_connection()
    run_sql(conn, "roles_setup.sql", params={v: env(k) for k, v in names.items()}, replace={"__DBNAME__": quoted_db})
    conn.close()
    print("\nRoles created: reserveit_owner, reserveit_app, reserveit_reporter, reserveit_dba.\n"
          "Next: python manage.py init-db   then   python manage.py seed")


def check():
    conn = connect()
    with conn.cursor() as cur:
        cur.execute("SELECT version() AS v, current_database() AS db, current_user AS u, "
                    "(SELECT rolsuper FROM pg_roles WHERE rolname = current_user) AS su")
        row = cur.fetchone()
    conn.close()
    print(f"Connected to database '{row['db']}' as '{row['u']}'.\n{row['v']}")
    if row["su"]:
        print("\nWARNING: this account is a PostgreSQL superuser. Ordinary application access must use a "
              "least-privilege account.\nRun python manage.py setup-roles and set DB_USER=reserveit_app in .env.")


def reset():
    answer = input("This DELETES every table and all data in the configured database. Type YES to continue: ")
    if answer.strip() != "YES":
        print("Cancelled.")
        return
    conn = owner_connection()
    with conn.cursor() as cur:
        cur.execute("DROP SCHEMA public CASCADE; CREATE SCHEMA public;")
    conn.commit()
    run_sql(conn, "schema.sql")
    apply_grants(conn)
    run_sql(conn, "seed.sql")
    conn.close()


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "check":
        check()
    elif cmd == "setup-roles":
        setup_roles()
    elif cmd in ("init-db", "seed", "grants"):
        conn = owner_connection()
        if cmd == "init-db":
            run_sql(conn, "schema.sql")
            apply_grants(conn)
        elif cmd == "seed":
            run_sql(conn, "seed.sql")
        else:
            run_sql(conn, "grants.sql")
        conn.close()
    elif cmd == "reset-db":
        reset()
    elif cmd == "run":
        from app import create_app
        create_app().run(debug=True)
    else:
        print(__doc__)


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception as exc:  # friendly message instead of a long traceback for common setup problems
        print(f"\nFailed: {exc}\nSee docs/troubleshooting.md.")
        sys.exit(1)
