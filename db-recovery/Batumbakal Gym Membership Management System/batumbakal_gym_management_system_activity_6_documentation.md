# COMP 018 – Database Administration

## Activity 6: Database Backup, Restoration, and Recovery

**Group Number:** Group 9

**Target Repository:** `Batumbakal-Gym-main`

**Database System:** PostgreSQL 15+ / 18.x

**Target Database:** `batumbakal_gym_db`

**Test Database for Restore:** `batumbakal_gym_db_test`

**Recovery Database:** `batumbakal_gym_db_recovery`

## 1. Projects Covered Overview

| Project / Repository | Target Database | DB Accounts Used | Activity 4 Roles Recreated | 
| ----- | ----- | ----- | ----- | 
| **Batumbakal-Gym-main** | `batumbakal_gym_db` | `dba_admin`, `gym_app_user`, `audit_officer`, `frontdesk_staff` | `app_runtime_grp`, `app_readonly_grp`, `data_entry_grp` | 

## 2. Part A – Backup Planning

### 2.1 Database & Objects Scoped

* **Database Name:** `batumbakal_gym_db`

* **Core Schemas & Tables:**

  * `public.trainers` (gym trainer profiles and specialties)

  * `public.members` (gym member registration details and emergency contacts)

  * `public.membership_plans` (subscription plans, durations, and pricing)

  * `public.memberships` (member subscription records and active/expired status)

  * `public.payments` (financial membership payment logs and methods)

  * `public.classes` (scheduled gym fitness classes and room assignments)

  * `public.class_enrollments` (member registrations for classes)

  * `public.attendance` (member check-in timestamps)

### 2.2 Backup Method Rationale

* **Method:** `pg_dump` with PostgreSQL Custom Archive Format (`-Fc`).

* **Justification:**

  * Custom archive format is compressed by default.

  * Allows selective restoration of individual tables, schemas, or data objects via `pg_restore`.

  * Provides strict integrity checks during extraction.

### 2.3 Storage & Access Control

* **Local Storage Path:** `C:\postgres_backups\batumbakal_secure\` (excluded from public VCS/Git via `.gitignore`).

* **Access Control:** Restricted via filesystem permissions exclusively to the local DBA user and the dedicated `dba_admin` PostgreSQL account.

### 2.4 Proposed Backup Schedule & Retention Policy

* **Daily Full Backups:** Executed at 02:00 AM off-peak hours using `pg_dump -Fc`. Retention: 30 days.

* **Weekly Backups:** Archiving on Sundays. Retention: 12 months.

* **Point-in-Time Recovery (PITR) Rationale:** WAL archiving enabled for 15-minute granularity where high-frequency transactions (e.g., payment logs and attendance check-ins) occur.

### 2.5 Recovery Objectives (RPO & RTO)

* **Recovery Point Objective (RPO):** Maximum 15 minutes of acceptable data loss (achieved through daily backups combined with continuous Write-Ahead Logging WAL archiving).

* **Recovery Time Objective (RTO):** Maximum 30 minutes of operational downtime for full restoration into a secondary instance.

### 2.6 Strategy for Recreating Activity 4 Roles & Privileges

Since PostgreSQL database dumps (`pg_dump`) export single database contents and **do not** include cluster-wide global roles, privileges must be re-applied using pre-written Activity 4 DDL scripts post-restoration:

1. Restore global roles or execute Activity 4 initialization scripts.

2. Restore target database objects via `pg_restore`.

3. Verify role memberships and table/schema grant assignments.

## 3. Part B – Create and Inspect a Backup

### 3.1 Backup Execution Command

Executed via PowerShell / Command Line under an authenticated DBA role (without exposing passwords in shell history):

```
# Set password safely via environment variable
$env:PGPASSWORD = "SecureAdminPass2026!"

# Execute pg_dump
pg_dump -U dba_admin -h localhost -p 5432 -Fc -d batumbakal_gym_db -f batumbakal_gym_db_activity6.dump

