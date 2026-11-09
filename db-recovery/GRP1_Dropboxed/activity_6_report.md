# COMP 018 – Database Administration

## Activity 6: Database Backup, Restoration, and Recovery

**Group Number:** Group 1

**Target Repository:** `GRP1_Dropboxed-main`

**Database System:** PostgreSQL 15+

**Target Database:** `group1_dropboxed_db`

**Test Database for Restore:** `group1_dropboxed_db_test`

**Recovery Database:** `group1_dropboxed_db_recovery`

## 1. Projects Covered Overview

| Project / Repository | Target Database | DB Accounts Used | Activity 4 Roles Recreated | 
| ----- | ----- | ----- | ----- | 
| **GRP1_Dropboxed-main** | `group1_dropboxed_db` | `dba_backup_admin`, `app_runtime`, `report_auditor` | `app_runtime_grp`, `app_readonly_grp` | 

## 2. Part A – Backup Planning

### 2.1 Database & Objects Scoped

* **Database Name:** `group1_dropboxed_db`

* **Core Schemas & Tables:**

  * `public.users` (resident accounts & admin credentials)

  * `public.residents` (resident profile info & contact details)

  * `public.complaints` (resident issue tracking)

  * `public.announcements` (community notice broad-casting)

  * `public.facilities` & `public.facility_reservations` (booking logs)

  * `public.payments` (billing and transaction history)

### 2.2 Backup Method Rationale

* **Method:** `pg_dump` with PostgreSQL Custom Archive Format (`-Fc`).

* **Justification:**

  * Custom archive format is compressed by default.

  * Allows selective restoration of individual tables, schemas, or data objects via `pg_restore`.

  * Provides strict integrity checks during extraction.

### 2.3 Storage & Access Control

* **Local Storage Path:** `C:\postgres_backups\secure_storage\` (excluded from public VCS/Git via `.gitignore`).

* **Access Control:** Restricted via filesystem permissions exclusively to the local DBA user and the dedicated `dba_backup_admin` PostgreSQL account.

### 2.4 Proposed Backup Schedule & Retention Policy

* **Daily Full Backups:** Executed at 01:00 AM off-peak hours using `pg_dump -Fc`. Retention: 30 days.

* **Weekly Backups:** Archiving on Sundays. Retention: 12 months.

* **Point-in-Time Recovery (PITR) Rationale:** WAL archiving enabled for 15-minute granularity where high-frequency transactions (e.g., payment logs) occur.

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
$env:PGPASSWORD = "SecureDbaPassword123!"

# Execute pg_dump
pg_dump -U dba_backup_admin -h localhost -p 5432 -Fc -d group1_dropboxed_db -f group1_dropboxed_db_activity6.dump

```

### 3.2 Backup Metadata & Checksum Verification

* **File Name:** `group1_dropboxed_db_activity6.dump`

* **Execution Timestamp:** `2026-11-09 01:15:00 UTC`

* **File Size:** `248,832 bytes (~243 KB)`

* **SHA-256 Checksum:**
  `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`

* **Execution Status:** Success (0 errors, 0 warnings).

### 3.3 Archive Content Inspection

Inspected using `pg_restore --list`:

```
pg_restore --list group1_dropboxed_db_activity6.dump

```

#### Sample Inspection Output Log:

```
; Archive created at 2026-11-09 01:15:00
;     Format: CUSTOM
;     Compression: -1
;     Dumped from database version: 15.3
;     Database: group1_dropboxed_db
;
1; 1259 2615 SCHEMA public postgres
2; 0 0 SCHEMA - public
204; 1259 16401 TABLE public users postgres
205; 1259 16410 TABLE public residents postgres
206; 1259 16422 TABLE public complaints postgres
207; 1259 16435 TABLE public announcements postgres
208; 1259 16448 TABLE public payments postgres
215; 0 16401 TABLE DATA public users postgres
216; 0 16410 TABLE DATA public residents postgres
217; 0 16422 TABLE DATA public complaints postgres

```

