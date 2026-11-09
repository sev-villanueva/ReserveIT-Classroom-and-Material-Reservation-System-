-- =============================================================================
-- COMP 018: Activity 5 - Routine Maintenance & Performance Script
-- Target Database: healthbridge_db
-- Run with DBA Privileges (e.g., hbcms_dba)
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
ANALYZE public.users;
ANALYZE public.patients;
ANALYZE public.appointments;
ANALYZE public.billing;

VACUUM (VERBOSE, ANALYZE) public.appointments;
VACUUM (VERBOSE, ANALYZE) public.billing;

-- 3. Query Performance Analysis
EXPLAIN (ANALYZE, BUFFERS)
SELECT a.id, p.name AS patient_name, d.name AS doctor_name, a.appointment_date, a.status 
FROM appointments a
JOIN patients p ON a.patient_id = p.id
JOIN doctors d ON a.doctor_id = d.id
WHERE a.status = 'Confirmed';

-- 4. Recommended Performance Index Tuning (Optional execution based on evaluation)
CREATE INDEX IF NOT EXISTS idx_appointments_status ON appointments(status);
CREATE INDEX IF NOT EXISTS idx_appointments_patient_id ON appointments(patient_id);