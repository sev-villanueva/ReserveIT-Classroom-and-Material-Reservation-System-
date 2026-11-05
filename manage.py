"""Command-line helper for ReserveIT.

  python manage.py check      test the database connection
  python manage.py init-db    create all tables (database/schema.sql)
  python manage.py seed       load sample data (database/seed.sql)
  python manage.py reset-db   DROP everything, then run init-db and seed
  cd reserveit                before running the app
  python manage.py run        start the web app at http://127.0.0.1:5000
  staff email                 staff@reserveit.test 
  password of my staff        ChangeMe123!
"""
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

from app.db import connect  # noqa: E402  (needs .env loaded first)

SQL_DIR = Path(__file__).parent / "database"


def run_sql_file(name):
    conn = connect()
    try:
        with conn, conn.cursor() as cur:
            cur.execute((SQL_DIR / name).read_text(encoding="utf-8"))
        print(f"OK: ran database/{name}")
    finally:
        conn.close()


def check():
    conn = connect()
    with conn.cursor() as cur:
        cur.execute("SELECT version() AS v, current_database() AS db")
        row = cur.fetchone()
    conn.close()
    print(f"Connected to database '{row['db']}'.\n{row['v']}")


def reset():
    answer = input("This DELETES every table and all data in the configured database. Type YES to continue: ")
    if answer.strip() != "YES":
        print("Cancelled.")
        return
    conn = connect()
    with conn, conn.cursor() as cur:
        cur.execute("DROP SCHEMA public CASCADE; CREATE SCHEMA public;")
    conn.close()
    run_sql_file("schema.sql")
    run_sql_file("seed.sql")


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "check":
        check()
    elif cmd == "init-db":
        run_sql_file("schema.sql")
    elif cmd == "seed":
        run_sql_file("seed.sql")
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
    except Exception as exc:  # friendly message instead of a long traceback for common setup problems
        print(f"\nFailed: {exc}\nSee docs/troubleshooting.md.")
        sys.exit(1)
