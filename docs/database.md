# Database documentation: `grp01_appdb`

PostgreSQL 16+ (designed for 18), schema `public`, owner `postgres`. Created by `database/schema.sql`.
This implements the approved Activity 2 design: 8 tables, 5 one-to-many relationships, and 1 many-to-many
relationship resolved by `reservation_material`.

## Relationships

| Relationship | Type | Foreign key |
|---|---|---|
| department to app_user | 1:N | `app_user.department_id` |
| app_user to reservation | 1:N | `reservation.user_id` |
| room to reservation | 1:N | `reservation.room_id` |
| staff to reservation (reviewer) | 1:N | `reservation.staff_id` (null until reviewed) |
| reservation to penalty | 1:1 (at most one) | `penalty.reservation_id` (UNIQUE) |
| reservation to material | M:N | `reservation_material` (composite PK of both keys) |

## Tables

**department**: `department_id` PK, `department_name` UNIQUE NOT NULL.

**app_user** (requesters): `user_id` PK, `first_name`, `last_name`, `email` UNIQUE (stored lowercase),
`password_hash`, `role` (STUDENT or FACULTY), `department_id` FK NOT NULL, `status` (ACTIVE or SUSPENDED, default ACTIVE).

**staff**: `staff_id` PK, `full_name`, `email` UNIQUE (lowercase), `password_hash`, `role` (STAFF or ADMIN),
`status` (ACTIVE or INACTIVE, default ACTIVE).

**room**: `room_id` PK, `room_name`, `building`, `capacity` (> 0), `room_type` (CLASSROOM, LABORATORY, CONFERENCE),
`status` (AVAILABLE or UNDER_MAINTENANCE, default AVAILABLE). UNIQUE (`building`, `room_name`).

**material**: `material_id` PK, `material_name` UNIQUE, `category` (AV_EQUIPMENT, FURNITURE, SUPPLIES),
`total_quantity` (>= 0), `available_quantity` (between 0 and `total_quantity`).

**reservation**: `reservation_id` PK, `user_id` FK, `room_id` FK, `staff_id` FK (nullable), `reservation_date`,
`start_time`, `end_time`, `purpose`, `status` (PENDING, APPROVED, REJECTED, CANCELLED, COMPLETED; default PENDING).

**reservation_material**: PK (`reservation_id`, `material_id`), `quantity_requested` (> 0).
Deleting a reservation removes its line items (ON DELETE CASCADE).

**penalty**: `penalty_id` PK, `reservation_id` FK UNIQUE, `reason` (NO_SHOW, DAMAGED_MATERIAL, LATE_RETURN),
`amount` (>= 0), `issue_date` (default today), `paid_status` (UNPAID or PAID, default UNPAID), `paid_date`.

## Constraints that enforce business rules

| Business rule (Activity 2, Part 4) | Enforced by |
|---|---|
| 1. One department per user, unique email | `app_user.department_id` NOT NULL FK; `UNIQUE (email)` |
| 3. Approved reservations for one room cannot overlap | `EXCLUDE USING gist` constraint `no_overlapping_approved_reservations` on (`room_id`, time range), only for rows with status APPROVED |
| 4. Reviewed before approved or rejected | `CHECK (status IN ('PENDING','CANCELLED') OR staff_id IS NOT NULL)` |
| 5. Zero or more materials per reservation | `reservation_material` (M:N) |
| 6. Requested quantity cannot exceed available | `CHECK (available_quantity BETWEEN 0 AND total_quantity)` as the last line of defense, plus application checks at request and approval |
| 7. One penalty per reservation | `UNIQUE (penalty.reservation_id)` |
| 8. Unpaid penalties above a limit block new requests | Application layer (`PENALTY_THRESHOLD`) |
| 9. End after start; no past dates | `CHECK (end_time > start_time)`; past-date check in the application |
| 10. Only active staff approve | Application layer (login blocks INACTIVE staff; approval re-checks status) |

The overlap exclusion constraint uses the `btree_gist` extension, which `schema.sql` enables.

## How stock counts stay correct

`material.available_quantity` is a maintained counter. Requests do not hold stock. The counter changes only inside one
transaction, with the material rows locked:

- Approve: subtract the requested units (fails if there are not enough).
- Cancel an approved reservation, or mark it completed: add the units back.
- Edit a material's total: available shifts by the same amount; the edit is refused if it would go below zero.

## Changes from the Activity 2 draft

| Change | Reason |
|---|---|
| Table `user` is named `app_user` | `user` is a reserved word in PostgreSQL and would need quotes everywhere |
| Added `password_hash` to `app_user` and `staff` | Feature 10 (login and role-based access) needs somewhere to store credentials; only salted hashes are stored |
| Email columns must be lowercase (CHECK) | Prevents the same address registering twice with different capitals |
| Added the overlap exclusion constraint | Business rule 3 is now enforced by the database, not only the application |
| Added reviewer CHECK on `reservation` | Enforces business rule 4 in the database |
| `UNIQUE (building, room_name)` on `room`; `UNIQUE (material_name)` on `material` | Prevents accidental duplicate catalog entries |
| `paid_status` and `paid_date` must agree (CHECK) | A penalty is PAID exactly when it has a paid date |
| Added index on `reservation.user_id` | Speeds up "my reservations" |

The ERD, data dictionary, and Part 4 "Design Impact" notes in the Activity 2 report should be updated to match.

## Indexes

`idx_reservation_room`, `idx_reservation_date`, `idx_reservation_status`, `idx_reservation_user`, plus the indexes
PostgreSQL creates automatically for primary keys, UNIQUE constraints, and the exclusion constraint.

## Backup and restore

```
pg_dump -U postgres -F c -f reserveit_backup.dump grp01_appdb
pg_restore -U postgres -d grp01_appdb --clean --if-exists reserveit_backup.dump
```
