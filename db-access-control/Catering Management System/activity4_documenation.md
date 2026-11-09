# COMP 018 – Database Administration
## Activity 4: Database Users, Roles, Privileges, and Access Control

* **Group Number:** Group 7
* **Target Repository:** `catering-management-system-main`
* **Database System:** PostgreSQL 15+ / 18.x
* **Target Database:** `catering_management_db`
* **Document Version:** 1.0 (Production Release)

---

## 1. Projects Set Up Overview

| Project / Repository | Database Name | Primary Database Objects Identified | Setup Result |
| :--- | :--- | :--- | :--- |
| **catering-management-system-main** | `catering_management_db` | `customer`, `package`, `menu_item`, `employee`, `inventory`, `reservation`, `reservation_menu`, `payment`, `cancellation`, `event_assignment`, `admin` | Success |

---

## 2. Access Control Plan & Role Mapping

To enforce the Principle of Least Privilege (PoLP), database access is segregated into distinct functional layers separating administrative provisioning, backend runtime execution, compliance auditing, and inventory stock management.

| Login Account | Group Role | Application Role Served | Responsibilities | Required Privileges |
| :--- | :--- | :--- | :--- | :--- |
| `dba_admin` | *N/A* | Database Administrator | Provisioning, schema setup, role management, database maintenance | Elevated administrative access (`CREATEDB`, `CREATEROLE`) |
| `catering_app` | `app_runtime_grp` | Express.js Backend Runtime | Handling customer reservations, menu selections, inventory updates, and payment processing | `CONNECT`, `USAGE` on schema/sequences, `SELECT`, `INSERT`, `UPDATE`, `DELETE` on operational tables |
| `audit_officer` | `app_readonly_grp` | Auditor / Compliance Officer | Read-only access to customer bookings, financial records, and operational tables | `CONNECT`, `USAGE`, `SELECT` on all operational tables |
| `inventory_manager` | `data_entry_grp` | Inventory / Operations Staff | Managing catering inventory levels and stock allocations | `CONNECT`, `USAGE`, `SELECT`, `UPDATE` on `inventory` and `menu_item` tables |

---

## 3. SQL Access Control Implementation Script (`activity_4_catering_sql_script.sql`)

This production script establishes group roles, assigns secure passwords to login accounts, locks down public schema permissions, and grants table-level DML privileges.

```sql
-- =============================================================================
-- COMP 018: Activity 4 - Access Control & Role Management Script
-- Target Database: catering_management_db
-- System: Catering Management System
-- =============================================================================

-- Step 1: Clean up existing test roles if re-running
DROP ROLE IF EXISTS catering_app;
DROP ROLE IF EXISTS audit_officer;
DROP ROLE IF EXISTS inventory_manager;
DROP ROLE IF EXISTS dba_admin;

DROP ROLE IF EXISTS app_runtime_grp;
DROP ROLE IF EXISTS app_readonly_grp;
DROP ROLE IF EXISTS data_entry_grp;

-- -----------------------------------------------------------------------------
-- Step 2: Create Group Roles (NOLOGIN)
-- -----------------------------------------------------------------------------
CREATE ROLE app_runtime_grp NOLOGIN;
CREATE ROLE app_readonly_grp NOLOGIN;
CREATE ROLE data_entry_grp NOLOGIN;

-- -----------------------------------------------------------------------------
-- Step 3: Create Login Accounts
-- -----------------------------------------------------------------------------
CREATE ROLE dba_admin WITH LOGIN CREATEDB CREATEROLE PASSWORD 'SecureAdminPass2026!';
CREATE ROLE catering_app WITH LOGIN PASSWORD 'CateringAppPass2026!';
CREATE ROLE audit_officer WITH LOGIN PASSWORD 'AuditOfficerPass2026!';
CREATE ROLE inventory_manager WITH LOGIN PASSWORD 'InventoryPass2026!';

-- Step 4: Role Memberships
GRANT app_runtime_grp TO catering_app;
GRANT app_readonly_grp TO audit_officer;
GRANT data_entry_grp TO inventory_manager;

-- Step 5: Schema Privileges & Hardening
REVOKE ALL ON SCHEMA public FROM PUBLIC;
GRANT CONNECT ON DATABASE catering_management_db TO app_runtime_grp, app_readonly_grp, data_entry_grp;
GRANT USAGE ON SCHEMA public TO app_runtime_grp, app_readonly_grp, data_entry_grp;

-- Step 6: Object Privileges
-- App Runtime Privileges (Full DML for Express backend)
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO app_runtime_grp;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO app_runtime_grp;

-- Read-Only Auditor Privileges
GRANT SELECT ON ALL TABLES IN SCHEMA public TO app_readonly_grp;

-- Inventory Specialist Privileges
GRANT SELECT, UPDATE ON TABLE public.inventory, public.menu_item TO data_entry_grp;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO data_entry_grp;
```

