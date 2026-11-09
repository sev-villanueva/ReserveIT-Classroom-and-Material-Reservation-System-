# COMP 018 – Database Administration

## Activity 4: Database Users, Roles, Privileges, and Access Control

**Group Number:** Group 9

**Target Repository:** `Batumbakal-Gym-main`

**Database System:** PostgreSQL 15+ / 18.x

**Target Database:** `batumbakal_gym_db`

## 1. Projects Set Up Overview

| Project / Repository | Database Name | Primary Database Objects Identified | Setup Result | 
| ----- | ----- | ----- | ----- | 
| **Batumbakal-Gym-main** | `batumbakal_gym_db` | `trainers`, `members`, `membership_plans`, `memberships`, `payments`, `classes`, `class_enrollments`, `attendance` | Success | 

## 2. Access Control Plan

| Login Account | Group Role | Application Role Served | Responsibilities | Required Privileges | 
| ----- | ----- | ----- | ----- | ----- | 
| `dba_admin` | N/A | Database Administrator | Provisioning, schema setup, role management, maintenance | Elevated administrative access (`CREATEDB`, `CREATEROLE`) | 
| `gym_app_user` | `app_runtime_grp` | Spring Boot Backend Runtime | Interacting with backend Spring Data JPA routes (`/api/members`, `/api/payments`, `/api/attendance`) | `CONNECT` on DB, `USAGE` on `public` schema, `SELECT`, `INSERT`, `UPDATE`, `DELETE` on all tables, `USAGE` on sequences | 
| `audit_officer` | `app_readonly_grp` | Compliance Auditor / Reporting | Reading data for auditing and generating gym membership/financial metrics without risk of modification | `CONNECT` on DB, `USAGE` on `public` schema, `SELECT` on all tables | 
| `frontdesk_staff` | `data_entry_grp` | Front Desk / Gym Staff | Managing member attendance check-ins, daily gym class enrollments, and viewing member details | `CONNECT` on DB, `USAGE` on `public` schema, `SELECT`, `INSERT`, `UPDATE` on `attendance`, `class_enrollments`, and `members` tables | 

## 3. SQL Access Control Implementation Summary

All access-control logic has been implemented using standard PostgreSQL role-based access control (RBAC).

```
-- =============================================================================
-- COMP 018: Activity 4 - Access Control & Role Management Script
-- Target Database: batumbakal_gym_db
-- =============================================================================

-- Step 1: Clean up existing test roles if re-running
DROP ROLE IF EXISTS gym_app_user;
DROP ROLE IF EXISTS audit_officer;
DROP ROLE IF EXISTS frontdesk_staff;
DROP ROLE IF EXISTS dba_admin;
DROP ROLE IF EXISTS app_runtime_grp;
DROP ROLE IF EXISTS app_readonly_grp;
DROP ROLE IF EXISTS data_entry_grp;

-- Step 2: Create Group Roles (NOLOGIN)
CREATE ROLE app_runtime_grp NOLOGIN;
CREATE ROLE app_readonly_grp NOLOGIN;
CREATE ROLE data_entry_grp NOLOGIN;

-- Step 3: Create Login Accounts
CREATE ROLE dba_admin WITH LOGIN CREATEDB CREATEROLE PASSWORD 'SecureAdminPass2026!';
CREATE ROLE gym_app_user WITH LOGIN PASSWORD 'GymAppPass2026!';
CREATE ROLE audit_officer WITH LOGIN PASSWORD 'AuditorPass2026!';
CREATE ROLE frontdesk_staff WITH LOGIN PASSWORD 'DataEntryPass2026!';

-- Step 4: Role Memberships
GRANT app_runtime_grp TO gym_app_user;
GRANT app_readonly_grp TO audit_officer;
GRANT data_entry_grp TO frontdesk_staff;

-- Step 5: Schema Privileges & Hardening
REVOKE ALL ON SCHEMA public FROM PUBLIC;
GRANT CONNECT ON DATABASE batumbakal_gym_db TO app_runtime_grp, app_readonly_grp, data_entry_grp;
GRANT USAGE ON SCHEMA public TO app_runtime_grp, app_readonly_grp, data_entry_grp;

-- Step 6: Object Privileges
-- App Runtime Privileges (Spring Boot backend)
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO app_runtime_grp;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO app_runtime_grp;

-- Read-Only Auditor Privileges
GRANT SELECT ON ALL TABLES IN SCHEMA public TO app_readonly_grp;

-- Front Desk Staff Privileges
GRANT SELECT, INSERT, UPDATE ON TABLE public.members, public.attendance, public.class_enrollments TO data_entry_grp;
GRANT SELECT ON TABLE public.trainers, public.membership_plans, public.memberships, public.payments, public.classes TO data_entry_grp;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO data_entry_grp;

```

