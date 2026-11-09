# COMP 018 – Database Administration

## Activity 4: Database Users, Roles, Privileges, and Access Control

**Group Number:** Group 3

**Target Repository:** `GRP03_PROJECTDB-main`

**Database System:** PostgreSQL 16+

**Target Database:** `healthbridge_db`

## 1. Projects Set Up Overview

| Project / Repository | Database Name | Primary Database Objects Identified | Setup Result | 
| ----- | ----- | ----- | ----- | 
| **GRP03_PROJECTDB-main** | `healthbridge_db` | `users`, `patients`, `doctors`, `appointments`, `billing`, `visit_notes`, `audit_logs` | Success | 

## 2. Access Control Plan

| Login Account | Group Role | Application Role Served | Responsibilities | Required Privileges | 
| ----- | ----- | ----- | ----- | ----- | 
| `hbcms_dba` | N/A | Database Administrator | Provisioning, schema setup, role management, maintenance | Elevated administrative access (`CREATEDB`, `CREATEROLE`) | 
| `hbcms_app_user` | `hbcms_app_grp` | Web Application Backend | Interacting with backend clinical routes (`/appointments`, `/billing`, `/visit_notes`) | `CONNECT` on DB, `USAGE` on `public` schema, `SELECT`, `INSERT`, `UPDATE`, `DELETE` on all tables, `USAGE` on sequences | 
| `hbcms_auditor` | `hbcms_readonly_grp` | Compliance Auditor / Reporting | Reading data for auditing and generating clinic metrics without risk of modification | `CONNECT` on DB, `USAGE` on `public` schema, `SELECT` on all tables | 
| `hbcms_staff` | `hbcms_dataentry_grp` | Data Entry Specialist | Registering new patient records and managing appointment queues | `CONNECT` on DB, `USAGE` on `public` schema, `SELECT`, `INSERT` on `patients` and `appointments` tables | 

## 3. SQL Access Control Implementation Summary

All access-control logic has been implemented using standard PostgreSQL role-based access control (RBAC).

```sql
-- 1. Create NOLOGIN Group Roles
CREATE ROLE hbcms_app_grp NOLOGIN;
CREATE ROLE hbcms_readonly_grp NOLOGIN;
CREATE ROLE hbcms_dataentry_grp NOLOGIN;

-- 2. Create LOGIN Accounts with Secure Passwords
CREATE ROLE hbcms_dba WITH LOGIN CREATEDB CREATEROLE PASSWORD 'HBCMSAdmin2026!';
CREATE ROLE hbcms_app_user WITH LOGIN PASSWORD 'HBCMSAppPass2026!';
CREATE ROLE hbcms_auditor WITH LOGIN PASSWORD 'HBCMSAuditor2026!';
CREATE ROLE hbcms_staff WITH LOGIN PASSWORD 'HBCMSStaffPass2026!';

-- 3. Assign Role Memberships
GRANT hbcms_app_grp TO hbcms_app_user;
GRANT hbcms_readonly_grp TO hbcms_auditor;
GRANT hbcms_dataentry_grp TO hbcms_staff;

-- 4. Restrict Default Public Schema Privileges
REVOKE ALL ON SCHEMA public FROM PUBLIC;

-- 5. Grant Explicit Privileges to Group Roles
GRANT CONNECT ON DATABASE healthbridge_db TO hbcms_app_grp, hbcms_readonly_grp, hbcms_dataentry_grp;
GRANT USAGE ON SCHEMA public TO hbcms_app_grp, hbcms_readonly_grp, hbcms_dataentry_grp;

-- App Runtime Group
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO hbcms_app_grp;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO hbcms_app_grp;

-- Read-Only Auditor Group
GRANT SELECT ON ALL TABLES IN SCHEMA public TO hbcms_readonly_grp;

-- Data Entry Group
GRANT SELECT, INSERT ON TABLE public.patients, public.appointments TO hbcms_dataentry_grp;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO hbcms_dataentry_grp;
```

## 4. Privilege Verification Results

| Account Used | Operation Tested | SQL Statement / Test | Expected Result | Actual Result | Status | 
| ----- | ----- | ----- | ----- | ----- | ----- | 
| `hbcms_app_user` | Fetch patient records | `SELECT * FROM patients WHERE email = 'patient@example.com';` | Allowed | Returned 1 row | PASS | 
| `hbcms_app_user` | Create new appointment | `INSERT INTO appointments (patient_id, doctor_id, appointment_date) VALUES (1, 1, NOW());` | Allowed | Row inserted successfully | PASS | 
| `hbcms_auditor` | View billing logs | `SELECT * FROM billing;` | Allowed | Returned all billing records | PASS | 
| `hbcms_auditor` | Update billing record | `UPDATE billing SET status = 'Paid' WHERE id = 1;` | Denied | `ERROR: permission denied for table billing` | PASS | 
| `hbcms_staff` | Add new patient profile | `INSERT INTO patients (name, phone) VALUES ('Jane Smith', '555-0144');` | Allowed | Row inserted successfully | PASS | 
| `hbcms_staff` | Delete patient record | `DELETE FROM patients WHERE id = 1;` | Denied | `ERROR: permission denied for table patients` | PASS | 
| `hbcms_app_user` | Create new DB | `CREATE DATABASE malicious_db;` | Denied | `ERROR: permission denied to create database` | PASS | 

## 5. Principle of Least Privilege Justification

1. **Elimination of Superuser for Web Backend:** The application runtime (`hbcms_app_user`) connects with explicit DML permissions (`SELECT`, `INSERT`, `UPDATE`, `DELETE`) on relevant tables without administrative credentials.

2. **Revocation of PUBLIC Schema Permissions:** PostgreSQL default privileges allow any user to create objects in the `public` schema. `REVOKE ALL ON SCHEMA public FROM PUBLIC` enforces schema isolation.

3. **Auditor Isolation:** The read-only auditor account cannot modify operational data or alter database DDLs, mitigating unauthorized modifications.

## 6. Tracker Log Entry (Activity 4)

| Column | Details / Value | 
| ----- | ----- | 
| **Project** | Group 3 - GRP03_PROJECTDB-main | 
| **Repository Cloned** | `GRP03_PROJECTDB-main` (branch: `main`) | 
| **Database Setup Result** | Success | 
| **Access-Control Folder Link** | `db-access-control/group-03/` | 
| **Access-Control Status** | Completed | 
| **Feedback Sent to Owners** | Yes (2026-11-09) | 
| **PDF Progress Document** | `docs/Activity4_Progress_Documentation.pdf` | 
| **Last Updated** | 2026-11-09 | 

## 7. AI Usage Declaration

* **AI Tools Used:** ChatGPT / Gemini 3 Flash.
* **Tasks Performed:** Formatting SQL role templates, drafting permission validation matrix.
* **Validation Procedure:** Executed all GRANT/REVOKE commands and verified access errors in `psql`.