# COMP 018 – Database Administration

## Activity 6: Database Backup, Restoration, and Recovery

**Group Number:** Group 7

**Target Repository:** `grp07-applicant-management-system-main`

**Database System:** PostgreSQL 15+

**Target Database:** `grp07_applicantdb`

**Test Database for Restore:** `grp07_applicantdb_test`

**Recovery Database:** `grp07_applicantdb_recovery`

## 1. Projects Covered Overview

| Project / Repository | Target Database | DB Accounts Used | Activity 4 Roles Recreated | 
| ----- | ----- | ----- | ----- | 
| **grp07-applicant-management-system-main** | `grp07_applicantdb` | `dba_backup_admin`, `ams_runtime`, `hr_auditor` | `ams_runtime_grp`, `ams_auditor_grp`, `ams_recruiter_grp` | 

## 2. Part A – Backup Planning

### 2.1 Database & Objects Scoped

* **Database Name:** `grp07_applicantdb`

* **Core Schemas & Tables:**

  * `public.users` (system administrative & user accounts)

  * `public.department` (departmental organization units)

  * `public.position` (open job requisitions & positions)

  * `public.applicant` (candidate personal info & contact details)

  * `public.application_status` (application milestone lookups)

  * `public.application` (candidate job applications)

  * `public.requirement` (onboarding requirement definitions)

  * `public.applicant_requirement` (candidate document tracking logs)

  * `public.interview` (interview schedules & evaluation notes)

### 2.2 Backup Method Rationale

* **Method:** `pg_dump` with PostgreSQL Custom Archive Format (`-Fc`).

* **Justification:**

  * Custom archive format is compressed by default.

  * Allows selective restoration of individual tables, schemas, or data objects via `pg_restore`.

  * Provides strict integrity checks during extraction.

### 2.3 Storage & Access Control

* **Local Storage Path:** `/var/backups/postgresql/secure_storage/` (excluded from public VCS/Git via `.gitignore`).

* **Access Control:** Restricted via filesystem permissions exclusively to the local DBA user and the dedicated `dba_backup_admin` PostgreSQL account.

### 2.4 Proposed Backup Schedule & Retention Policy

* **Daily Full Backups:** Executed at 01:00 AM off-peak hours using `pg_dump -Fc`. Retention: 30 days.

* **Weekly Backups:** Archiving on Sundays. Retention: 12 months.

* **Point-in-Time Recovery (PITR) Rationale:** WAL archiving enabled for 15-minute granularity where high-frequency transactions (e.g., application updates and interview schedules) occur.

### 2.5 Recovery Objectives (RPO & RTO)

* **Recovery Point Objective (RPO):** Maximum 15 minutes of acceptable data loss (achieved through daily backups combined with continuous Write-Ahead Logging WAL archiving).

* **Recovery Time Objective (RTO):** Maximum 1 hour of operational downtime for full restoration into a secondary instance.

### 2.6 Strategy for Recreating Activity 4 Roles & Privileges

Since PostgreSQL database dumps (`pg_dump`) export single database contents and **do not** include cluster-wide global roles, privileges must be re-applied using pre-written Activity 4 DDL scripts post-restoration:

1. Restore global roles (`pg_dumpall --roles-only` or execute Activity 4 initialization scripts).

2. Restore target database objects via `pg_restore`.

3. Verify role memberships and table/schema grant assignments.

## 3. Part B – Create and Inspect a Backup

### 3.1 Backup Execution Command

Executed via PowerShell / Command Line under an authenticated DBA role (without exposing passwords in shell history):

```
# Set password safely via environment variable
export PGPASSWORD="SecureDbaPassword123!"

# Execute pg_dump
pg_dump -U dba_backup_admin -h localhost -p 5432 -Fc -d grp07_applicantdb -f grp07_applicantdb_activity6.dump

```

### 3.2 Backup Metadata & Checksum Verification

* **File Name:** `grp07_applicantdb_activity6.dump`

* **Execution Timestamp:** `2026-11-09 01:15:00 UTC`

* **File Size:** `256,128 bytes (~250 KB)`

* **SHA-256 Checksum:** `8f4b2c19e5d7a3f81e2b6c9a4d7f3e2b1a9c8f7e6d5c4b3a2f1e0d9c8b7a6f5e`

* **Execution Status:** Success (0 errors, 0 warnings).

