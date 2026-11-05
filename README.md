<<<<<<< HEAD
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

Details and the PostgreSQL role mapping are in [docs/user-roles.md](docs/user-roles.md).

## Prerequisites

- Python 3.10 or newer ([python.org](https://www.python.org/downloads/); tick **Add python.exe to PATH**)
- PostgreSQL 16 or newer, running on port 5432, with the `postgres` superuser password known
- Git
- The `btree_gist` extension, which ships with the standard PostgreSQL installer (contrib modules)

## Setup (Windows, VS Code terminal)

Run these in the project folder. On macOS/Linux use `python3` and `source venv/bin/activate`.

**1. Get the code and create a virtual environment**
```
git clone <repo-url>
cd reserveit
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

**2. Create the database** (once, in psql or pgAdmin)
```
psql -U postgres -c "CREATE DATABASE grp01_appdb;"
```

**3. Configure the app**
```
copy .env.example .env
```
Open `.env` and set `DB_PASSWORD` to your PostgreSQL password and `SECRET_KEY` to any long random text.
`.env` is ignored by Git, so your password is never committed.

**4. Create the tables and load sample data**
```
python manage.py check       # should print your PostgreSQL version
python manage.py init-db     # creates the 8 tables from database/schema.sql
python manage.py seed        # loads sample departments, rooms, materials, accounts, reservations
```

**5. Run the app**
```
python manage.py run
```
Open <http://127.0.0.1:5000> and log in with a sample account.

**6. (Optional) Create the PostgreSQL roles** so the app can run without the superuser. Run this *after* step 4:
```
psql -U postgres -d grp01_appdb -v app_pw="'choose_a_password'" -v report_pw="'choose_another'" -f database/roles_setup.sql
```
Then set `DB_USER=reserveit_app` and `DB_PASSWORD=choose_a_password` in `.env`. See [docs/user-roles.md](docs/user-roles.md).

## Sample accounts (testing only)

All sample accounts use the password `ChangeMe123!`. They exist only in the seed data. Delete them before any real use.

| Email | Role |
|---|---|
| admin@reserveit.test | Administrator |
| staff@reserveit.test | Staff |
| student@reserveit.test | Student |
| faculty@reserveit.test | Faculty |
| student2@reserveit.test | Student (has an unpaid sample penalty) |

## Verify the install

```
python tests/smoke_test.py
```
It runs 67 checks across login, reservations, conflict prevention, approvals, stock counts, penalties, and permissions.
It adds a few rows each run, so use it on a development database only.

## Useful commands

| Command | Purpose |
|---|---|
| `python manage.py check` | Test the database connection |
| `python manage.py init-db` | Create tables from `database/schema.sql` |
| `python manage.py seed` | Load `database/seed.sql` (run once on an empty database) |
| `python manage.py reset-db` | Delete everything and rebuild with sample data (asks for confirmation) |
| `python manage.py run` | Start the web app on port 5000 |

Prefer plain SQL? `psql -U postgres -d grp01_appdb -f database/schema.sql` followed by `-f database/seed.sql`
does the same as `init-db` and `seed`.

## Project layout

```
reserveit/
├── app/                  Flask application (routes, templates, styles)
├── database/
│   ├── schema.sql        8 tables, keys, constraints, indexes
│   ├── seed.sql          sample data
│   └── roles_setup.sql   PostgreSQL group and login roles
├── docs/
│   ├── database.md       tables, relationships, constraints, changes from Activity 2
│   ├── user-roles.md     application roles and PostgreSQL role mapping
│   └── troubleshooting.md
├── tests/smoke_test.py
├── manage.py
├── requirements.txt
└── .env.example
```

## Settings (`.env`)

| Variable | Meaning | Default |
|---|---|---|
| `DB_HOST`, `DB_PORT` | Where PostgreSQL runs | `localhost`, `5432` |
| `DB_NAME` | Database name | `grp01_appdb` |
| `DB_USER`, `DB_PASSWORD` | Database login | `postgres`, empty |
| `SECRET_KEY` | Signs login sessions | development placeholder: **change it** |
| `PENALTY_THRESHOLD` | Unpaid penalties above this amount (₱) block new requests | `500` |

Problems? See [docs/troubleshooting.md](docs/troubleshooting.md).