---

## 4. Privilege Verification Results

The implemented access controls were thoroughly tested against simulated user actions to confirm proper boundary enforcement.

| Account Used | Operation Tested | SQL Statement / Test | Expected Result | Actual Result | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `catering_app` | Fetch customer records | `SELECT * FROM customer LIMIT 5;` | Allowed | Returned rows successfully | PASS |
| `catering_app` | Create new reservation | `INSERT INTO reservation (customer_id, package_id, event_date, venue, event_type, number_of_guests, status, estimated_cost) VALUES (1, 1, '2026-12-25', 'Laguna Hall', 'Wedding', 100, 'Confirmed', 45000);` | Allowed | Row inserted successfully | PASS |
| `audit_officer` | View payment records | `SELECT * FROM payment;` | Allowed | Returned all payment records | PASS |
| `audit_officer` | Delete payment record | `DELETE FROM payment WHERE payment_id = 1;` | Denied | `ERROR: permission denied for table payment` | PASS |
| `inventory_manager` | Update inventory stock | `UPDATE inventory SET quantity = 150 WHERE inventory_id = 1;` | Allowed | Row updated successfully | PASS |
| `inventory_manager` | Delete customer profile | `DELETE FROM customer WHERE customer_id = 1;` | Denied | `ERROR: permission denied for table customer` | PASS |
| `catering_app` | Create new DB | `CREATE DATABASE malicious_db;` | Denied | `ERROR: permission denied to create database` | PASS |

---

## 5. Principle of Least Privilege Justification

1. **Elimination of Superuser for Web Backend:** The Express.js backend runtime (`catering_app`) connects with explicit DML permissions (`SELECT`, `INSERT`, `UPDATE`, `DELETE`) on relevant tables without administrative credentials.
2. **Revocation of PUBLIC Schema Permissions:** PostgreSQL default privileges allow any user to create objects in the `public` schema. `REVOKE ALL ON SCHEMA public FROM PUBLIC` enforces strict schema isolation.
3. **Auditor & Operational Isolation:** The read-only auditor and inventory manager accounts are restricted to their specific operational boundaries, preventing unauthorized data modification or administrative leaks.

---

## 6. Tracker Log Entry (Activity 4)

| Column | Details / Value |
| :--- | :--- |
| **Project** | Catering Management System (`catering-management-system-main`) |
| **Database Setup Result** | Success |
| **Access-Control Folder Link** | `database/roles.sql` / `database/schema.sql` |
| **Access-Control Status** | Completed |
| **Last Updated** | 2026-11-09 |

---

## 7. AI Usage Declaration

* **AI Tools Used:** Gemini 3 Flash / Google DS Python Interpreter.
* **Tasks Performed:** Formatting SQL role templates, drafting permission validation matrix tailored to the Catering Management System schema.
* **Validation Procedure:** Executed all GRANT/REVOKE commands and verified access errors in PostgreSQL.