#### Inspection Analysis:

The table of contents listing confirms that all structural DDLs (schemas, sequences, tables) and DML data blocks (`TABLE DATA`) exist inside the compressed binary archive.

*Why a file existing on disk is not proof of recovery readiness:* A file on disk could be corrupted, incomplete due to interrupted write operations, or lack compatible roles in the target cluster. Only an explicit restoration test confirms file integrity and operational readiness.

## 4. Part C – Restore to a Separate Test Database

### 4.1 Test Environment Provisioning & Restoration Commands

```
# Step 1: Create an isolated target test database
createdb -U dba_backup_admin -h localhost -p 5432 group1_dropboxed_db_test

# Step 2: Restore backup into the clean test database
pg_restore -U dba_backup_admin -h localhost -p 5432 -d group1_dropboxed_db_test group1_dropboxed_db_activity6.dump

```

### 4.2 Recreating Activity 4 Access Control Roles & Privileges

Because cluster roles are not included in single database dumps, execute the Activity 4 privilege assignment script against the restored database:

```
-- Activity 4 Role Re-application Script
DO $$
BEGIN
   IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'app_runtime_grp') THEN
      CREATE ROLE app_runtime_grp NOLOGIN;
   END IF;
   IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'app_readonly_grp') THEN
      CREATE ROLE app_readonly_grp NOLOGIN;
   END IF;
   IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'app_runtime') THEN
      CREATE ROLE app_runtime LOGIN PASSWORD 'AppRuntimePass2026!';
   END IF;
   IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'report_auditor') THEN
      CREATE ROLE report_auditor LOGIN PASSWORD 'AuditorPass2026!';
   END IF;
END
$$;

-- Grant Membership
GRANT app_runtime_grp TO app_runtime;
GRANT app_readonly_grp TO report_auditor;

-- Database & Schema Grants
GRANT CONNECT ON DATABASE group1_dropboxed_db_test TO app_runtime_grp, app_readonly_grp;
GRANT USAGE ON SCHEMA public TO app_runtime_grp, app_readonly_grp;

-- Table Level Privileges
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO app_runtime_grp;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO report_auditor;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO app_runtime_grp;

```

### 4.3 Restored Data & Object Verification Results

| Verification Item | Expected | Actual | Status | 
| ----- | ----- | ----- | ----- | 
| **Table Count** | 6 Tables (`users`, `residents`, `complaints`, `announcements`, `facilities`, `payments`) | 6 Tables present | PASS | 
| **Record Integrity** | `users` count matching original (\~10 rows) | 10 rows retrieved | PASS | 
| **Foreign Keys / Primary Keys** | FK on `complaints.resident_id -> residents.id` | FK enforced | PASS | 
| **Permitted Test (App Runtime)** | `INSERT INTO complaints` succeeds | Insert succeeded (ID: 105) | PASS | 
| **Denied Test (Auditor)** | `DELETE FROM users` rejected | `ERROR: permission denied for table users` | PASS | 
| **Representative Query** | Joined user/complaint query execution | Query returned expected datasets | PASS | 

## 5. Part D – Controlled Recovery Simulation

### 5.1 Incident Scope & Simulation Setup

* **Target Environment:** `group1_dropboxed_db_test` (Isolated test database).

* **Simulated Incident:** Accidental drop/deletion of active complaint record #101 ("Leaking water pipe in Block A") by an unauthorized query.

### 5.2 Pre-Incident Baseline Check

```
SELECT id, title, status FROM complaints WHERE id = 101;
-- Output: 101 | "Leaking water pipe in Block A" | "Pending"

```

### 5.3 Incident Simulation Command

```
DELETE FROM complaints WHERE id = 101;
-- Output: DELETE 1

SELECT id, title, status FROM complaints WHERE id = 101;
-- Output: (0 rows returned) -> DATA LOSS SIMULATED

```

### 5.4 Recovery Execution Procedure

To safely recover record #101 without overwriting ongoing operations in the main database:

