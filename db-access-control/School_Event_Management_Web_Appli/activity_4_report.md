# COMP 018 – Database Administration
## Activity 4: Database Users, Roles, Privileges, and Access Control

**Group Number:** Group 1  
**Target Repository:** `School_Event_Management_Web_Appli-main`  
**Database System:** PostgreSQL 15+  
**Target Database:** `school_event_db`  

---

## 1. Projects Set Up Overview

| Project / Repository | Database Name | Primary Database Objects Identified | Setup Result |
| :--- | :--- | :--- | :--- |
| **School_Event_Management_Web_Appli-main** | `school_event_db` | `user_accounts`, `roles`, `events`, `venues`, `event_schedules`, `participants`, `event_assignments`, `attendance`, `audit_logs` | Success |

---

## 2. Access Control Plan

| Login Account | Group Role | Application Role Served | Responsibilities | Required Privileges |
| :--- | :--- | :--- | :--- | :--- |
| `school_dba_admin` | N/A | Database Administrator | Schema management, migration maintenance, role assignment | Elevated privileges (`CREATEDB`, `CREATEROLE`) |
| `school_app_runtime` | `school_app_runtime_grp` | Spring Boot Backend Application | Fulfilling application backend REST API calls (CRUD on events, participants, attendance) | `CONNECT` on DB, `USAGE` on `public` schema, `SELECT`, `INSERT`, `UPDATE`, `DELETE` on all tables, `USAGE` on sequences |
| `school_auditor` | `school_readonly_grp` | Compliance Officer / Auditor | Reading event schedules, attendance stats, and audit logs without modification | `CONNECT` on DB, `USAGE` on `public` schema, `SELECT` on all tables |
| `school_staff_user` | `school_staff_grp` | Event Coordinator | Managing event participation and attendance records | `CONNECT` on DB, `USAGE` on `public` schema, `SELECT`, `INSERT`, `UPDATE` on `events`, `participants`, `attendance` |

---

## 3. SQL Access Control Implementation Summary

```sql
-- 1. Create NOLOGIN Group Roles
CREATE ROLE school_app_runtime_grp NOLOGIN;
CREATE ROLE school_readonly_grp NOLOGIN;
CREATE ROLE school_staff_grp NOLOGIN;

-- 2. Create LOGIN Accounts with Secure Passwords
CREATE ROLE school_dba_admin WITH LOGIN CREATEDB CREATEROLE PASSWORD 'SecureSchoolAdmin2026!';
CREATE ROLE school_app_runtime WITH LOGIN PASSWORD 'SchoolAppPass2026!';
CREATE ROLE school_auditor WITH LOGIN PASSWORD 'AuditorSchoolPass2026!';
CREATE ROLE school_staff_user WITH LOGIN PASSWORD 'StaffPass2026!';

-- 3. Assign Role Memberships
GRANT school_app_runtime_grp TO school_app_runtime;
GRANT school_readonly_grp TO school_auditor;
GRANT school_staff_grp TO school_staff_user;

-- 4. Restrict Default Public Schema Privileges
REVOKE ALL ON SCHEMA public FROM PUBLIC;

-- 5. Grant Explicit Privileges
GRANT CONNECT ON DATABASE school_event_db TO school_app_runtime_grp, school_readonly_grp, school_staff_grp;
GRANT USAGE ON SCHEMA public TO school_app_runtime_grp, school_readonly_grp, school_staff_grp;

-- Application Runtime Permissions
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO school_app_runtime_grp;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO school_app_runtime_grp;

-- Auditor Permissions
GRANT SELECT ON ALL TABLES IN SCHEMA public TO school_readonly_grp;

-- Staff Coordinator Permissions
GRANT SELECT, INSERT, UPDATE ON TABLE public.events, public.participants, public.attendance TO school_staff_grp;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO school_staff_grp;
```

---

## 4. Privilege Verification Results

| Account Used | Operation Tested | SQL Statement / Test | Expected Result | Actual Result | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `school_app_runtime` | Fetch event records | `SELECT * FROM events;` | Allowed | Returned active events | PASS |
| `school_app_runtime` | Log event attendance | `INSERT INTO attendance (event_id, participant_id, status) VALUES (1, 10, 'PRESENT');` | Allowed | Inserted successfully | PASS |
| `school_auditor` | View audit logs | `SELECT * FROM audit_logs;` | Allowed | Returned logs | PASS |
| `school_auditor` | Modify event schedule | `UPDATE event_schedules SET start_time = NOW();` | Denied | `ERROR: permission denied for table event_schedules` | PASS |
| `school_staff_user` | Add participant | `INSERT INTO participants (first_name, last_name, email) VALUES ('Alex', 'Smith', 'alex@school.edu');` | Allowed | Participant created | PASS |
| `school_staff_user` | Delete user account | `DELETE FROM user_accounts WHERE id = 2;` | Denied | `ERROR: permission denied for table user_accounts` | PASS |
| `school_app_runtime` | Create DB | `CREATE DATABASE test_db;` | Denied | `ERROR: permission denied to create database` | PASS |

---

## 5. Principle of Least Privilege Justification

1. **Spring Boot Connection Hardening:** `school_app_runtime` operates with explicitly defined object-level permissions, preventing arbitrary database creation or administrative modifications.
2. **Revocation of PUBLIC Privileges:** Explicitly revoking PUBLIC schema grants prevents default user access to unassigned database objects.
3. **Auditor Isolation:** Read-only privileges allow system compliance auditing while ensuring zero risk of data mutation.

---

## 6. Tracker Log Entry (Activity 4)

| Column | Details / Value |
| :--- | :--- |
| **Project** | Group 02 - School_Event_Management_Web_Appli-main |
| **Repository Cloned** | `https://github.com/[your-repo]/School_Event_Management_Web_Appli-main` |
| **Database Setup Result** | Success |
| **Access-Control Folder Link** | `https://github.com/[your-repo]/db-access-control/school-event-mgmt/` |
| **Access-Control Status** | Completed |
| **Feedback Sent to Owners** | Yes (2026-11-09) |
| **PDF Progress Document** | `https://github.com/[your-repo]/docs/Activity4_SchoolEvent_Documentation.pdf` |
| **Last Updated** | 2026-11-09 |

---

## 7. AI Usage Declaration

* **AI Tools Used:** ChatGPT / Gemini 3 Flash.
* **Tasks Performed:** Generating RBAC Grant/Revoke scripts tailored to Spring Security tables and structuring testing matrices.
* **Validation Procedure:** Tested all PostgreSQL operations against a local PostgreSQL instance.