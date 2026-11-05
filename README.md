# ReserveIT: Classroom and Material Reservation System

Students and faculty request classrooms and shared materials (projectors, extension cords, sound systems) online.
Staff review and approve requests. The database prevents double-booked rooms and over-borrowed equipment, and
records penalties for no-shows, damage, and late returns.

**Stack:** Python 3.10+ (Flask), PostgreSQL 16 or newer (built for 18), plain HTML/CSS. No JavaScript build step.

**Group:** BSIT 3-2, COMP 018. Database: `ReserveIT`.

## What it does

| Role | Can do |
|---|---|
| Requester (student or faculty) | Register, check room availability by date and time, request a room with materials, cancel their own requests, view their penalties |
| Staff | Everything a requester can view, plus approve/reject requests, mark them completed, record and settle penalties, and add/edit/delete rooms and materials |
| Administrator (staff with the ADMIN role) | Everything staff can do, plus manage departments and staff accounts, and suspend requester accounts |

## Database security (least privilege)

The app never runs as the PostgreSQL superuser. Setup creates separate accounts, each with only the privileges it needs:

| Account | Group role | Purpose |
|---|---|---|
| `reserveit_owner` | (owns the tables) | Setup only: creates tables, loads sample data |
| `reserveit_app` | `app_runtime_grp` | The web application. Can only do what the app's code does |
| `reserveit_reporter` | `app_readonly_grp` | Read-only reports. Cannot see emails or password hashes |
| `reserveit_dba` | `app_admin_grp` | Maintenance: correct data, but cannot change table structure |

Full privilege tables and reasons: [docs/access-requirements.md](docs/access-requirements.md).
Role mapping: [docs/user-roles.md](docs/user-roles.md).

## Prerequisites

- Python 3.10 or newer ([python.org](https://www.python.org/downloads/); check **Add python.exe to PATH**)
- PostgreSQL 16 or newer, running on port 5432, and the password of its `postgres` superuser (needed once)
- Git

## Setup (Windows, VS Code terminal)

Run these in the folder that contains `manage.py`. On macOS/Linux use `python3` and `source venv/bin/activate`.

**1. Get the code and install packages**
```
git clone <repo-url>
cd reserveit
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

**2. Create an empty database** (once, as the `postgres` user in pgAdmin, or:)
```
psql -U postgres -c "CREATE DATABASE \"ReserveIT\";"
```
Any name works if `DB_NAME` in `.env` matches it exactly, including capital letters.

**3. Create your settings file**
```
copy .env.example .env
```
Open `.env` and choose four different passwords for `DB_PASSWORD`, `DB_OWNER_PASSWORD`, `DB_REPORT_PASSWORD`, and
`DB_DBA_PASSWORD`. Set `SECRET_KEY` to any long random text. `.env` is ignored by Git, so nothing secret is committed.

**4. Create the database accounts** (asks for the `postgres` password once; it is not saved)
```
python manage.py setup-roles
```

**5. Create the tables and load sample data**
```
python manage.py init-db     # creates the 8 tables and applies the privileges
python manage.py seed        # sample departments, rooms, materials, accounts, reservations
python manage.py check       # should say: Connected ... as 'reserveit_app'
```

**6. Run the app**
```
python manage.py run
```
Open <http://127.0.0.1:5000> and log in with a sample account.

## Sample accounts (testing only)

| Email | Role | Passwords
|---|---|---|
| admin@reserveit.test | Administrator | steaven
| staff@reserveit.test | Staff | chann
| pat5012@reserveit.test| Staff | villanueva
| student@reserveit.test | Student | ChangeMe123!
| faculty@reserveit.test | Faculty | ChangeMe123!
| student2@reserveit.test | Student (has an unpaid sample penalty) | ChangeMe123!

## Verify the install

```
python tests/smoke_test.py     # 67 checks: login, reservations, conflicts, approvals, penalties, permissions
python tests/access_test.py    # 48 checks: each database account can do its job and nothing more
```
Both add or touch only a few rows, so use a development database. `access_test.py` rolls back everything it tries.

## Commands

| Command | Account used | Purpose |
|---|---|---|
| `python manage.py setup-roles` | postgres (asked once) | Create the roles and login accounts |
| `python manage.py init-db` | owner | Create tables from `database/schema.sql`, then apply `database/grants.sql` |
| `python manage.py seed` | owner | Load `database/seed.sql` (run once on an empty database) |
| `python manage.py grants` | owner | Re-apply the privileges (after adding a table) |
| `python manage.py check` | app | Test the connection; warns if the account is a superuser |
| `python manage.py reset-db` | owner | Delete everything and rebuild with sample data (asks for confirmation) |
| `python manage.py run` | app | Start the web app on port 5000 |

Using pgAdmin instead of `manage.py`? See the comments at the top of `database/roles_setup.sql`.

## Project layout

```
reserveit/
├── app/                  Flask application (routes, templates, styles)
├── database/
│   ├── roles_setup.sql   roles and login accounts (run by setup-roles)
│   ├── schema.sql        8 tables, keys, constraints, indexes
│   ├── grants.sql        per-table privileges for each role
│   └── seed.sql          sample data
├── docs/
│   ├── database.md       tables, relationships, constraints, changes from Activity 2
│   ├── user-roles.md     application roles mapped to database roles
│   ├── access-requirements.md   what each account needs, table by table, and why
│   └── troubleshooting.md
├── tests/                smoke_test.py (app) and access_test.py (database privileges)
├── manage.py
├── requirements.txt
└── .env.example
```

## Settings (`.env`)

| Variable | Meaning |
|---|---|
| `DB_HOST`, `DB_PORT`, `DB_NAME` | Where PostgreSQL runs and the database name |
| `DB_USER`, `DB_PASSWORD` | The web app's account (`reserveit_app`) |
| `DB_OWNER_USER`, `DB_OWNER_PASSWORD` | The table owner, used for setup only |
| `DB_REPORT_PASSWORD`, `DB_DBA_PASSWORD` | Passwords for the reporting and maintenance accounts |
| `DB_SUPERUSER` | Superuser name for `setup-roles` (default `postgres`) |
| `SECRET_KEY` | Signs login sessions: **change it** |
| `PENALTY_THRESHOLD` | Unpaid penalties above this amount (₱) block new requests (default 500) |

Problems? See [docs/troubleshooting.md](docs/troubleshooting.md).