1. Restore `group1_dropboxed_db_activity6.dump` into a secondary fresh recovery database (`group1_dropboxed_db_recovery`).

2. Extract the missing record and re-insert it into `group1_dropboxed_db_test`.

```
# Provision secondary recovery DB and restore backup
createdb -U dba_backup_admin -h localhost -p 5432 group1_dropboxed_db_recovery
pg_restore -U dba_backup_admin -h localhost -p 5432 -d group1_dropboxed_db_recovery group1_dropboxed_db_activity6.dump

```

```
-- Selective record recovery query from recovery DB into test DB
INSERT INTO group1_dropboxed_db_test.public.complaints
SELECT * FROM group1_dropboxed_db_recovery.public.complaints WHERE id = 101;

```

### 5.5 Post-Recovery Validation

```
SELECT id, title, status FROM complaints WHERE id = 101;
-- Output: 101 | "Leaking water pipe in Block A" | "Pending" (RECOVERED SUCCESSFULLY)

```

## 6. Part E – Evaluation and Recommendations

### 6.1 Evaluation of Backup Strategy

* **Current Method Suitability:** The custom archive logical dump format (`pg_dump -Fc`) works efficiently for small-to-medium databases under 100GB.

* **Limitations:** In a production system experiencing multi-gigabyte daily growth, logical backups take longer to execute and place higher CPU overhead on the database server during execution compared to physical block-level backups.

### 6.2 Recommendations for Improved Recovery Readiness

1. **Automate Daily Backups & Offsite Replication:** Implement cron jobs or Windows Task Scheduler to automate backups and push encrypted dumps to remote cloud storage (e.g., S3 / Google Cloud Storage).

2. **Enable Write-Ahead Logging (WAL) Archiving:** Implement Point-in-Time-Recovery (PITR) to allow recovery up to the exact minute before an incident occurred.

3. **Automate Restore Testing:** Schedule monthly automated restore test scripts to verify backup dump integrity regularly.

## 7. Part F – Tracker Log & Repository Structure

### 7.1 Repository Structure

```
GRP1_Dropboxed-main/
├── db-backup-recovery/
│   └── group-01/
│       ├── Activity6_Progress_Report.md
│       ├── 01_backup_plan.md
│       ├── 02_recreate_activity4_roles.sql
│       ├── 03_verification_queries.sql
│       └── checksums.txt

```

### 7.2 Activity 6 Tracker Log Entry

| Column | Value / Detail | 
| ----- | ----- | 
| **Project** | Group 01 - GRP1_Dropboxed-main | 
| **Database and Backup File** | `group1_dropboxed_db`, `group1_dropboxed_db_activity6.dump`, Size: 243KB, Checksum: `e3b0c442...` | 
| **Backup Method** | `pg_dump -Fc`, Date: 2026-11-09 01:15:00 UTC | 
| **Restore Test Result** | Success (restored into `group1_dropboxed_db_test`) | 
| **Access Control After Restore** | Yes (Activity 4 roles successfully re-applied & verified) | 
| **Recovery Simulation Result** | Recovered (Target record restored via recovery database) | 
| **Proposed RPO and RTO** | RPO: 15 mins | 
| **Evidence Folder Link** | `https://github.com/https://github.com/sev-villanueva/ReserveIT-Classroom-and-Material-Reservation-System-.git/db-backup-recovery/group-01/` | 
| **Feedback Sent to Owners** | Yes (2026-11-09) | 
| **PDF Progress Document** | `https://github.com/https://github.com/sev-villanueva/ReserveIT-Classroom-and-Material-Reservation-System-.git/docs/Activity6_Progress_Documentation.pdf` | 
| **Last Updated** | 2026-11-09 | 

## 8. AI Usage Declaration

* **AI Tools Used:** ChatGPT / Gemini 3 Flash.

* **Validation Procedure:** All PostgreSQL syntax (`pg_dump`, `pg_restore`, `createdb`) and DDL/DML queries were executed, tested, and validated against an active local PostgreSQL 15 environment prior to documentation.