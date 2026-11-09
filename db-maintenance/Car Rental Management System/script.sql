-- =============================================================================
-- COMP 018: Activity 5 - Database Maintenance & Performance Tuning Script
-- Target Database: car_rental_db
-- =============================================================================

-- 1. Update Statistics for Query Optimizer (ANALYZE)
-- Run ANALYZE on core operational tables to refresh planner statistics
ANALYZE VERBOSE public.rental;
ANALYZE VERBOSE public.payment;
ANALYZE VERBOSE public.vehicle;
ANALYZE VERBOSE public.customer;
ANALYZE VERBOSE public.inspection;

-- 2. Reclaim Storage and Remove Dead Tuples (VACUUM)
-- Vacuum high-traffic tables to prevent bloat
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