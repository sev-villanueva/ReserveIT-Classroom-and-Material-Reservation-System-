-- =============================================================================
-- COMP 018: Activity 5 - Routine Maintenance & Performance Script
-- Target Database: pawpaw_db
-- Run with DBA Privileges (e.g., pawpaw_dba)
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
ANALYZE public.clients;
ANALYZE public.patients;
ANALYZE public.appointments;
ANALYZE public.invoices;

VACUUM (VERBOSE, ANALYZE) public.appointments;
VACUUM (VERBOSE, ANALYZE) public.invoices;

-- 3. Query Performance Analysis
EXPLAIN (ANALYZE, BUFFERS)
SELECT a.appointment_id, c.last_name, p.pet_name, a.appointment_date, a.status 
FROM appointments a
JOIN clients c ON a.client_id = c.client_id
JOIN patients p ON a.patient_id = p.patient_id
WHERE a.status = 'Scheduled';

-- 4. Recommended Performance Index Tuning (Optional execution based on evaluation)
CREATE INDEX IF NOT EXISTS idx_appointments_status ON appointments(status);
CREATE INDEX IF NOT EXISTS idx_appointments_client_id ON appointments(client_id);