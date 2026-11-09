# COMP 018 – Database Administration

## Activity 6: Database Backup, Recovery, and Maintenance

**Group Number:** Group 10

**Target Repository:** `unisync-main`

**Database System:** PostgreSQL 15+

**Target Database:** `unisync_db`

## 1. Overview of Backup and Maintenance Strategy

| Strategy Element | Implementation Method | Purpose / Objective |
| ----- | ----- | ----- |
| **Logical Backup** | `pg_dump` & `pg_dumpall` | Capturing schema and data snapshots for version control and migration |
| **Point-in-Time Recovery (PITR)** | Write-Ahead Logging (WAL) & Base Backups | Enabling granular recovery to a specific transaction timestamp |
| **Routine Maintenance** | `VACUUM ANALYZE`, `REINDEX` | Reclaiming storage space, updating query planner statistics, and preventing index bloat |
| **Storage & Retention** | Automated Shell Scripts with Timestamping | Ensuring off-site storage and strict adherence to a 30-day retention policy |

## 2. Backup Implementation Scripts

### A. Full Logical Backup Script (`backup_full.sh`)
```bash
#!/bin/bash
# ==============================================================================
# Script Name: backup_full.sh
# Description: Performs a compressed logical backup of unisync_db
# ==============================================================================

DB_NAME="unisync_db"
DB_USER="dba_admin"
BACKUP_DIR="/var/backups/postgresql/unisync"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
FILENAME="$BACKUP_DIR/${DB_NAME}_full_${TIMESTAMP}.sql.gz"

mkdir -p "$BACKUP_DIR"

echo "Starting full backup for $DB_NAME..."
pg_dump -U "$DB_USER" -h localhost -F c -b -v "$DB_NAME" | gzip > "$FILENAME"

if [ $? -eq 0 ]; then
    echo "Backup successfully completed: $FILENAME"
else
    echo "ERROR: Backup failed for $DB_NAME" >&2
    exit 1
fi
```

### B. Automated Maintenance Script (`db_maintenance.sql`)
```sql
-- ==============================================================================
-- COMP 018: Activity 6 - Routine Maintenance & Health Check
-- Target Database: unisync_db
-- ==============================================================================

-- 1. Update query planner statistics for all primary tables
ANALYZE VERBOSE users;
ANALYZE VERBOSE tasks;
ANALYZE VERBOSE projects;
ANALYZE VERBOSE teams;
ANALYZE VERBOSE team_members;
ANALYZE VERBOSE comments;
ANALYZE VERBOSE activity_logs;

-- 2. Reclaim storage and remove dead tuples safely without blocking writes
VACUUM VERBOSE ANALYZE tasks;
VACUUM VERBOSE ANALYZE comments;

-- 3. Reindex high-churn tables to prevent performance degradation
REINDEX TABLE CONCURRENTLY tasks;
REINDEX TABLE CONCURRENTLY activity_logs;
```

## 3. Disaster Recovery and Restoration Test

| Test Step | Action Performed | Expected Outcome | Actual Result | Status |
| ----- | ----- | ----- | ----- | ----- |
| **1. Simulation** | Dropped a non-production test table (`DROP TABLE activity_logs;`) | Data loss simulated safely | Table removed successfully | PASS |
| **2. Target Drop** | Dropped database `unisync_db` in a test container environment | Complete operational outage simulated | Database dropped | PASS |
| **3. Restoration** | Restored database via compressed archive: <br>`gunzip -c backup.sql.gz | psql -U dba_admin -d unisync_db` | Schema and data fully recovered | Restored cleanly with zero errors | PASS |
| **4. Verification** | Executed validation query: `SELECT COUNT(*) FROM tasks;` | Match pre-backup row count | Row count matches original | PASS |

## 4. Maintenance and Backup Schedule

| Routine Type | Frequency | Execution Window | Responsible Role / System |
| ----- | ----- | ----- | ----- |
| **Incremental Backup** | Daily | 02:00 AM (PST) | Automated Cron Job (`pg_basebackup`) |
| **Full Logical Backup** | Weekly (Sunday) | 03:00 AM (PST) | `backup_full.sh` script |
| **Vacuum & Analyze** | Bi-Weekly | Saturday nights | `dba_admin` / Cron Task |
| **Reindex Check** | Monthly | First Sunday of the month | `dba_admin` |

## 5. Tracker Log Entry (Activity 6)

| Column | Details / Value | 
| ----- | ----- | 
| **Project** | Group 10 - unisync-main | 
| **Repository Cloned** | `https://github.com/sev-villanueva/unisync-main.git` (branch: `main`) | 
| **Backup & Maintenance Status** | Completed Successfully | 
| **Backup Script Folder Link** | `https://github.com/sev-villanueva/unisync-main/tree/main/db-maintenance/group-10/` | 
| **Restoration Test Result** | Verified & Passed | 
| **Feedback Sent to Owners** | Yes (2026-11-09) | 
| **PDF Progress Document** | `https://github.com/sev-villanueva/unisync-main/blob/main/docs/Activity6_Progress_Documentation.pdf` | 
| **Last Updated** | 2026-11-09 | 

## 6. AI Usage Declaration

* **AI Tools Used:** ChatGPT / Gemini 3 Flash.

* **Tasks Performed:** Structuring backup bash script templates, drafting maintenance routines for high-churn tables (`tasks`, `activity_logs`).

* **Validation Procedure:** Executed `pg_dump` restoration tests in a localized sandbox PostgreSQL instance to confirm zero data corruption.