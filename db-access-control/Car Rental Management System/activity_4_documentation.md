# COMP 018 – Database Administration

## Activity 4: Database Users, Roles, Privileges, and Access Control

**Group Number:** Group 06

**Target Repository:** `Car_Rental_Management_System-main`

**Database System:** PostgreSQL 15+

**Target Database:** `car_rental_db`

## 1. Projects Set Up Overview

| Project / Repository | Database Name | Primary Database Objects Identified | Setup Result | 
| ----- | ----- | ----- | ----- | 
| **Car_Rental_Management_System-main** | `car_rental_db` | `customers`, `vehicles`, `rentals`, `payments`, `driver_license`, `maintenance_logs`, `staff` | Success | 

## 2. Access Control Plan

| Login Account | Group Role | Application Role Served | Responsibilities | Required Privileges | 
| ----- | ----- | ----- | ----- | ----- | 
| `dba_admin` | N/A | Database Administrator | Provisioning, schema setup, role management, maintenance | Elevated administrative access (`CREATEDB`, `CREATEROLE`) | 
| `app_runtime` | `app_runtime_grp` | Web Application Backend | Interacting with backend Express/Spring routes (`/vehicles`, `/rentals`, `/customers`) | `CONNECT` on DB, `USAGE` on `public` schema, `SELECT`, `INSERT`, `UPDATE`, `DELETE` on all tables, `USAGE` on sequences | 
| `report_auditor` | `app_readonly_grp` | Compliance Auditor / Reporting | Reading operational data for analytics and auditing without modification risks | `CONNECT` on DB, `USAGE` on `public` schema, `SELECT` on all tables | 
| `agent_entry_user` | `data_entry_grp` | Rental Booking Agent | Registering new customers and creating new vehicle rental bookings | `CONNECT` on DB, `USAGE` on `public` schema, `SELECT`, `INSERT` on `customers` and `rentals` tables | 

## 3. SQL Access Control Implementation Summary

All access-control logic has been implemented using standard PostgreSQL role-based access control (RBAC).

```sql
-- 1. Create NOLOGIN Group Roles
CREATE ROLE app_runtime_grp NOLOGIN;
CREATE ROLE app_readonly_grp NOLOGIN;
CREATE ROLE data_entry_grp NOLOGIN;

-- 2. Create LOGIN Accounts with Secure Passwords
CREATE ROLE dba_admin WITH LOGIN CREATEDB CREATEROLE PASSWORD 'SecureAdminPass2026!';
CREATE ROLE app_runtime WITH LOGIN PASSWORD 'AppRuntimePass2026!';
CREATE ROLE report_auditor WITH LOGIN PASSWORD 'AuditorPass2026!';
CREATE ROLE agent_entry_user WITH LOGIN PASSWORD 'DataEntryPass2026!';

-- 3. Assign Role Memberships
GRANT app_runtime_grp TO app_runtime;
GRANT app_readonly_grp TO report_auditor;
GRANT data_entry_grp TO agent_entry_user;

-- 4. Restrict Default Public Schema Privileges
REVOKE ALL ON SCHEMA public FROM PUBLIC;

-- 5. Grant Explicit Privileges to Group Roles
GRANT CONNECT ON DATABASE car_rental_db TO app_runtime_grp, app_readonly_grp, data_entry_grp;
GRANT USAGE ON SCHEMA public TO app_runtime_grp, app_readonly_grp, data_entry_grp;

-- App Runtime Group
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO app_runtime_grp;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO app_runtime_grp;

-- Read-Only Auditor Group
GRANT SELECT ON ALL TABLES IN SCHEMA public TO app_readonly_grp;

-- Data Entry Group
GRANT SELECT, INSERT ON TABLE public.customers, public.rentals TO data_entry_grp;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO data_entry_grp;
```

## 4. Privilege Verification Results

| Account Used | Operation Tested | SQL Statement / Test | Expected Result | Actual Result | Status | 
| ----- | ----- | ----- | ----- | ----- | ----- | 
| `app_runtime` | Fetch vehicle data | `SELECT * FROM vehicles WHERE status = 'available';` | Allowed | Returned 5 rows | PASS | 
| `app_runtime` | Create new rental booking | `INSERT INTO rentals (customer_id, vehicle_id, start_date) VALUES (1, 3, '2026-11-10');` | Allowed | Row inserted successfully | PASS | 
| `report_auditor` | View rental list | `SELECT * FROM rentals;` | Allowed | Returned all rental records | PASS | 
| `report_auditor` | Update rental status | `UPDATE rentals SET status = 'Completed' WHERE id = 1;` | Denied | `ERROR: permission denied for table rentals` | PASS | 
| `agent_entry_user` | Add new customer profile | `INSERT INTO customers (name, email) VALUES ('John Smith', 'john@example.com');` | Allowed | Row inserted successfully | PASS | 
| `agent_entry_user` | Delete customer profile | `DELETE FROM customers WHERE id = 1;` | Denied | `ERROR: permission denied for table customers` | PASS | 
| `app_runtime` | Create new DB | `CREATE DATABASE malicious_db;` | Denied | `ERROR: permission denied to create database` | PASS | 

## 5. Principle of Least Privilege Justification

1. **Elimination of Superuser for Web Backend:** The application runtime (`app_runtime`) connects with explicit DML permissions (`SELECT`, `INSERT`, `UPDATE`, `DELETE`) on relevant tables without administrative credentials.

2. **Revocation of PUBLIC Schema Permissions:** PostgreSQL default privileges allow any user to create objects in the `public` schema. `REVOKE ALL ON SCHEMA public FROM PUBLIC` enforces schema isolation.

3. **Auditor Isolation:** The read-only auditor account cannot modify operational data or alter database DDLs, mitigating unauthorized modifications.

## 6. Tracker Log Entry (Activity 4)

| Column | Details / Value | 
| ----- | ----- | 
| **Project** | Group 06 - Car_Rental_Management_System-main | 
| **Repository Cloned** | `https://github.com/sev-villanueva/Car_Rental_Management_System-main.git` (branch: `main`) | 
| **Database Setup Result** | Success | 
| **Access-Control Folder Link** | `https://github.com/sev-villanueva/Car_Rental_Management_System-main/db-access-control/group-06/` | 
| **Access-Control Status** | Completed | 
| **Feedback Sent to Owners** | Yes (2026-11-09) | 
| **PDF Progress Document** | `https://github.com/sev-villanueva/Car_Rental_Management_System-main/docs/Activity4_Progress_Documentation.pdf` | 
| **Last Updated** | 2026-11-09 | 

## 7. AI Usage Declaration

* **AI Tools Used:** ChatGPT / Gemini 3 Flash.

* **Tasks Performed:** Formatting SQL role templates, drafting permission validation matrix.

* **Validation Procedure:** Executed all GRANT/REVOKE commands and verified access errors in `psql`.
