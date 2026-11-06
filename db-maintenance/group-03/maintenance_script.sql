-- Activity 5: Database Maintenance & Monitoring Script
-- Group 03 | Pawpaw Clinic Database

-- 1. Health & Activity Checks
SELECT version();
SELECT current_database(), pg_size_pretty(pg_database_size(current_database()));
SELECT datname, numbackends FROM pg_stat_database WHERE datname = current_database();
SELECT pid, usename, state, query_start, query FROM pg_stat_activity WHERE datname = current_database() ORDER BY query_start NULLS LAST;

-- 2. Routine Maintenance Operations
ANALYZE;
VACUUM (VERBOSE, ANALYZE) public.patient;

-- 3. Query Performance Analysis
EXPLAIN SELECT * FROM public.patient WHERE email = 'student@pawpaw.test';
