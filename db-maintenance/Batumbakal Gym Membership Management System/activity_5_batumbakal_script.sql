-- =============================================================================
-- COMP 018: Activity 5 - Routine Maintenance & Performance Script
-- Target Database: batumbakal_gym_db
-- Run with DBA Privileges (e.g., dba_admin)
-- =============================================================================

-- 1. Database Health & Activity Checks
SELECT version();
SELECT current_database(), pg_size_pretty(pg_database_size(current_database()));

-- Active Connections Check
SELECT pid, usename, state, wait_event_type, wait_event, query_start, query
FROM pg_stat_activity
WHERE datname = current_database()
ORDER BY query_start NULLS LAST;

-- 2. Maintenance Tasks (Run as standalone statements, not inside transaction block)
ANALYZE public.members;
ANALYZE public.trainers;
ANALYZE public.membership_plans;
ANALYZE public.memberships;
ANALYZE public.payments;
ANALYZE public.classes;
ANALYZE public.class_enrollments;
ANALYZE public.attendance;

VACUUM (VERBOSE, ANALYZE) public.members;
VACUUM (VERBOSE, ANALYZE) public.memberships;
VACUUM (VERBOSE, ANALYZE) public.payments;
VACUUM (VERBOSE, ANALYZE) public.attendance;

-- 3. Query Performance Analysis
EXPLAIN (ANALYZE, BUFFERS)
SELECT m.member_id, m.first_name, m.last_name, ms.status, pl.plan_name
FROM members m
JOIN memberships ms ON m.member_id = ms.member_id
JOIN membership_plans pl ON ms.plan_id = pl.plan_id
WHERE ms.status = 'Active';

-- 4. Recommended Performance Index Tuning (Optional execution based on evaluation)
CREATE INDEX IF NOT EXISTS idx_memberships_status ON memberships(status);
CREATE INDEX IF NOT EXISTS idx_memberships_member_id ON memberships(member_id);
CREATE INDEX IF NOT EXISTS idx_memberships_plan_id ON memberships(plan_id);