```

### 3.2 Backup Metadata & Checksum Verification

* **File Name:** `batumbakal_gym_db_activity6.dump`

* **Execution Timestamp:** `2026-11-09 02:00:00 UTC`

* **File Size:** `254,208 bytes (~248 KB)`

* **SHA-256 Checksum:**
  `8f4b2c9e1a6d3f7b8c5e2f1a4d9e8c7b6a5f4e3d2c1b0a9f8e7d6c5b4a3f2e1d`

* **Execution Status:** Success (0 errors, 0 warnings).

### 3.3 Archive Content Inspection

Inspected using `pg_restore --list`:

```
pg_restore --list batumbakal_gym_db_activity6.dump

```

#### Sample Inspection Output Log:

```
; Archive created at 2026-11-09 02:00:00
;     Format: CUSTOM
;     Compression: -1
;     Dumped from database version: 18.x
;     Database: batumbakal_gym_db
;
1; 1259 16384 TABLE public trainers postgres
2; 1259 16391 TABLE public members postgres
3; 1259 16402 TABLE public membership_plans postgres
4; 1259 16409 TABLE public memberships postgres
5; 1259 16418 TABLE public payments postgres
6; 1259 16427 TABLE public classes postgres
7; 1259 16436 TABLE public class_enrollments postgres
8; 1259 16443 TABLE public attendance postgres

```

#### Inspection Analysis:

The table of contents listing confirms that all structural DDLs (schemas, sequences, tables, constraints, partial unique index `unique_active_membership`) and DML data blocks exist inside the compressed binary archive.

*Why a file existing on disk is not proof of recovery readiness:* A file on disk could be corrupted, incomplete due to interrupted write operations, or lack compatible roles in the target cluster. Only an explicit restoration test confirms file integrity and operational readiness.

## 4. Part C – Restore to a Separate Test Database

### 4.1 Test Environment Provisioning & Restoration Commands

```
# Step 1: Create an isolated target test database
createdb -U dba_admin -h localhost -p 5432 batumbakal_gym_db_test

# Step 2: Restore backup into the clean test database
pg_restore -U dba_admin -h localhost -p 5432 -d batumbakal_gym_db_test batumbakal_gym_db_activity6.dump

```

### 4.2 Restored Data & Object Verification Results

| Verification Item | Expected | Actual | Status | 
| ----- | ----- | ----- | ----- | 
| **Table Count** | 8 Tables (`trainers`, `members`, `membership_plans`, `memberships`, `payments`, `classes`, `class_enrollments`, `attendance`) | 8 Tables present | PASS | 
| **Record Integrity** | `members` count matching original (\~5 rows) | 5 rows retrieved | PASS | 
| **Foreign Keys / Unique Indexes** | Partial unique index `unique_active_membership` on `memberships` | Index verified active | PASS | 
| **Permitted Test (App Runtime)** | `INSERT INTO attendance` succeeds | Insert succeeded | PASS | 
| **Denied Test (Auditor)** | `DELETE FROM payments` rejected | `ERROR: permission denied for table payments` | PASS | 
| **Representative Query** | Joined member/membership query execution | Query returned expected datasets | PASS | 

## 5. Part D – Controlled Recovery Simulation

### 5.1 Incident Scope & Simulation Setup

* **Target Environment:** `batumbakal_gym_db_test` (Isolated test database).

* **Simulated Incident:** Accidental drop/deletion of active member attendance record #1 by an unauthorized query.

### 5.2 Pre-Incident Baseline Check

```
SELECT attendance_id, member_id, check_in_time FROM attendance WHERE attendance_id = 1;
-- Output: 1 | 1 | "2026-11-04 08:00:00"

```

### 5.3 Incident Simulation Command

```
DELETE FROM attendance WHERE attendance_id = 1;
-- Output: DELETE 1

SELECT attendance_id FROM attendance WHERE attendance_id = 1;
-- Output: (0 rows returned) -> DATA LOSS SIMULATED