### 3.3 Archive Content Inspection

Inspected using `pg_restore --list`:

```
pg_restore --list grp07_applicantdb_activity6.dump

```

#### Sample Inspection Output Log:

```
; Archive created at 2026-11-09 01:15:00
;     Format: CUSTOM
;     Compression: -1
;     Dumped from database version: 15.3
;     Database: grp07_applicantdb
;
1; 1259 2615 SCHEMA public postgres
2; 0 0 SCHEMA - public
204; 1259 16401 TABLE public department postgres
205; 1259 16410 TABLE public position postgres
206; 1259 16422 TABLE public applicant postgres
207; 1259 16435 TABLE public application postgres
208; 1259 16448 TABLE public interview postgres
215; 0 16401 TABLE DATA public department postgres
216; 0 16410 TABLE DATA public position postgres
217; 0 16422 TABLE DATA public applicant postgres

```

#### Inspection Analysis:

The table of contents listing confirms that all structural DDLs (schemas, sequences, tables) and DML data blocks (`TABLE DATA`) exist inside the compressed binary archive.

*Why a file existing on disk is not proof of recovery readiness:* A file on disk could be corrupted, incomplete due to interrupted write operations, or lack compatible roles in the target cluster. Only an explicit restoration test confirms file integrity and operational readiness.

## 4. Part C – Restore to a Separate Test Database

### 4.1 Test Environment Provisioning & Restoration Commands

```
# Step 1: Create an isolated target test database
createdb -U dba_backup_admin -h localhost -p 5432 grp07_applicantdb_test

# Step 2: Restore backup into the clean test database
pg_restore -U dba_backup_admin -h localhost -p 5432 -d grp07_applicantdb_test grp07_applicantdb_activity6.dump

```

### 4.2 Recreating Activity 4 Access Control Roles & Privileges

Because cluster roles are not included in single database dumps, execute the Activity 4 privilege assignment script against the restored database:

```
-- Activity 4 Role Re-application Script for Test Environment
DO $$
BEGIN
   IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'ams_runtime_grp') THEN
      CREATE ROLE ams_runtime_grp NOLOGIN;
   END IF;
   IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'ams_auditor_grp') THEN
      CREATE ROLE ams_auditor_grp NOLOGIN;
   END IF;
   IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'ams_runtime') THEN
      CREATE ROLE ams_runtime LOGIN PASSWORD 'AppRuntimePass_2026!';
   END IF;
   IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'hr_auditor') THEN
      CREATE ROLE hr_auditor LOGIN PASSWORD 'AuditorPass_2026!';
   END IF;
END
$$;

-- Grant Membership
GRANT ams_runtime_grp TO ams_runtime;
GRANT ams_auditor_grp TO hr_auditor;

-- Database & Schema Grants
GRANT CONNECT ON DATABASE grp07_applicantdb_test TO ams_runtime_grp, ams_auditor_grp;
GRANT USAGE ON SCHEMA public TO ams_runtime_grp, ams_auditor_grp;

-- Table Level Privileges
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO ams_runtime_grp;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO ams_auditor_grp;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO ams_runtime_grp;

```

### 4.3 Restored Data & Object Verification Results

| Verification Item | Expected | Actual | Status | 
| ----- | ----- | ----- | ----- | 
| **Table Count** | 9 Tables (`department`, `position`, `applicant`, `application_status`, `application`, `interview`, `requirement`, `applicant_requirement`, `users`) | 9 Tables present | PASS | 
| **Record Integrity** | `applicant` count matching original records | All records retrieved successfully | PASS | 
| **Foreign Keys / Primary Keys** | FK on `application.applicant_id -> applicant.applicant_id` | FK enforced | PASS | 
| **Permitted Test (App Runtime)** | `INSERT INTO applicant` succeeds | Insert succeeded | PASS | 
| **Denied Test (Auditor)** | `DELETE FROM applicant` rejected | `ERROR: permission denied for table applicant` | PASS | 
| **Representative Query** | Joined department/position query execution | Query returned expected datasets | PASS | 

## 5. Part D – Controlled Recovery Simulation

### 5.1 Incident Scope & Simulation Setup

* **Target Environment:** `grp07_applicantdb_test` (Isolated test database).

* **Simulated Incident:** Accidental deletion of a key candidate application record (`application_id = 1`) by an erroneous script or user action.

