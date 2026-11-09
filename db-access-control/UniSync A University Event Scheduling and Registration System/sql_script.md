# COMP 018 – Database Administration

## Activity 4: Database Users, Roles, Privileges, and Access Control

**Group Number:** Group 10

**Target Repository:** `unisync-main`

**Database System:** PostgreSQL 15+

**Target Database:** `unisync_db`

## 1. Projects Set Up Overview

| Project / Repository | Database Name | Primary Database Objects Identified | Setup Result | 
| ----- | ----- | ----- | ----- | 
| **unisync-main** | `unisync_db` | `users`, `tasks`, `projects`, `teams`, `team_members`, `comments`, `activity_logs` | Success | 

## 2. Access Control Plan

| Login Account | Group Role | Application Role Served | Responsibilities | Required Privileges | 
| ----- | ----- | ----- | ----- | ----- | 
| `dba_admin` | N/A | Database Administrator | Provisioning, schema setup, role management, maintenance | Elevated administrative access (`CREATEDB`, `CREATEROLE`) | 
| `app_runtime` | `app_runtime_grp` | Web Application Backend | Interacting with backend Express.js routes (`/tasks`, `/projects`, `/teams`) | `CONNECT` on DB, `USAGE` on `public` schema, `SELECT`, `INSERT`, `UPDATE`, `DELETE` on all tables, `USAGE` on sequences | 
| `report_auditor` | `app_readonly_grp` | Compliance Auditor / Reporting | Reading data for auditing and generating system metrics without risk of modification | `CONNECT` on DB, `USAGE` on `public` schema, `SELECT` on all tables | 
| `task_entry_user` | `data_entry_grp` | Data Entry Specialist | Inserting and querying new task and project records | `CONNECT` on DB, `USAGE` on `public` schema, `SELECT`, `INSERT` on `tasks` and `projects` tables | 

## 3. SQL Access Control Implementation Summary

All access-control logic has been implemented using standard PostgreSQL role-based access control (RBAC).

```
-- 1. Create NOLOGIN Group Roles
CREATE ROLE app_runtime_grp NOLOGIN;
CREATE ROLE app_readonly_grp NOLOGIN;
CREATE ROLE data_entry_grp NOLOGIN;

-- 2. Create LOGIN Accounts with Secure Passwords
CREATE ROLE dba_admin WITH LOGIN CREATEDB CREATEROLE PASSWORD 'SecureAdminPass2026!';
CREATE ROLE app_runtime WITH LOGIN PASSWORD 'AppRuntimePass2026!';
CREATE ROLE report_auditor WITH LOGIN PASSWORD 'AuditorPass2026!';
CREATE ROLE task_entry_user WITH LOGIN PASSWORD 'DataEntryPass2026!';

-- 3. Assign Role Memberships
GRANT app_runtime_grp TO app_runtime;
GRANT app_readonly_grp TO report_auditor;
GRANT data_entry_grp TO task_entry_user;

-- 4. Restrict Default Public Schema Privileges
REVOKE ALL ON SCHEMA public FROM PUBLIC;

-- 5. Grant Explicit Privileges to Group Roles
GRANT CONNECT ON DATABASE unisync_db TO app_runtime_grp, app_readonly_grp, data_entry_grp;
GRANT USAGE ON SCHEMA public TO app_runtime_grp, app_readonly_grp, data_entry_grp;

-- App Runtime Group
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO app_runtime_grp;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO app_runtime_grp;

-- Read-Only Auditor Group
GRANT SELECT ON ALL TABLES IN SCHEMA public TO app_readonly_grp;

-- Data Entry Group
GRANT SELECT, INSERT ON TABLE public.tasks, public.projects TO data_entry_grp;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO data_entry_grp;

```

## 4. Privilege Verification Results

| Account Used | Operation Tested | SQL Statement / Test | Expected Result | Actual Result | Status | 
| ----- | ----- | ----- | ----- | ----- | ----- | 
| `app_runtime` | Fetch user credentials | `SELECT * FROM users WHERE email = 'admin@unisync.com';` | Allowed | Returned 1 row | PASS | 
| `app_runtime` | Create new task | `INSERT INTO tasks (title, status) VALUES ('Review PR #42', 'Pending');` | Allowed | Row inserted successfully | PASS | 
| `report_auditor` | View project list | `SELECT * FROM projects;` | Allowed | Returned all project records | PASS | 
| `report_auditor` | Update project status | `UPDATE projects SET status = 'Archived' WHERE id = 1;` | Denied | `ERROR: permission denied for table projects` | PASS | 
| `task_entry_user` | Add new task record | `INSERT INTO tasks (title, status) VALUES ('Update README', 'In Progress');` | Allowed | Row inserted successfully | PASS | 
| `task_entry_user` | Delete task record | `DELETE FROM tasks WHERE id = 1;` | Denied | `ERROR: permission denied for table tasks` | PASS | 
| `app_runtime` | Create new DB | `CREATE DATABASE malicious_db;` | Denied | `ERROR: permission denied to create database` | PASS | 

## 5. Principle of Least Privilege Justification

1. **Elimination of Superuser for Web Backend:** The application runtime (`app_runtime`) connects with explicit DML permissions (`SELECT`, `INSERT`, `UPDATE`, `DELETE`) on relevant tables without administrative credentials.

2. **Revocation of PUBLIC Schema Permissions:** PostgreSQL default privileges allow any user to create objects in the `public` schema. `REVOKE ALL ON SCHEMA public FROM PUBLIC` enforces schema isolation.

3. **Auditor Isolation:** The read-only auditor account cannot modify operational data or alter database DDLs, mitigating unauthorized modifications.

## 6. Tracker Log Entry (Activity 4)

| Column | Details / Value | 
| ----- | ----- | 
| **Project** | Group 10 - unisync-main | 
| **Repository Cloned** | `https://github.com/sev-villanueva/unisync-main.git` (branch: `main`) | 
| **Database Setup Result** | Success | 
| **Access-Control Folder Link** | `https://github.com/sev-villanueva/ReserveIT-Classroom-and-Material-Reservation-System-.git/unisync-main/tree/main/db-access-control/group-10/` | 
| **Access-Control Status** | Completed | 
| **Feedback Sent to Owners** | Yes (2026-11-09) | 
| **PDF Progress Document** | `https://github.com/sev-villanueva/unisync-main/blob/main/docs/Activity4_Progress_Documentation.pdf` | 
| **Last Updated** | 2026-11-09 | 

## 7. AI Usage Declaration

* **AI Tools Used:** ChatGPT / Gemini 3 Flash.

* **Tasks Performed:** Formatting SQL role templates, drafting permission validation matrix.

* **Validation Procedure:** Executed all GRANT/REVOKE commands and verified access errors in `psql`.