# Database access requirements

This document lists what each kind of database access needs, table by table, and why. It is the basis for the
accounts and privileges created by `database/roles_setup.sql` and `database/grants.sql`. Anyone setting up their own
roles for ReserveIT can use the tables below as the requirements.

**Principle: least privilege.** Every account gets only the permissions its job needs. No ordinary account is a
superuser, can create roles or databases, or can change the table structure.

## Who needs access, and for what

| Access need | Who | How they connect | Database role |
|---|---|---|---|
| Run the web application: sign in, register, create and review reservations, manage rooms and materials, record penalties | The Flask app, on behalf of requesters, staff, and administrators | Account `reserveit_app` | `app_runtime_grp` |
| Read data for reports and dashboards outside the app | Report viewer, instructor, auditor | Account `reserveit_reporter` | `app_readonly_grp` |
| Correct data and look into problems | Database maintainer | Account `reserveit_dba` | `app_admin_grp` |
| Create tables, apply changes, load sample data | The person who sets up the database | Account `reserveit_owner` (owns the objects) | none, owns the tables |
| Create the roles and accounts, once | PostgreSQL superuser `postgres` | Password typed once, never saved | superuser, setup only |

## Privileges by table

S = SELECT, I = INSERT, U = UPDATE, D = DELETE. Column names in brackets mean UPDATE is granted on those columns only.

| Table | app_runtime_grp (the app) | app_readonly_grp (reports) | app_admin_grp (maintenance) |
|---|---|---|---|
| department | S, I | S | S, I, U, D |
| app_user | S, I, U [status] | S [user_id, first_name, last_name, role, department_id, status] | S, I, U, D |
| staff | S, I, U [status] | S [staff_id, full_name, role, status] | S, I, U, D |
| room | S, I, D, U [room_name, building, capacity, room_type, status] | S | S, I, U, D |
| material | S, I, D, U [material_name, category, total_quantity, available_quantity] | S | S, I, U, D |
| reservation | S, I, U [status, staff_id] | S | S, I, U, D |
| reservation_material | S, I | S | S, I, U, D |
| penalty | S, I, U [paid_status, paid_date] | S | S, I, U, D |

Also: all three groups get USAGE on schema `public` and CONNECT on the database. The app group gets USAGE on the
ID sequences of the seven tables it inserts into. The maintenance group gets USAGE, SELECT, and UPDATE on all sequences.

## Why the app account gets what it gets

| Privilege | Reason (what in the app needs it) |
|---|---|
| SELECT on `app_user` and `staff`, including `password_hash` | Login compares the typed password with the stored hash |
| INSERT on `app_user` | Registration |
| INSERT on `staff`, `department` | The administrator creates staff accounts and departments |
| UPDATE `status` only on `app_user` and `staff` | The administrator suspends or reactivates accounts. Names, emails, and hashes cannot be changed through the app account |
| INSERT, DELETE, and UPDATE (listed columns) on `room` and `material` | Staff add, edit, and delete rooms and materials. `available_quantity` changes when requests are approved, cancelled, or completed |
| INSERT on `reservation` and `reservation_material` | A requester submits a request with materials |
| UPDATE `status` and `staff_id` only on `reservation` | Approve, reject, cancel, and complete. The date, time, room, and purpose cannot be changed afterwards |
| INSERT on `penalty`; UPDATE `paid_status` and `paid_date` only | Staff record a penalty, then mark it paid. The amount and reason cannot be changed afterwards |
| Row locking (SELECT ... FOR UPDATE) | Approving a request locks the reservation and material rows. PostgreSQL requires UPDATE on at least one column for this, which the grants above provide |

## What the app account is refused

- DELETE on `reservation`, `reservation_material`, `penalty`, `app_user`, `staff`, and `department`. Records are kept for history, so requests are cancelled, not erased
- Changing password hashes, emails, names, reservation details, or penalty amounts after creation
- TRUNCATE, creating or dropping tables, and any structure change (only the owner can)
- Creating roles or databases, and superuser powers

## Why the reporting account is limited

It can read every table needed for reports, but not `app_user.email`, `app_user.password_hash`, `staff.email`, or
`staff.password_hash`. Personal contact details and password hashes are not needed for usage reports. It cannot
INSERT, UPDATE, or DELETE anything. Because some columns are hidden, `SELECT *` on `app_user` or `staff` is refused:
name the columns instead.

## Why the maintenance account is limited

It can read and correct any row, which is what fixing mistakes requires, but it cannot change the table structure,
create roles or databases, or act as a superuser. Structure changes are done by `reserveit_owner`.

## Known limits

- The web app uses one database account for every user, so the difference between a requester, staff, and an
  administrator is enforced by the application code, not by PostgreSQL. The database privileges set the
  maximum the app could ever do, even if there were a bug in the code.
- Passwords of all four accounts live in each installer's own `.env` file. Use a different password for each, and
  never commit `.env`.
- New tables get no privileges until `python manage.py grants` is run again.

## Applying and testing

```
python manage.py setup-roles    # roles and accounts (superuser password asked once)
python manage.py init-db        # tables, then database/grants.sql
python tests/access_test.py     # tries allowed and refused actions with every account
```

`access_test.py` connects as each account, tries the actions in the lists above, and reports PASS or FAIL for each.
It rolls back everything it tries. The expected final line is `All 48 access checks passed.`
