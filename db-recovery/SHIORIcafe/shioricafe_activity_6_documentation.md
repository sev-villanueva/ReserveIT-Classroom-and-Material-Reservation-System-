# COMP 018 – Database Administration

## Activity 6: Database Backup, Restoration, and Recovery

**Group Number:** Group 5

**Target Repository:** `SHIORIcafe-new-main`

**Database System:** PostgreSQL 15.3

**Target Database:** `shioricafe_db`

**Account Used for Checks:** `dba_admin` (Backup / Restore / Verification)

## 1. Projects Monitored Overview

| Project / Repository | Database Inspected | Account & Role Used | Backup Status | Restoration Status | Recovery Simulation | Recommendation Priority | 
| ----- | ----- | ----- | ----- | ----- | ----- | ----- | 
| **SHIORIcafe-new-main** | `shioricafe_db` (v15.3) | `dba_admin` | Successful (`-Fc` format) | Verified in `shioricafe_test_db` | Successful (Test record recovery) | Follow-up action | 

## 2. Part A – Backup Planning

### 2.1 Backup Strategy and Parameters

* **Database & Objects:** All application schemas, tables (`menu_items`, `orders`, `order_items`, `reservations`, `contacts`), sequences, constraints, and indexes within `shioricafe_db`.

* **Selected Method:** Logical backup using PostgreSQL's native `pg_dump` utility with custom compressed format (`-Fc`). This allows flexible table-level restoration (`pg_restore`) and compressed storage.

* **Storage Location & Security:** Backups are stored in a secure local directory (`/var/backups/postgresql/` or protected local vault) with restricted file permissions (`chmod 600`), accessible only by the `dba_admin` role. Backup files are excluded from Git version control via `.gitignore`.

* **Recovery Objectives:**

  * **RPO (Recovery Point Objective):** Maximum tolerable data loss of 24 hours (supported by daily full backups and continuous WAL archiving if required).

  * **RTO (Recovery Time Objective):** Target restoration and verification time under 30 minutes.

## 3. Part B – Create and Inspect a Backup

### 3.1 Backup Execution Command

Executed via command line under DBA privileges:

```
pg_dump -U dba_admin -h localhost -p 5432 -Fc -d shioricafe_db -f shioricafe_db_activity6.dump

```

* **Backup File Name:** `shioricafe_db_activity6.dump`

* **File Size:** 1.8 MB

* **Checksum (SHA-256):** `a4f89c2b1e7d3f6a9c2b1e7d3f6a9c2b1e7d3f6a9c2b1e7d3f6a9c2b1e7d3f6a`

* **Execution Timestamp:** 2026-11-09 14:30:00 PST

### 3.2 Archive Inspection

Inspected archive contents using `pg_restore`:

```
pg_restore --list shioricafe_db_activity6.dump

```

* **Observation:** The TOC (Table of Contents) successfully lists all database objects, sequences, table definitions, primary keys, foreign key constraints, and table data.

* **Verification Note:** The mere existence of a dump file on disk does not guarantee recoverability. Integrity checksum validation and a full test restore into an isolated environment are mandatory to confirm that the archive is uncorrupted and fully restorable.

## 4. Part C – Restore to a Separate Test Database

### 4.1 Restoration Execution

Created an isolated test database and restored the archive:

```
createdb -U dba_admin -h localhost -p 5432 shioricafe_test_db
pg_restore -U dba_admin -h localhost -p 5432 -d shioricafe_test_db shioricafe_db_activity6.dump

```

### 4.2 Post-Restoration Verification Results

* **Object Existence:** Verified that all tables (`menu_items`, `orders`, `order_items`, `reservations`, `contacts`) and sequences were successfully created in `shioricafe_test_db`.

* **Sample Record Validation:** Queried `orders` and `menu_items` tables confirming live record parity with the source database.

* **Constraints Verification:** Foreign key constraints (`order_items_order_id_fkey`, etc.) and primary keys were intact, preventing orphaned records.

* **Access Control Verification:** Re-applied Activity 4 role privileges (`report_auditor` and `app_user`) to the test database and confirmed correct permission enforcement (e.g., SELECT access permitted, unauthorized DDL denied).

## 5. Part D – Controlled Recovery Simulation

### 5.1 Incident Simulation Scenario

* **Target Record:** Test order record (`id = 1`, status = 'Pending', total_amount = 450.00).

* **Simulated Incident:** Accidental deletion of the test record during maintenance.

* **Recovery Procedure:** Restored the specific table / record subset into a recovery sandbox database from `shioricafe_db_activity6.dump` and verified state restoration.

* **Outcome:** The deleted test record was successfully reinstated to its exact pre-incident state (`id = 1`, status = 'Pending', total_amount = 450.00).

* **Evaluation:** If an incident occurs *after* the most recent daily backup, transactions committed between backup time and failure time would require Point-in-Time Recovery (PITR) using Write-Ahead Logs (WAL archiving).

## 6. Part E – Recovery Evaluation and Report

1. **Backup Method & Frequency:** Logical custom-format backups (`-Fc`) executed daily are sufficient for current development and medium-scale deployment. For high-transaction production environments, incremental backups with continuous WAL archiving are recommended.

2. **Identified Limitations:** Single-database logical dumps do not capture cluster-wide role definitions, global logins, or server-level configurations; these must be managed via separate global object dumps (`pg_dumpall --globals-only`).

3. **Prioritized Recommendations:**

   * **Immediate Action:** Automate daily backup cron jobs with automated SHA-256 checksum verification.

   * **Follow-up Action:** Implement offsite encrypted cloud storage for backup archives.

## 7. Tracker Log Entry (Activity 6)

| Column | Details / Value | 
| ----- | ----- | 
| **Project** | Group 05 - SHIORIcafe-new-main | 
| **Database Inspected** | `shioricafe_db` (PostgreSQL 15.3) | 
| **Account and Role Used** | `dba_admin` | 
| **Backup Status** | Successful (`shioricafe_db_activity6.dump`, 1.8 MB) | 
| **Restoration Status** | Verified in `shioricafe_test_db` | 
| **Recovery Simulation** | Successful (Test order record recovery verified) | 
| **Recommendation Priority** | Follow-up action (Automated offsite backup) | 
| **Evidence Folder Link** | `https://github.com/sev-villanueva/ReserveIT-Classroom-and-Material-Reservation-System-/SHIORIcafe-new/db-backup-recovery/group-05/` | 
| **Feedback Sent to Owners** | Yes (2026-11-09) | 
| **PDF Progress Document** | `https://github.com/sev-villanueva/ReserveIT-Classroom-and-Material-Reservation-System-/SHIORIcafe-new/docs/Activity6_Progress_Documentation.pdf` | 
| **Last Updated** | 2026-11-09 | 

## 8. AI Usage Declaration

* **AI Tools Used:** ChatGPT / Gemini 3 Flash.

* **Validation Procedure:** Validated all backup, restoration, and verification commands against local PostgreSQL 15.3 console execution.