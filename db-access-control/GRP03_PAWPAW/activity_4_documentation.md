# COMP 018 – Database Administration

## Activity 4: Database Users, Roles, Privileges, and Access Control

**Group Number:** Group 3

**Target Repository:** `group3_Pawpaw`

**Database System:** PostgreSQL 16+

**Target Database:** `pawpaw_db`

## 1. Projects Set Up Overview

| Project / Repository | Database Name | Primary Database Objects Identified | Setup Result | 
| ----- | ----- | ----- | ----- | 
| **group3_Pawpaw** | `pawpaw_db` | `clients`, `patients`, `veterinarians`, `appointments`, `medical_records`, `inventory`, `invoices`, `audit_logs` | Success | 

## 2. Access Control Plan

| Login Account | Group Role | Application Role Served | Responsibilities | Required Privileges | 
| ----- | ----- | ----- | ----- | ----- | 
| `pawpaw_dba` | N/A | Database Administrator | Provisioning, schema setup, role management, maintenance | Elevated administrative access (`CREATEDB`, `CREATEROLE`) | 
| `pawpaw_app_user` | `pawpaw_app_grp` | Web Application Backend | Interacting with backend clinic routes (`/clients`, `/patients`, `/appointments`, `/invoices`) | `CONNECT` on DB, `USAGE` on `public` schema, `SELECT`, `INSERT`, `UPDATE`, `DELETE` on all tables, `USAGE` on sequences | 
| `pawpaw_auditor` | `pawpaw_readonly_grp` | Compliance Auditor / Reporting | Reading data for auditing and generating clinic metrics without risk of modification | `CONNECT` on DB, `USAGE` on `public` schema, `SELECT` on all tables | 
| `pawpaw_staff` | `pawpaw_dataentry_grp` | Data Entry Specialist | Registering new walk-in clients and scheduling patient appointments | `CONNECT` on DB, `USAGE` on `public` schema, `SELECT`, `INSERT` on `clients`, `patients`, and `appointments` tables | 

## 3. SQL Access Control Implementation Summary

All access-control logic has been implemented using standard PostgreSQL role-based access control (RBAC).

```sql
-- 1. Create NOLOGIN Group Roles
CREATE ROLE pawpaw_app_grp NOLOGIN;
CREATE ROLE pawpaw_readonly_grp NOLOGIN;
CREATE ROLE pawpaw_dataentry_grp NOLOGIN;

-- 2. Create LOGIN Accounts with Secure Passwords
CREATE ROLE pawpaw_dba WITH LOGIN CREATEDB CREATEROLE PASSWORD 'PawpawAdmin2026!';
CREATE ROLE pawpaw_app_user WITH LOGIN PASSWORD 'PawpawAppPass2026!';
CREATE ROLE pawpaw_auditor WITH LOGIN PASSWORD 'PawpawAuditor2026!';
CREATE ROLE pawpaw_staff WITH LOGIN PASSWORD 'PawpawStaffPass2026!';

-- 3. Assign Role Memberships
GRANT pawpaw_app_grp TO pawpaw_app_user;
GRANT pawpaw_readonly_grp TO pawpaw_auditor;
GRANT pawpaw_dataentry_grp TO pawpaw_staff;

-- 4. Restrict Default Public Schema Privileges
REVOKE ALL ON SCHEMA public FROM PUBLIC;

-- 5. Grant Explicit Privileges to Group Roles
GRANT CONNECT ON DATABASE pawpaw_db TO pawpaw_app_grp, pawpaw_readonly_grp, pawpaw_dataentry_grp;
GRANT USAGE ON SCHEMA public TO pawpaw_app_grp, pawpaw_readonly_grp, pawpaw_dataentry_grp;

-- App Runtime Group
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO pawpaw_app_grp;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO pawpaw_app_grp;

-- Read-Only Auditor Group
GRANT SELECT ON ALL TABLES IN SCHEMA public TO pawpaw_readonly_grp;

-- Data Entry Group
GRANT SELECT, INSERT ON TABLE public.clients, public.patients, public.appointments TO pawpaw_dataentry_grp;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO pawpaw_dataentry_grp;
```

## 4. Privilege Verification Results

| Account Used | Operation Tested | SQL Statement / Test | Expected Result | Actual Result | Status | 
| ----- | ----- | ----- | ----- | ----- | ----- | 
| `pawpaw_app_user` | Fetch client records | `SELECT * FROM clients WHERE email = 'client@example.com';` | Allowed | Returned 1 row | PASS | 
| `pawpaw_app_user` | Create new appointment | `INSERT INTO appointments (client_id, patient_id, appointment_date) VALUES (1, 1, NOW());` | Allowed | Row inserted successfully | PASS | 
| `pawpaw_auditor` | View medical records | `SELECT * FROM medical_records;` | Allowed | Returned all medical records | PASS | 
| `pawpaw_auditor` | Update medical record | `UPDATE medical_records SET diagnosis = 'Updated' WHERE id = 1;` | Denied | `ERROR: permission denied for table medical_records` | PASS | 
| `pawpaw_staff` | Add new client profile | `INSERT INTO clients (name, phone) VALUES ('John Doe', '555-0199');` | Allowed | Row inserted successfully | PASS | 
| `pawpaw_staff` | Delete client profile | `DELETE FROM clients WHERE id = 1;` | Denied | `ERROR: permission denied for table clients` | PASS | 
| `pawpaw_app_user` | Create new DB | `CREATE DATABASE malicious_db;` | Denied | `ERROR: permission denied to create database` | PASS | 

## 5. Principle of Least Privilege Justification

1. **Elimination of Superuser for Web Backend:** The application runtime (`pawpaw_app_user`) connects with explicit DML permissions (`SELECT`, `INSERT`, `UPDATE`, `DELETE`) on relevant tables without administrative credentials.

2. **Revocation of PUBLIC Schema Permissions:** PostgreSQL default privileges allow any user to create objects in the `public` schema. `REVOKE ALL ON SCHEMA public FROM PUBLIC` enforces schema isolation.

3. **Auditor Isolation:** The read-only auditor account cannot modify operational data or alter database DDLs, mitigating unauthorized modifications.

## 6. Tracker Log Entry (Activity 4)

| Column | Details / Value | 
| ----- | ----- | 
| **Project** | Group 3 - group3_Pawpaw | 
| **Repository Cloned** | `https://github.com/sev-villanueva/group3_Pawpaw.git` (branch: `main`) | 
| **Database Setup Result** | Success | 
| **Access-Control Folder Link** | `https://github.com/sev-villanueva/group3_Pawpaw/tree/main/db-access-control/group-03/` | 
| **Access-Control Status** | Completed | 
| **Feedback Sent to Owners** | Yes (2026-11-09) | 
| **PDF Progress Document** | `https://github.com/sev-villanueva/group3_Pawpaw/tree/main/docs/Activity4_Progress_Documentation.pdf` | 
| **Last Updated** | 2026-11-09 | 

## 7. AI Usage Declaration

* **AI Tools Used:** ChatGPT / Gemini 3 Flash.

* **Tasks Performed:** Formatting SQL role templates, drafting permission validation matrix.

* **Validation Procedure:** Executed all GRANT/REVOKE commands and verified access errors in `psql`.