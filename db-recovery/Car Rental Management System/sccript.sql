-- =============================================================================
-- COMP 018: Complete Database Maintenance, Backup, and Recovery Script
-- Project: Car Rental Management System
-- Target Database: car_rental_db
-- =============================================================================

--------------------------------------------------------------------------------
-- PART 1: MAINTENANCE & PERFORMANCE TUNING (Activity 5)
--------------------------------------------------------------------------------

-- 1. Update Statistics for Query Optimizer (ANALYZE)
ANALYZE VERBOSE public.rental;
ANALYZE VERBOSE public.payment;
ANALYZE VERBOSE public.vehicle;
ANALYZE VERBOSE public.customer;
ANALYZE VERBOSE public.inspection;

-- 2. Reclaim Storage and Remove Dead Tuples (VACUUM)
VACUUM VERBOSE public.rental;
VACUUM VERBOSE public.payment;
VACUUM VERBOSE public.vehicle;

-- 3. Check Table and Index Sizes (Storage Audit)
SELECT 
    schemaname AS schema_name,
    relname AS table_name,
    pg_size_pretty(pg_total_relation_size(relid)) AS total_size,
    pg_size_pretty(pg_relation_size(relid)) AS table_size,
    pg_size_pretty(pg_total_relation_size(relid) - pg_relation_size(relid)) AS index_size
FROM pg_stat_user_tables
ORDER BY pg_total_relation_size(relid) DESC;

-- 4. Identify Missing or Unused Indexes
SELECT 
    schemaname,
    relname AS table_name,
    idx_scan AS index_scans,
    pg_size_pretty(pg_relation_size(indexrelid)) AS index_size
FROM pg_stat_user_indexes
WHERE idx_scan = 0
  AND indexrelid NOT IN (
      SELECT conindid FROM pg_constraint WHERE contype IN ('p', 'u')
  )
ORDER BY pg_relation_size(indexrelid) DESC;

-- 5. Monitor Active Connection and Lock States
SELECT 
    pid,
    usename,
    client_addr,
    state,
    query_start,
    query
FROM pg_stat_activity
WHERE datname = 'car_rental_db'
  AND state != 'idle';


--------------------------------------------------------------------------------
-- PART 2: BACKUP, RECOVERY & WAL CONFIGURATION (Activity 6)
--------------------------------------------------------------------------------

-- 1. Verify PITR and Archive Status
SHOW archive_mode;
SHOW archive_command;
SHOW wal_level;

-- 2. Test Restoration Preparation SQL Commands
-- (Run these from your terminal/psql client when performing restoration drills)
/*
   -- Drop and recreate test restoration database:
   DROP DATABASE IF EXISTS car_rental_test_restore;
   CREATE DATABASE car_rental_test_restore;
*/