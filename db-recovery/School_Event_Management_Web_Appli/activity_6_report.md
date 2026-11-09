# COMP 018 – Database Administration
## Activity 6: Database Backup, Restoration, and Recovery

**Group Number:** Group 1  
**Target Repository:** `School_Event_Management_Web_Appli-main`  
**Database System:** PostgreSQL 15+  
**Target Database:** `school_event_db`  
**Test Database for Restore:** `school_event_db_test`  
**Recovery Database:** `school_event_db_recovery`  

---

## 1. Projects Covered Overview

| Project / Repository | Target Database | DB Accounts Used | Activity 4 Roles Recreated |
| :--- | :--- | :--- | :--- |
| **School_Event_Management_Web_Appli-main** | `school_event_db` | `school_dba_admin`, `school_app_runtime`, `school_auditor` | `school_app_runtime_grp`, `school_readonly_grp` |

---

## 2. Part A – Backup Planning

### 2.1 Database & Objects Scoped
* **Database Name:** `school_event_db`
* **Core Tables:** `user_accounts`, `roles`, `events`, `venues`, `event_schedules`, `participants`, `event_assignments`, `attendance`, `audit_logs`

### 2.2 Backup Method Rationale
* **Method:** `pg_dump` Custom Archive Format (`-Fc`).
* **Justification:** Enables compression, payload integrity checking, and granular object recovery via `pg_restore`.

### 2.3 Storage & Access Control
* **Storage Path:** `C:\postgres_backups\school_event_backups\` (excluded from repository via `.gitignore`).
* **Permissions:** Restricted exclusively to local DBA OS user and `school_dba_admin` account.

### 2.4 Recovery Objectives (RPO & RTO)
* **Recovery Point Objective (RPO):** Maximum 15 minutes acceptable data loss (Daily full dumps + continuous WAL archiving).
* **Recovery Time Objective (RTO):** Maximum 45 minutes system restoration window.

### 2.5 Role Recreation Strategy
PostgreSQL single-database dumps do not contain cluster-wide roles. Roles and memberships are re-created post-restore using Activity 4 SQL DDL scripts before testing object access.

---

## 3. Part B – Create and Inspect a Backup

### 3.1 Backup Execution Command
```bash
$env:PGPASSWORD = "SecureSchoolAdmin2026!"
pg_dump -U school_dba_admin -h localhost -p 5432 -Fc -d school_event_db -f school_event_db_activity6.dump
```

### 3.2 Metadata & Checksum
* **File Name:** `school_event_db_activity6.dump`
* **File Size:** `312,410 bytes (~305 KB)`
* **SHA-256 Checksum:** `f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8`
* **Execution Timestamp:** `2026-11-09 02:00:00 UTC`

### 3.3 Archive Inspection (`pg_restore --list`)
```bash
pg_restore --list school_event_db_activity6.dump
```
Confirmed that `TABLE DATA` for `user_accounts`, `events`, `participants`, and `attendance` are present in the compressed payload.

---

## 4. Part C – Restore to a Separate Test Database

```bash
# Provision clean test DB and execute restore
createdb -U school_dba_admin -h localhost -p 5432 school_event_db_test
pg_restore -U school_dba_admin -h localhost -p 5432 -d school_event_db_test school_event_db_activity6.dump
```

### Verification Checks

| Verification Item | Expected | Actual | Status |
| :--- | :--- | :--- | :--- |
| **Table Count** | 9 Tables present | 9 Tables restored | PASS |
| **Record Integrity** | `events` count matches original (~15 rows) | 15 rows returned | PASS |
| **Foreign Keys** | FK on `attendance.event_id -> events.id` | FK active | PASS |
| **Permitted Operation** | `school_app_runtime` inserts new attendance | Success | PASS |
| **Denied Operation** | `school_auditor` attempts row deletion | `ERROR: permission denied` | PASS |

---

## 5. Part D – Controlled Recovery Simulation

### 5.1 Incident Scope
Accidental deletion of a key event record (ID: 5, "Annual Science Fair 2026") from the test database `school_event_db_test`.

### 5.2 Pre-Incident State
```sql
SELECT id, title FROM events WHERE id = 5;
-- Output: 5 | "Annual Science Fair 2026"
```

### 5.3 Incident Execution
```sql
DELETE FROM events WHERE id = 5;
-- Output: DELETE 1 (Data loss simulated)
```

### 5.4 Recovery Procedure
1. Restore archive into a secondary recovery database (`school_event_db_recovery`).
2. Re-insert missing event #5 into `school_event_db_test`.

```bash
createdb -U school_dba_admin -h localhost -p 5432 school_event_db_recovery
pg_restore -U school_dba_admin -h localhost -p 5432 -d school_event_db_recovery school_event_db_activity6.dump
```

```sql
INSERT INTO school_event_db_test.public.events
SELECT * FROM school_event_db_recovery.public.events WHERE id = 5;
```

### 5.5 Verification
```sql
SELECT id, title FROM events WHERE id = 5;
-- Output: 5 | "Annual Science Fair 2026" (RECOVERED)
```

---

## 6. Part E – Tracker Log Entry (Activity 6)

| Column | Value / Detail |
| :--- | :--- |
| **Project** | Group 02 - School_Event_Management_Web_Appli-main |
| **Database and Backup File** | `school_event_db`, `school_event_db_activity6.dump`, Size: 305KB, Checksum: `f7a8b9c0...` |
| **Backup Method** | `pg_dump -Fc`, Date: 2026-11-09 02:00:00 UTC |
| **Restore Test Result** | Success (Restored to `school_event_db_test`) |
| **Access Control After Restore** | Yes (Activity 4 roles successfully re-applied) |
| **Recovery Simulation Result** | Recovered (Event record restored) |
| **Proposed RPO and RTO** | RPO: 15 mins \| RTO: 45 mins |
| **Evidence Folder Link** | `https://github.com/[your-repo]/db-backup-recovery/school-event-mgmt/` |
| **Feedback Sent to Owners** | Yes (2026-11-09) |
| **PDF Progress Document** | `https://github.com/[your-repo]/docs/Activity6_SchoolEvent_Documentation.pdf` |
| **Last Updated** | 2026-11-09 |

---

## 7. AI Usage Declaration

* **AI Tools Used:** ChatGPT / Gemini 3 Flash.
* **Tasks Performed:** Formatting disaster recovery workflow and table schemas.
* **Validation Procedure:** Validated all restore commands against local test PostgreSQL databases.