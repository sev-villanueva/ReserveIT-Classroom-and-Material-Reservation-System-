-- =============================================================================
-- COMP 018: Activity 5 - Routine Maintenance & Monitoring Script
-- Target Database: school_event_db
-- =============================================================================

-- 1. Database Health & Connection Monitoring
SELECT version();
SELECT current_database(), pg_size_pretty(pg_database_size(current_database()));

SELECT pid, usename, state, wait_event_type, wait_event, query_start, query
FROM pg_stat_activity
WHERE datname = current_database()
ORDER BY query_start NULLS LAST;

-- 2. Maintenance Operations
ANALYZE public.user_accounts;
ANALYZE public.events;
ANALYZE public.participants;

VACUUM (VERBOSE, ANALYZE) public.attendance;
VACUUM (VERBOSE, ANALYZE) public.audit_logs;

-- 3. Query Performance Analysis
EXPLAIN (ANALYZE, BUFFERS)
SELECT a.status, COUNT(a.id) 
FROM attendance a 
JOIN events e ON a.event_id = e.id 
WHERE e.id = 1 
GROUP BY a.status;

-- 4. Proposed Tuning Index
CREATE INDEX IF NOT EXISTS idx_attendance_event_id ON attendance(event_id);