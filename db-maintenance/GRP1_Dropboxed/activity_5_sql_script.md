\-- =============================================================================
\-- COMP 018: Activity 5 - Routine Maintenance & Performance Script
\-- Target Database: group1_dropboxed_db
\-- Run with DBA Privileges (e.g., dba_admin)
\-- =============================================================================

\-- 1. Database Health & Activity Checks
SELECT version();
SELECT current_database(), pg_size_pretty(pg_database_size(current_database()));

\-- Active Connections Check
SELECT pid, usename, state, wait_event_type, wait_event, query_start, query
FROM pg_stat_activity
WHERE datname = current_database()
ORDER BY query_start NULLS LAST;

\-- 2. Maintenance Tasks (Run as standalone statements, not inside transaction block)
ANALYZE public.users;
ANALYZE public.residents;
ANALYZE public.complaints;
ANALYZE public.payments;

VACUUM (VERBOSE, ANALYZE) public.complaints;
VACUUM (VERBOSE, ANALYZE) public.payments;

\-- 3. Query Performance Analysis
EXPLAIN (ANALYZE, BUFFERS)
SELECT c.id, c.title, c.status, r.name
FROM complaints c
JOIN residents r ON c.resident_id = r.id
WHERE c.status = 'Pending';

\-- 4. Recommended Performance Index Tuning (Optional execution based on evaluation)
CREATE INDEX IF NOT EXISTS idx_complaints_status ON complaints(status);
CREATE INDEX IF NOT EXISTS idx_complaints_resident_id ON complaints(resident_id);