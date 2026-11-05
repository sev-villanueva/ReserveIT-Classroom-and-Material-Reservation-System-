# User roles and PostgreSQL roles

ReserveIT has two layers of roles. Keep them separate:

- **Application roles** decide what a person can do after logging in to the web app. They are stored in the
  `app_user.role` and `staff.role` columns and enforced by the application code.
- **PostgreSQL roles** decide what a database account can do. The web app connects through one runtime account;
  individual end users do not have their own database logins.

## Application roles mapped to database roles

| Application role | Responsibilities | Functions and data access | Intended database role |
|---|---|---|---|
| Requester (STUDENT or FACULTY) | Request rooms and materials for classes and events | Register, view rooms and materials, check availability, submit requests, view and cancel own reservations, view own penalties. Cannot see other people's reservations | The web app connects as `reserveit_app`, member of `app_runtime_grp` |
| Staff (STAFF) | Review requests and run the catalogs | View all reservations, approve, reject, complete, and cancel them, record and settle penalties, add, edit, and delete rooms and materials, view dashboards | The web app connects as `reserveit_app`, member of `app_runtime_grp` |
| Administrator (ADMIN) | Manage accounts and departments | Everything staff can do, plus add departments, create staff accounts, deactivate staff, suspend requesters | The web app connects as `reserveit_app`, member of `app_runtime_grp` |
| Report viewer (outside the web app) | Read usage and penalty data | Read-only access to reservations, rooms, materials, and penalties. No emails or password hashes | `reserveit_reporter`, member of `app_readonly_grp` |
| Database maintainer | Correct data, investigate problems | Read and change rows in all tables. Cannot change table structure or create roles | `reserveit_dba`, member of `app_admin_grp` |
| Schema owner | Create tables, run setup and sample data | Owns the database and tables. Not a superuser | `reserveit_owner` (setup only, never used by the running app) |
| PostgreSQL superuser | Create the roles once | Used only by `setup-roles`; password typed when asked | `postgres` (never used by the app) |

The three web-app roles share one database account because the app, not PostgreSQL, decides what each signed-in
person may do. The database privileges cap what that account can ever do (see
[access-requirements.md](access-requirements.md) for the table-by-table list and reasons).

## PostgreSQL roles

| Role | Type | Created by | Privileges |
|---|---|---|---|
| `app_runtime_grp` | Group (NOLOGIN) | `roles_setup.sql` | Narrow, table by table: see access-requirements.md |
| `app_readonly_grp` | Group (NOLOGIN) | `roles_setup.sql` | SELECT on report tables; people tables without email and password columns |
| `app_admin_grp` | Group (NOLOGIN) | `roles_setup.sql` | SELECT, INSERT, UPDATE, DELETE on all tables; no structure changes |
| `reserveit_app` | Login | `roles_setup.sql` | Member of `app_runtime_grp` |
| `reserveit_reporter` | Login | `roles_setup.sql` | Member of `app_readonly_grp` |
| `reserveit_dba` | Login | `roles_setup.sql` | Member of `app_admin_grp` |
| `reserveit_owner` | Login | `roles_setup.sql` | Owns the database and tables; cannot create roles or databases |

None of the five accounts is a superuser. Privileges on tables are applied by `database/grants.sql`.
Connecting to the database is refused for anyone who is not granted CONNECT (the PUBLIC default is removed).

## Setup

```
python manage.py setup-roles
python manage.py init-db
python manage.py seed
```

`setup-roles` reads the four passwords from your `.env` (`DB_PASSWORD`, `DB_OWNER_PASSWORD`, `DB_REPORT_PASSWORD`,
`DB_DBA_PASSWORD`) and asks once for the `postgres` password. Passwords never appear in the repository.

If you run `python manage.py reset-db`, the privileges are re-applied automatically.

## Verify

```
python tests/access_test.py
```

Or try it by hand with psql:

```
psql -U reserveit_app      -d ReserveIT -c "SELECT count(*) FROM room;"           -- works
psql -U reserveit_app      -d ReserveIT -c "DELETE FROM reservation;"             -- permission denied
psql -U reserveit_reporter -d ReserveIT -c "SELECT password_hash FROM app_user;"  -- permission denied
psql -U reserveit_dba      -d ReserveIT -c "DROP TABLE penalty;"                  -- must be owner
```

## Sample application accounts

Created by `seed.sql`, all with password `ChangeMe123!` (testing only):
`admin@reserveit.test` (ADMIN), `staff@reserveit.test` (STAFF), `student@reserveit.test` (STUDENT),
`faculty@reserveit.test` (FACULTY), `student2@reserveit.test` (STUDENT).