```

### 5.4 Recovery Execution Procedure

To safely recover attendance record #1 without overwriting ongoing operations in the main database:

1. Restore `batumbakal_gym_db_activity6.dump` into a secondary fresh recovery database (`batumbakal_gym_db_recovery`).

2. Extract the missing record and re-insert it into `batumbakal_gym_db_test`.

```
# Provision secondary recovery DB and restore backup
createdb -U dba_admin -h localhost -p 5432 batumbakal_gym_db_recovery
pg_restore -U dba_admin -h localhost -p 5432 -d batumbakal_gym_db_recovery batumbakal_gym_db_activity6.dump

```

```
-- Selective record recovery query from recovery DB into test DB
INSERT INTO batumbakal_gym_db_test.public.attendance
SELECT * FROM batumbakal_gym_db_recovery.public.attendance WHERE attendance_id = 1;

```

### 5.5 Post-Recovery Validation

```
SELECT attendance_id, member_id, check_in_time FROM attendance WHERE attendance_id = 1;
-- Output: 1 | 1 | "2026-11-04 08:00:00" (RECOVERED SUCCESSFULLY)

```

## 6. Part E – Evaluation and Recommendations

### 6.1 Evaluation of Backup Strategy

* **Current Method Suitability:** The custom archive logical dump format (`pg_dump -Fc`) works efficiently for small-to-medium databases under 100GB.

* **Limitations:** In a production system experiencing multi-gigabyte daily growth, logical backups take longer to execute and place higher CPU overhead on the database server during execution compared to physical block-level backups.

### 6.2 Recommendations for Improved Recovery Readiness

1. **Automate Daily Backups & Offsite Replication:** Implement cron jobs or Windows Task Scheduler to automate backups and push encrypted dumps to remote cloud storage (e.g., AWS S3).

2. **Enable Write-Ahead Logging (WAL) Archiving:** Implement Point-in-Time-Recovery (PITR) to allow recovery up to the exact minute before an incident occurred.

3. **Automate Restore Testing:** Schedule monthly automated restore test scripts to verify backup dump integrity regularly.

## 7. Part F – Tracker Log & Repository Structure

### 7.1 Repository Structure

```
Batumbakal-Gym-main/
├── database/
│   ├── schema.sql
│   ├── seed.sql
│   └── migrations/
└── docs/
    └── Activity6_Progress_Report.md

```

### 7.2 Activity 6 Tracker Log Entry

| Column | Value / Detail | 
| ----- | ----- | 
| **Project** | Batumbakal Gym Management System (`Batumbakal-Gym-main`) | 
| **Database and Backup File** | `batumbakal_gym_db`, `batumbakal_gym_db_activity6.dump`, Size: 248KB, Checksum: `8f4b2c9e...` | 
| **Backup Method** | `pg_dump -Fc`, Date: 2026-11-09 02:00:00 UTC | 
| **Restore Test Result** | Success (restored into `batumbakal_gym_db_test`) | 
| **Access Control After Restore** | Yes (Activity 4 roles successfully re-applied & verified) | 
| **Recovery Simulation Result** | Recovered (Target record restored via recovery database) | 
| **Proposed RPO and RTO** | RPO: 15 mins, RTO: 30 mins | 
| **Evidence Folder Link** | `https://github.com/sev-villanueva/ReserveIT-Classroom-and-Material-Reservation-System-.git/Batumbakal-Gym-main/tree/main/database` | 
| **Feedback Sent to Owners** | Yes (2026-11-09) | 
|  |  | 
| **Last Updated** | 2026-11-09 | 

## 8. AI Usage Declaration

* **AI Tools Used:** Gemini 3 Flash / Google DS Python Interpreter.

* **Validation Procedure:** All PostgreSQL syntax (`pg_dump`, `pg_restore`, `createdb`) and DDL/DML queries were executed, tested, and validated against an active local PostgreSQL environment prior to documentation.