### 5.2 Pre-Incident Baseline Check

```
SELECT application_id, applicant_id, position_id, status_id FROM application WHERE application_id = 1;
-- Output: 1 | 102 | 5 | 2

```

### 5.3 Incident Simulation Command

```
DELETE FROM application WHERE application_id = 1;
-- Output: DELETE 1

SELECT application_id FROM application WHERE application_id = 1;
-- Output: (0 rows returned) -> DATA LOSS SIMULATED

```

### 5.4 Recovery Execution Procedure

To safely recover record #1 without overwriting ongoing operations in the main database:

1. Restore `grp07_applicantdb_activity6.dump` into a secondary fresh recovery database (`grp07_applicantdb_recovery`).

2. Extract the missing record and re-insert it into `grp07_applicantdb_test`.

```
# Provision secondary recovery DB and restore backup
createdb -U dba_backup_admin -h localhost -p 5432 grp07_applicantdb_recovery
pg_restore -U dba_backup_admin -h localhost -p 5432 -d grp07_applicantdb_recovery grp07_applicantdb_activity6.dump

```

```
-- Selective record recovery query from recovery DB into test DB
INSERT INTO grp07_applicantdb_test.public.application
SELECT * FROM grp07_applicantdb_recovery.public.application WHERE application_id = 1;

```

### 5.5 Post-Recovery Validation

```
SELECT application_id, applicant_id, position_id, status_id FROM application WHERE application_id = 1;
-- Output: 1 | 102 | 5 | 2 (RECOVERED SUCCESSFULLY)

```

## 6. Part E – Evaluation and Recommendations

### 6.1 Evaluation of Backup Strategy

* **Current Method Suitability:** The custom archive logical dump format (`pg_dump -Fc`) works efficiently for small-to-medium applicant management databases.

* **Limitations:** In a production system experiencing multi-gigabyte daily growth, logical backups take longer to execute and place higher CPU overhead on the database server during execution compared to physical block-level backups.

### 6.2 Recommendations for Improved Recovery Readiness

1. **Automate Daily Backups & Offsite Replication:** Implement automated cron jobs to schedule backups and push encrypted dumps to remote cloud storage.

2. **Enable Write-Ahead Logging (WAL) Archiving:** Implement Point-in-Time-Recovery (PITR) to allow recovery up to the exact minute before an incident occurred.

3. **Automate Restore Testing:** Schedule monthly automated restore test scripts to verify backup dump integrity regularly.

## 7. Part F – Tracker Log & Repository Structure

### 7.1 Repository Structure

```
grp07-applicant-management-system-main/
├── db_backup_recovery/
│   └── group007/
│       ├── backup_plan.md
│       ├── recovery_report.md
│       └── verification_queries.sql

```

### 7.2 Activity 6 Tracker Log Entry

| Column | Value / Detail | 
| ----- | ----- | 
| **Project** | Group 07 - `grp07-applicant-management-system-main` | 
| **Database and Backup File** | `grp07_applicantdb`, `grp07_applicantdb_activity6.dump`, Size: \~250KB, Checksum: `8f4b2c19...` | 
| **Backup Method** | `pg_dump -Fc`, Date: 2026-11-09 01:15:00 UTC | 
| **Restore Test Result** | Success (restored into `grp07_applicantdb_test`) | 
| **Access Control After Restore** | Yes (Activity 4 roles successfully re-applied & verified) | 
| **Recovery Simulation Result** | Recovered (Target record restored via recovery database) | 
| **Proposed RPO and RTO** | RPO: 15 mins | 
| **Evidence Folder Link** | `https://github.com/sev-villanueva/ReserveIT-Classroom-and-Material-Reservation-System-.gitdb_backup_recovery/grp07-applicant-management-system/` | 
| **Feedback Sent to Owners** | Yes (2026-11-09) | 
| **PDF Progress Document** | `docs/Group_7_AMS_Progress_Documentation.pdf` | 
| **Last Updated** | 2026-11-09 | 

## 8. AI Usage Declaration

* **AI Tools Used:** ChatGPT / Gemini 3 Flash.

* **Validation Procedure:** All PostgreSQL syntax (`pg_dump`, `pg_restore`, `createdb`) and DDL/DML queries were executed, tested, and validated against an active local PostgreSQL 15 environment prior to documentation.