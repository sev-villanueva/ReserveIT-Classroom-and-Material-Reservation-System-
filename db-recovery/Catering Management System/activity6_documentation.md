# COMP 018 – Database Administration

## Activity 6: Database Backup, Restoration, and Disaster Recovery Plan

* **Group Number:** Group 7

* **Target Repository:** `catering-management-system-main`

* **Database System:** PostgreSQL 15+ / 18.x

* **Target Database:** `catering_management_db`

* **Document Version:** 1.0 (Production Release)

## 1. Executive Summary & Objective

This document outlines the complete backup, restoration, and disaster recovery (DR) procedures for the **Catering Management System** (`catering_management_db`). As a database-driven web application managing customer profiles, sensitive financial transactions, catering packages, and event inventory, establishing robust backup policies ensures business continuity and compliance with data integrity regulations.

## 2. Backup Strategy & Schedule

To balance performance overhead against Recovery Point Objectives (RPO) and Recovery Time Objectives (RTO), we implement a hybrid backup strategy combining physical/logical dumps and continuous Write-Ahead Log (WAL) archiving.

| Backup Type | Frequency | Retention Period | Storage Location | Target RPO / RTO | 
| ----- | ----- | ----- | ----- | ----- | 
| **Full Logical Backup** | Daily at 02:00 UTC | 30 Days | Secure Offsite Object Storage (S3 / Encrypted NAS) | RPO: 24 Hours / RTO: 30 Mins | 
| **Incremental / WAL Archive** | Continuous (Archived hourly) | 7 Days | Dedicated Backup Partition (`/var/lib/postgresql/wal_archive`) | RPO: < 1 Hour / RTO: 45 Mins | 
| **Schema-Only Snapshot** | Weekly (Sundays) | Indefinite | Version-Controlled Repository (`/database/schema.sql`) | N/A (Version Recovery) | 

## 3. Operational Backup Procedures

### 3.1 Creating a Full Custom-Format Backup (`.dump`)

The compressed custom format (`-Fc`) is recommended for production environments as it allows flexible restoration and selective table recovery using `pg_restore`.

```bash
# Execute via command line with administrative privileges
pg_dump -U postgres -h localhost -p 5432 -d catering_management_db -Fc -f /backups/catering_management_db_$(date +%Y%m%d_%H%M%S).dump
```

### 3.2 Creating a Plain-Text SQL Script Backup

Useful for text-based analysis, auditing, or quick inspection of database definitions and seed rows.

```bash
pg_dump -U postgres -h localhost -p 5432 -d catering_management_db --clean --if-exists > /backups/catering_management_db_schema_seed.sql
```

## 4. Disaster Recovery & Restoration Runbook

In the event of accidental data corruption, hardware failure, or botched migration scripts, execute the following disaster recovery workflow.

### Scenario A: Full Database Restoration from a Custom Dump

1. **Terminate active connections** to prevent write locks during recovery:

   ```sql
   SELECT pg_terminate_backend(pid) 
   FROM pg_stat_activity 
   WHERE datname = 'catering_management_db' AND pid <> pg_backend_pid();
   ```

2. **Drop and recreate the target database** (if performing a clean recovery):

   ```bash
   dropdb -U postgres catering_management_db
   createdb -U postgres catering_management_db
   ```

3. **Restore the database using `pg_restore`**:

   ```bash
   pg_restore -U postgres -h localhost -d catering_management_db --verbose /backups/catering_management_db_20261109_020000.dump
   ```

### Scenario B: Point-in-Time Recovery (PITR) via WAL Archives

If transactions were corrupted at a specific timestamp (e.g., `2026-11-09 14:35:00 UTC`), administrators can recover up to the exact second preceding the failure:

1. Restore the latest full base backup.

2. Configure `recovery.conf` (or `postgresql.conf` parameters in PostgreSQL 15+):

   ```ini
   restore_command = 'cp /var/lib/postgresql/wal_archive/%f "%p"'
   recovery_target_time = '2026-11-09 14:35:00'
   recovery_target_action = 'pause'
   ```

3. Restart the PostgreSQL service to initiate recovery playback.

## 5. Backup Verification and Integrity Testing Protocol

Backups are only as good as their restoration capability. The team executes a monthly verification drill:

1. **Isolate Test Environment:** Spin up an ephemeral test container running PostgreSQL 18.x.

2. **Execute Restoration:** Import the latest production `.dump` file into `group08_cateringdb_test`.

3. **Run Automated Integrity Queries:**

   ```sql
   -- Verify row count thresholds and foreign key integrity
   SELECT 'customer' AS tbl, COUNT(*) FROM customer
   UNION ALL
   SELECT 'reservation', COUNT(*) FROM reservation
   UNION ALL
   SELECT 'payment', COUNT(*) FROM payment;
   ```

4. **Log Results:** Record validation success rates in the Activity 6 verification log.

## 6. Security, Encryption, and Access Control

* **At-Rest Encryption:** All backup directories are encrypted using AES-256 via LUKS or cloud-native bucket policies.

* **Credential Isolation:** Backup automation scripts fetch database superuser passwords securely from restricted environment files (`.pgpass`), prohibiting plaintext password exposure in shell history.

* **Least Privilege:** The backup execution agent operates under a dedicated system role (`postgres_backup_agent`) with `pg_read_all_settings` and `pg_read_all_stats` system privileges rather than full root access.

## 7. Activity 6 Tracker Sign-Off

| Metric / Parameter | Value / Status | 
| ----- | ----- | 
| **Target Project** | Catering Management System (`catering-management-system-main`) | 
| **Backup Script Path** | `database/backups/` | 
| **Verification Status** | Passed (Simulated Test Restore on `group08_cateringdb_test`) | 
| **Last Audit Date** | 2026-11-09 | 
| **Approved By** | Database Administration Group 7 | 
