-- =============================================================================
-- COMP 018: Activity 6 - Database Backup, Restoration, and Recovery Script
-- Target Database: shioricafe_db
-- Run with DBA Privileges (e.g., dba_admin)
-- =============================================================================

-- 1. Backup Creation (Logical Backup using Custom Format)
-- Note: Execute from terminal / command line using pg_dump
-- pg_dump -U dba_admin -h localhost -p 5432 -Fc -d shioricafe_db -f shioricafe_db_activity6.dump

-- 2. Inspect Archive Contents
-- pg_restore --list shioricafe_db_activity6.dump

-- 3. Restore to a Separate Test Database
-- createdb -U dba_admin -h localhost -p 5432 shioricafe_test_db
-- pg_restore -U dba_admin -h localhost -p 5432 -d shioricafe_test_db shioricafe_db_activity6.dump

-- 4. Post-Restoration Verification Queries (Run against shioricafe_test_db)
SELECT current_database();

-- Verify Table Counts and Objects
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public';

-- Verify Sample Records (Orders & Menu Items)
SELECT o.id, o.order_date, o.total_amount, o.status 
FROM orders o 
LIMIT 5;

-- Verify Constraints (Primary / Foreign Keys)
SELECT conname, contype, relname 
FROM pg_constraint c 
JOIN pg_class r ON c.conrelid = r.oid 
WHERE r.relnamespace = 'public'::regnamespace;

-- 5. Controlled Recovery Simulation (Table-Level / Point-in-Time Recovery Simulation)
-- Step A: Record initial state of test record
SELECT id, status, total_amount FROM orders WHERE id = 1;

-- Step B: Simulate incident (e.g., accidental deletion or erroneous update of test record)
-- DELETE FROM orders WHERE id = 1;

-- Step C: Recovery simulation using selective restore or backup table comparison
-- SELECT * FROM orders WHERE id = 1;
