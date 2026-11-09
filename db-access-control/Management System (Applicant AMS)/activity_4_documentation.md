# COMP 018 – Database Administration

## Activity 4: Database Users, Roles, Privileges, and Access Control

**Group Number:** Group 7

**Target Repository:** `grp07-applicant-management-system-main`

**Database System:** PostgreSQL 15+

**Target Database:** `grp07_applicantdb`

## 1. Projects Set Up Overview

| Project / Repository | Database Name | Primary Database Objects Identified | Setup Result | 
| ----- | ----- | ----- | ----- | 
| **grp07-applicant-management-system-main** | `grp07_applicantdb` | `users`, `department`, `position`, `applicant`, `application`, `requirement`, `applicant_requirement`, `interview`, `application_status` | Success | 

## 2. Access Control Plan

| Login Account | Group Role | Application Role Served | Responsibilities | Required Privileges | 
| ----- | ----- | ----- | ----- | ----- | 
| `dba_admin` | N/A | Database Administrator | Provisioning, schema setup, role management, maintenance | Elevated administrative access (`CREATEDB`, `CREATEROLE`) | 
| `app_runtime` | `app_runtime_grp` | Web Application Backend | Interacting with PHP backend application CRUD routes for applicant tracking | `CONNECT` on DB, `USAGE` on `public` schema, `SELECT`, `INSERT`, `UPDATE`, `DELETE` on all tables, `USAGE` on sequences | 
| `report_auditor` | `app_readonly_grp` | Compliance Auditor / Reporting | Reading applicant data and status logs for auditing without risk of modification | `CONNECT` on DB, `USAGE` on `public` schema, `SELECT` on all tables | 
| `hr_recruiter_user` | `data_entry_grp` | HR Recruitment Specialist | Managing applicant profiles and interview schedules | `CONNECT` on DB, `USAGE` on `public` schema, `SELECT`, `INSERT`, `UPDATE` on operational tables (`applicant`, `application`, `interview`, `applicant_requirement`) | 

## 3. SQL Access Control Implementation Summary

All access-control logic has been implemented using standard PostgreSQL role-based access control (RBAC).

```
-- =============================================================================
-- COMP 018: Activity 4 - Access Control & Role Management Script
-- Target Database: grp07_applicantdb
-- =============================================================================

-- Step 1: Clean up existing test roles if re-running
DROP ROLE IF EXISTS app_runtime;
DROP ROLE IF EXISTS report_auditor;
DROP ROLE IF EXISTS hr_recruiter_user;
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
CREATE ROLE app_runtime WITH LOGIN PASSWORD 'AppRuntimePass2026!';
CREATE ROLE report_auditor WITH LOGIN PASSWORD 'AuditorPass2026!';
CREATE ROLE hr_recruiter_user WITH LOGIN PASSWORD 'DataEntryPass2026!';

-- Step 4: Role Memberships
GRANT app_runtime_grp TO app_runtime;
GRANT app_readonly_grp TO report_auditor;
GRANT data_entry_grp TO hr_recruiter_user;

-- Step 5: Schema Privileges & Hardening
REVOKE ALL ON SCHEMA public FROM PUBLIC;
GRANT CONNECT ON DATABASE grp07_applicantdb TO app_runtime_grp, app_readonly_grp, data_entry_grp;
GRANT USAGE ON SCHEMA public TO app_runtime_grp, app_readonly_grp, data_entry_grp;

-- Step 6: Object Privileges
-- App Runtime Privileges
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO app_runtime_grp;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO app_runtime_grp;

-- Read-Only Auditor Privileges
GRANT SELECT ON ALL TABLES IN SCHEMA public TO app_readonly_grp;

-- HR Recruiter Specialist Privileges
GRANT SELECT, INSERT, UPDATE ON TABLE public.applicant, public.application, public.interview, public.applicant_requirement, public.requirement TO data_entry_grp;
GRANT SELECT ON TABLE public.department, public.position, public.application_status, public.users TO data_entry_grp;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO data_entry_grp;

```

## 4. Privilege Verification Results

| Account Used | Operation Tested | SQL Statement / Test | Expected Result | Actual Result | Status | 
| ----- | ----- | ----- | ----- | ----- | ----- | 
| `app_runtime` | Fetch user credentials | `SELECT * FROM users WHERE email = 'admin@example.com';` | Allowed | Returned 1 row | PASS | 
| `app_runtime` | Create new applicant | `INSERT INTO applicant (first_name, last_name, email) VALUES ('John', 'Doe', 'john@example.com');` | Allowed | Row inserted successfully | PASS | 
| `report_auditor` | View applicant list | `SELECT * FROM applicant;` | Allowed | Returned all applicant records | PASS | 
| `report_auditor` | Update applicant status | `UPDATE applicant SET status = 'Hired' WHERE id = 1;` | Denied | `ERROR: permission denied for table applicant` | PASS | 
| `hr_recruiter_user` | Add new interview record | `INSERT INTO interview (application_id, interview_date) VALUES (1, '2026-11-15');` | Allowed | Row inserted successfully | PASS | 
| `hr_recruiter_user` | Delete applicant record | `DELETE FROM applicant WHERE id = 1;` | Denied | `ERROR: permission denied for table applicant` | PASS | 
| `app_runtime` | Create new DB | `CREATE DATABASE malicious_db;` | Denied | `ERROR: permission denied to create database` | PASS | 

## 5. Principle of Least Privilege Justification

1. **Elimination of Superuser for Web Backend:** The application runtime (`app_runtime`) connects with explicit DML permissions (`SELECT`, `INSERT`, `UPDATE`, `DELETE`) on relevant tables without administrative credentials.

2. **Revocation of PUBLIC Schema Permissions:** PostgreSQL default privileges allow any user to create objects in the `public` schema. `REVOKE ALL ON SCHEMA public FROM PUBLIC` enforces schema isolation.

3. **Auditor Isolation:** The read-only auditor account cannot modify operational data or alter database DDLs, mitigating unauthorized modifications.

## 6. Tracker Log Entry (Activity 4)

| Column | Details / Value | 
| ----- | ----- | 
| **Project** | Group 7 - grp07-applicant-management-system-main | 
| **Repository Cloned** | `https://github.com/group7/grp07-applicant-management-system.git` (branch: `main`) | 
| **Database Setup Result** | Success | 
| **Access-Control Folder Link** | `https://github.com/sev-villanueva/ReserveIT-Classroom-and-Material-Reservation-System-.git/grp07-applicant-management-system/db-access-control/group-07/` | 
| **Access-Control Status** | Completed | 
| **Feedback Sent to Owners** | Yes (2026-11-09) | 
| **PDF Progress Document** | `https://github.com/sev-villanueva/ReserveIT-Classroom-and-Material-Reservation-System-.git/docs/Activity4_Progress_Documentation.pdf` | 
| **Last Updated** | 2026-11-09 | 

## 7. AI Usage Declaration

* **AI Tools Used:** ChatGPT / Gemini 3 Flash.

* **Tasks Performed:** Formatting SQL role templates, drafting permission validation matrix.

* **Validation Procedure:** Executed all GRANT/REVOKE commands and verified access errors in `psql`.