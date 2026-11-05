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

- Python 3.10 or newer ([python.org](https://www.python.org/downloads/); check **Add python.exe to PATH**).
  If `pip install` fails on a very new Python, use 3.11 or 3.12.
- PostgreSQL 16 or newer, running on port 5432
- The password of the PostgreSQL `postgres` superuser (needed once, for step 4)
- Git

## Setup (Windows, VS Code terminal)

Run every command in the folder that contains `manage.py`, one at a time, and read the output before moving on.
On macOS/Linux use `python3` and `source venv/bin/activate`.

> **Important order:** create the database (step 2) and set `DB_NAME` in `.env` (step 3) **before** running
> `setup-roles` (step 4). Setup grants privileges to the database named in `DB_NAME`. If the name is wrong,
> you will get errors such as `permission denied to create extension "btree_gist"`.

**1. Get the code and install packages**
```
git clone https://github.com/sev-villanueva/ReserveIT-Classroom-and-Material-Reservation-System-.git
cd ReserveIT-Classroom-and-Material-Reservation-System-
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```
If PowerShell says scripts are disabled, run
`Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned` and activate again.

**2. Create an empty database** (once, as the `postgres` user)

The easiest way is pgAdmin: right-click **Databases > Create > Database...**, name it `ReserveIT`, and save.

Or with the command line:
```
psql -U postgres -c "CREATE DATABASE \"ReserveIT\";"
```
If Windows says `psql` is not recognized, use pgAdmin instead, or run it with its full path, for example
`& "C:\Program Files\PostgreSQL\18\bin\psql.exe" -U postgres -c 'CREATE DATABASE "ReserveIT";'`

Any database name works, but `DB_NAME` in `.env` must match it exactly, including capital letters.

**3. Create your settings file**
```
copy .env.example .env
```
Open `.env` and set:
- `DB_NAME` to the database you created in step 2
- four different passwords: `DB_PASSWORD`, `DB_OWNER_PASSWORD`, `DB_REPORT_PASSWORD`, `DB_DBA_PASSWORD`
- `SECRET_KEY` to any long random text

`.env` is ignored by Git, so nothing secret is committed. Never put real passwords in `.env.example`.

**4. Create the database accounts** (asks for the `postgres` password once; it is not saved)
```
python manage.py setup-roles
```
Nothing shows on screen while you type the password. Just press Enter.

**5. Create the tables and load sample data**
```
python manage.py init-db     # creates the 8 tables and applies the privileges
python manage.py seed        # sample departments, rooms, materials, accounts, reservations
python manage.py check       # should say: Connected to database 'ReserveIT' as 'reserveit_app'
```
Read the database name in the `check` line. It must be the one you intended.

**6. Run the app**
```
python manage.py run
```
Open <http://127.0.0.1:5000> and log in with a sample account. Press Ctrl+C in the terminal to stop it.

## Sample accounts (testing only)

These are throwaway passwords for a development database. Never use them in production.

| Email | Role | Password |
|---|---|---|
| admin@reserveit.test | Administrator | ChangeMe123! |
| staff@reserveit.test | Staff | ChangeMe123! |
| pat5012@reserveit.test | Staff | ChangeMe123! |
| student@reserveit.test | Student | ChangeMe123! |
| faculty@reserveit.test | Faculty | ChangeMe123! |
| student2@reserveit.test | Student (has an unpaid sample penalty) | ChangeMe123! |

## Verify the install

```
python tests/smoke_test.py     # 67 checks: login, reservations, conflicts, approvals, penalties, permissions
python tests/access_test.py    # 48 checks: each database account can do its job and nothing more
```
Both add or touch a few rows, so use a development database. `access_test.py` rolls back everything it tries.

## Commands

| Command | Account used | Purpose |
|---|---|---|
| `python manage.py setup-roles` | postgres (asked once) | Create the roles and login accounts, and set privileges on the database named in `DB_NAME` |
| `python manage.py init-db` | owner | Create tables from `database/schema.sql`, then apply `database/grants.sql` |
| `python manage.py seed` | owner | Load `database/seed.sql` (run once on an empty database) |
| `python manage.py grants` | owner | Re-apply the privileges (after adding a table) |
| `python manage.py check` | app | Test the connection and print the database name; warns if the account is a superuser |
| `python manage.py reset-db` | owner | **Deletes everything** in the database named in `DB_NAME` and rebuilds it with sample data (asks you to type YES) |
| `python manage.py run` | app | Start the web app on port 5000 |

Run `python manage.py check` before `reset-db` and read the database name it prints.

Using pgAdmin instead of `manage.py`? See the comments at the top of `database/roles_setup.sql`.

## Using a second database on the same computer

PostgreSQL roles belong to the whole server, not to one database. If you already ran `setup-roles` for one
database and want another (for example `ReserveIT_test`):

1. Create the new empty database.
2. Set `DB_NAME` to the new name in `.env`.
3. Use the **same four passwords** as before, because running `setup-roles` again resets them.
4. Run `setup-roles`, `init-db`, `seed` and `check` again, and confirm `check` prints the new name.

Any other project folder that uses these roles must have the same passwords in its `.env`.

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
| `DB_HOST`, `DB_PORT`, `DB_NAME` | Where PostgreSQL runs and the database name (must match exactly) |
| `DB_USER`, `DB_PASSWORD` | The web app's account (`reserveit_app`) |
| `DB_OWNER_USER`, `DB_OWNER_PASSWORD` | The table owner, used for setup only |
| `DB_REPORT_PASSWORD`, `DB_DBA_PASSWORD` | Passwords for the reporting and maintenance accounts |
| `DB_SUPERUSER` | Superuser name for `setup-roles` (default `postgres`) |
| `DB_SUPERUSER_PASSWORD` | Optional. If set, `setup-roles` does not ask for the password. Leave it blank so nobody saves it by accident |
| `SECRET_KEY` | Signs login sessions: **change it** |
| `PENALTY_THRESHOLD` | Unpaid penalties above this amount (₱) block new requests (default 500) |

## Common problems

| Message | Cause and fix |
|---|---|
| `psql` is not recognized | PostgreSQL's `bin` folder is not on PATH. Create the database in pgAdmin instead |
| `permission denied to create extension "btree_gist"` | `setup-roles` ran for a different database. Fix `DB_NAME` in `.env`, then run `setup-roles` again |
| `relation "department" already exists` | The tables exist already, often because `DB_NAME` points at an older database. Run `python manage.py check` to see which one |
| `password authentication failed` | The passwords in `.env` differ from the ones the roles were created with. Run `setup-roles` again |
| `FAIL the PUBLIC pseudo-role cannot connect to the database` | `setup-roles` ran against another database name. Fix `DB_NAME` and run `setup-roles` again |

More: [docs/troubleshooting.md](docs/troubleshooting.md).