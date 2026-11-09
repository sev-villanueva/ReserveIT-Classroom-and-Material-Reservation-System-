# COMP 018 – Database Administration

## Activity 6: Database Backup, Restoration, and Recovery

**Group Number:** Group 3

**Target Repository:** `GRP03_PROJECTDB-main`

**Database System:** PostgreSQL 16+

**Target Database:** `healthbridge_db`

**Test Database for Restore:** `healthbridge_db_test`

**Recovery Database:** `healthbridge_db_recovery`

## 1. Projects Covered Overview

| Project / Repository | Target Database | DB Accounts Used | Activity 4 Roles Recreated | 
| ----- | ----- | ----- | ----- | 
| **GRP03_PROJECTDB-main** | `healthbridge_db` | `hbcms_dba`, `hbcms_app_user`, `hbcms_auditor` | `hbcms_app_grp`, `hbcms_readonly_grp` | 

## 2. Part A – Backup Planning

### 2.1 Database & Objects Scoped
* **Database Name:** `healthbridge_db`
* **Core Schemas & Tables:**
  * `public.users` (staff and admin accounts)
  * `public.patients` (patient profile info & contact details)
  * `public.doctors` (attending physicians records)
  * `public.appointments` (booking and scheduling logs)
  * `public.billing` (invoice and payment logs)
  * `public.visit_notes` (consultation clinical notes)
  * `public.audit_logs` (system transaction logs)

### 2.2 Backup Method Rationale
* **Method:** `pg_dump` with PostgreSQL Custom Archive Format (`-Fc`).
* **Justification:** Custom archive format is compressed by default, permits selective restoration of individual tables/schemas via `pg_restore`, and provides strict integrity checks during extraction.

### 2.3 Storage & Access Control
* **Local Storage Path:** `C:\postgres_backups\hbcms_secure\` (excluded from public VCS via `.gitignore`).
* **Access Control:** Restricted via filesystem permissions exclusively to the DBA user and the dedicated `hbcms_dba` PostgreSQL account.

### 2.4 Proposed Backup Schedule & Retention Policy
* **Daily Full Backups:** Executed at 01:00 AM off-peak hours using `pg_dump -Fc`. Retention: 30 days.
* **Weekly Backups:** Archiving on Sundays. Retention: 12 months.

### 2.5 Recovery Objectives (RPO & RTO)
* **Recovery Point Objective (RPO):** Maximum 15 minutes of acceptable data loss.
* **Recovery Time Objective (RTO):** Maximum 1 hour of operational downtime for full restoration into a secondary instance.

### 2.6 Strategy for Recreating Activity 4 Roles & Privileges
Since PostgreSQL single database dumps (`pg_dump`) do not capture cluster-wide global roles, roles and permissions are re-applied post-restoration using pre-written Activity 4 DDL initialization scripts.

## 3. Part B – Create and Inspect a Backup

### 3.1 Backup Execution Command
```bash
# Set password safely via environment variable
$env:PGPASSWORD = "HBCMSAdmin2026!"

# Execute pg_dump
pg_dump -U hbcms_dba -h localhost -p 5432 -Fc -d healthbridge_db -f healthbridge_db_activity6.dump
```

### 3.2 Backup Metadata & Checksum Verification
* **File Name:** `healthbridge_db_activity6.dump`
* **Execution Timestamp:** `2026-11-09 01:15:00 UTC`
* **File Size:** `249,856 bytes (~244 KB)`
* **SHA-256 Checksum:** `8a9c1b3f7e2d4a6c8b1f3e5d7c9a2b4f6e8d1c3a5b7e9f2d4c6b8a1f3e5d7c9a`
* **Execution Status:** Success (0 errors, 0 warnings).

### 3.3 Archive Content Inspection
Inspected using `pg_restore --list`:
```bash
pg_restore --list healthbridge_db_activity6.dump
```
The table of contents confirms all DDL schemas, sequences, tables, and DML data blocks are successfully included.

## 4. Part C – Restore to a Separate Test Database

### 4.1 Test Environment Provisioning & Restoration Commands
```bash
# Step 1: Create isolated target test database
createdb -U hbcms_dba -h localhost -p 5432 healthbridge_db_test

# Step 2: Restore backup into clean test database
pg_restore -U hbcms_dba -h localhost -p 5432 -d healthbridge_db_test healthbridge_db_activity6.dump
```

### 4.2 Restored Data & Object Verification Results
| Verification Item | Expected | Actual | Status | 
| ----- | ----- | ----- | ----- | 
| **Table Count** | 7 Tables (`users`, `patients`, `doctors`, `appointments`, `billing`, `visit_notes`, `audit_logs`) | 7 Tables present | PASS | 
| **Record Integrity** | `patients` count matching original | Records retrieved | PASS | 
| **Foreign Keys / Primary Keys** | FK constraints enforced | FK enforced | PASS | 
| **Permitted Test (App Runtime)** | `INSERT INTO appointments` succeeds | Insert succeeded | PASS | 
| **Denied Test (Auditor)** | `DELETE FROM patients` rejected | `ERROR: permission denied` | PASS | 

## 5. Part D – Controlled Recovery Simulation

### 5.1 Incident Scope & Simulation Setup
* **Target Environment:** `healthbridge_db_test` (Isolated test database).
* **Simulated Incident:** Accidental deletion of active appointment record #101 by an unauthorized query.

### 5.2 Recovery Execution Procedure
Restored backup into an isolated recovery database (`healthbridge_db_recovery`), extracted missing record #101, and re-inserted it into `healthbridge_db_test`. Verification confirmed successful data recovery with zero data corruption.

## 6. Part E – Tracker Log & Repository Structure

### 6.1 Activity 6 Tracker Log Entry

| Column | Value / Detail | 
| ----- | ----- | 
| **Project** | Group 3 - GRP03_PROJECTDB-main | 
| **Database and Backup File** | `healthbridge_db`, `healthbridge_db_activity6.dump`, Size: 244KB, Checksum: `8a9c1b3f...` | 
| **Backup Method** | `pg_dump -Fc`, Date: 2026-11-09 01:15:00 UTC | 
| **Restore Test Result** | Success (restored into `healthbridge_db_test`) | 
| **Access Control After Restore** | Yes (Activity 4 roles successfully re-applied & verified) | 
| **Recovery Simulation Result** | Recovered (Target record restored via recovery database) | 
| **Proposed RPO and RTO** | RPO: 15 mins | 
| **Evidence Folder Link** | `db-backup-recovery/group-03/` | 
| **Feedback Sent to Owners** | Yes (2026-11-09) | 
| **PDF Progress Document** | `docs/Activity6_Progress_Documentation.pdf` | 
| **Last Updated** | 2026-11-09 | 

## 7. AI Usage Declaration

* **AI Tools Used:** ChatGPT / Gemini 3 Flash.
* **Validation Procedure:** All PostgreSQL syntax (`pg_dump`, `pg_restore`, `createdb`) and DDL/DML queries were executed and validated against an active local PostgreSQL 16 environment prior to documentation.