## 4. Privilege Verification Results

| Account Used | Operation Tested | SQL Statement / Test | Expected Result | Actual Result | Status | 
| ----- | ----- | ----- | ----- | ----- | ----- | 
| `gym_app_user` | Fetch member records | `SELECT * FROM members LIMIT 5;` | Allowed | Returned rows successfully | PASS | 
| `gym_app_user` | Insert new attendance log | `INSERT INTO attendance (member_id) VALUES (1);` | Allowed | Row inserted successfully | PASS | 
| `audit_officer` | View payment records | `SELECT * FROM payments;` | Allowed | Returned all payment records | PASS | 
| `audit_officer` | Delete payment record | `DELETE FROM payments WHERE payment_id = 1;` | Denied | `ERROR: permission denied for table payments` | PASS | 
| `frontdesk_staff` | Insert attendance check-in | `INSERT INTO attendance (member_id) VALUES (2);` | Allowed | Row inserted successfully | PASS | 
| `frontdesk_staff` | Delete member profile | `DELETE FROM members WHERE member_id = 1;` | Denied | `ERROR: permission denied for table members` | PASS | 
| `gym_app_user` | Create new DB | `CREATE DATABASE malicious_db;` | Denied | `ERROR: permission denied to create database` | PASS | 

## 5. Principle of Least Privilege Justification

1. **Elimination of Superuser for Spring Boot Backend:** The application runtime (`gym_app_user`) connects with explicit DML permissions (`SELECT`, `INSERT`, `UPDATE`, `DELETE`) on relevant tables without administrative credentials.

2. **Revocation of PUBLIC Schema Permissions:** PostgreSQL default privileges allow any user to create objects in the `public` schema. `REVOKE ALL ON SCHEMA public FROM PUBLIC` enforces schema isolation.

3. **Auditor & Front Desk Operational Isolation:** The read-only auditor and front desk staff accounts are restricted to their specific operational boundaries, preventing unauthorized data modification or administrative leaks.

## 6. Tracker Log Entry (Activity 4)

| Column | Details / Value | 
| ----- | ----- | 
| **Project** | Batumbakal Gym Management System (`Batumbakal-Gym-main`) | 
| **Repository Cloned** | `https://github.com/sev-villanueva/Batumbakal-Gym-main.git` (branch: `main`) | 
| **Database Setup Result** | Success | 
| **Access-Control Folder Link** | `https://github.com/sev-villanueva/Batumbakal-Gym-main/tree/main/database` | 
| **Access-Control Status** | Completed | 
| **Feedback Sent to Owners** | Yes (2026-11-09) | 
| **PDF Progress Document** | `https://github.com/sev-villanueva/Batumbakal-Gym-main/blob/main/docs/ACTIVITY3_PROGRESS_REPORT_DRAFT.pdf` | 
| **Last Updated** | 2026-11-09 | 

## 7. AI Usage Declaration

* **AI Tools Used:** Gemini 3 Flash / Google DS Python Interpreter.

* **Tasks Performed:** Formatting SQL role templates, drafting permission validation matrix.

* **Validation Procedure:** Executed all GRANT/REVOKE commands and verified access errors in `psql`.