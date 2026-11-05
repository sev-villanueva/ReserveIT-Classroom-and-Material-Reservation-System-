# User roles and PostgreSQL roles

ReserveIT has two layers of "roles". Keep them separate:

- **Application roles** decide what a person can do after logging in to the web app. They are stored in the
  `app_user.role` and `staff.role` columns.
- **PostgreSQL roles** decide what a database *account* can do. The web app connects with one runtime account;
  individual end users do not need their own database logins.

## Application roles

| Role | Stored in | Can do | Cannot do |
|---|---|---|---|
| STUDENT / FACULTY | `app_user.role` | Register, view rooms and materials, check availability, submit requests, view and cancel own reservations, view own penalties | Approve requests, see other people's reservations, change rooms or materials |
| STAFF | `staff.role` | View all reservations, approve/reject/complete/cancel, record and settle penalties, add/edit/delete rooms and materials, view dashboard reports | Submit reservation requests, manage accounts and departments |
| ADMIN | `staff.role` | All staff actions, plus add departments, create staff accounts, deactivate staff, suspend or reactivate requesters | Deactivate their own account |

Account states: requesters are ACTIVE or SUSPENDED (a suspended requester can log in but cannot submit requests);
staff are ACTIVE or INACTIVE (an inactive staff member cannot log in).

## PostgreSQL roles (`database/roles_setup.sql`)

| PostgreSQL role | Type | Privileges | Used by |
|---|---|---|---|
| `app_readonly_grp` | Group (NOLOGIN) | CONNECT, SELECT on all tables | Reporting accounts |
| `app_readwrite_grp` | Group (NOLOGIN) | Inherits read-only, plus INSERT, UPDATE, DELETE and sequence use | The web app |
| `app_admin_grp` | Group (NOLOGIN) | Inherits read/write, plus ALL on tables and sequences | Database administrators (DDL stays with the table owner, `postgres`) |
| `reserveit_app` | Login | Member of `app_readwrite_grp` | The Flask app (set in `.env`) |
| `reserveit_reporter` | Login | Member of `app_readonly_grp` | Read-only reports and checking data |

### Mapping

| Application role | Database account used |
|---|---|
| STUDENT, FACULTY, STAFF, ADMIN (all via the web app) | `reserveit_app` (read/write group) |
| Report viewer outside the app | `reserveit_reporter` (read-only group) |
| Database administrator | `postgres` or a member of `app_admin_grp` |

Application roles are enforced by the app code (`app/auth.py` decorators). Database roles are enforced by PostgreSQL.
The app never gives end users direct database access.

## Setup

Run after the tables exist (`python manage.py init-db`):

```
psql -U postgres -d grp01_appdb -v app_pw="'choose_a_password'" -v report_pw="'choose_another'" -f database/roles_setup.sql
```

The passwords are passed on the command line so they never appear in the repo. The script can be re-run safely.

**Important:** if you run `python manage.py reset-db`, it recreates the schema and removes the grants. Run
`roles_setup.sql` again afterwards.

## Verify

```
psql -U reserveit_app -d grp01_appdb -c "SELECT count(*) FROM room;"      -- works
psql -U reserveit_app -d grp01_appdb -c "DROP TABLE penalty;"             -- ERROR: must be owner
psql -U reserveit_reporter -d grp01_appdb -c "DELETE FROM room;"          -- ERROR: permission denied
```

## Sample application accounts

Created by `seed.sql`, all with password `ChangeMe123!` (testing only):
`admin@reserveit.test` (ADMIN), `staff@reserveit.test` (STAFF), `student@reserveit.test` (STUDENT),
`faculty@reserveit.test` (FACULTY), `student2@reserveit.test` (STUDENT).
