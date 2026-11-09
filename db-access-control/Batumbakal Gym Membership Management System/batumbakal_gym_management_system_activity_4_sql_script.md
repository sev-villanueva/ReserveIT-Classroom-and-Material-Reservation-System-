-- =============================================================================
-- COMP 018: Activity 4 - Access Control & Role Management Script
-- Target Database: batumbakal_gym_db
-- System: Batumbakal Gym Management System
-- =============================================================================

-- Step 1: Clean up existing test roles if re-running
DROP ROLE IF EXISTS gym_app_user;
DROP ROLE IF EXISTS audit_officer;
DROP ROLE IF EXISTS frontdesk_staff;
DROP ROLE IF EXISTS dba_admin;
DROP ROLE IF EXISTS app_runtime_grp;
DROP ROLE IF EXISTS app_readonly_grp;
DROP ROLE IF EXISTS data_entry_grp;

-- -----------------------------------------------------------------------------
-- Step 2: Create Group Roles (NOLOGIN)
-- -----------------------------------------------------------------------------
CREATE ROLE app_runtime_grp NOLOGIN;
CREATE ROLE app_readonly_grp NOLOGIN;
CREATE ROLE data_entry_grp NOLOGIN;

-- -----------------------------------------------------------------------------
-- Step 3: Create Login Accounts with Secure Passwords
-- -----------------------------------------------------------------------------
CREATE ROLE dba_admin WITH LOGIN CREATEDB CREATEROLE PASSWORD 'SecureAdminPass2026!';
CREATE ROLE gym_app_user WITH LOGIN PASSWORD 'GymAppPass2026!';
CREATE ROLE audit_officer WITH LOGIN PASSWORD 'AuditorPass2026!';
CREATE ROLE frontdesk_staff WITH LOGIN PASSWORD 'DataEntryPass2026!';

-- -----------------------------------------------------------------------------
-- Step 4: Assign Role Memberships
-- -----------------------------------------------------------------------------
GRANT app_runtime_grp TO gym_app_user;
GRANT app_readonly_grp TO audit_officer;
GRANT data_entry_grp TO frontdesk_staff;

-- -----------------------------------------------------------------------------
-- Step 5: Schema Privileges & Security Hardening
-- -----------------------------------------------------------------------------
REVOKE ALL ON SCHEMA public FROM PUBLIC;
GRANT CONNECT ON DATABASE batumbakal_gym_db TO app_runtime_grp, app_readonly_grp, data_entry_grp;
GRANT USAGE ON SCHEMA public TO app_runtime_grp, app_readonly_grp, data_entry_grp;

-- -----------------------------------------------------------------------------
-- Step 6: Object-Level Privileges
-- -----------------------------------------------------------------------------

-- App Runtime Privileges (Spring Boot Backend)
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO app_runtime_grp;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO app_runtime_grp;

-- Read-Only Auditor Privileges
GRANT SELECT ON ALL TABLES IN SCHEMA public TO app_readonly_grp;

-- Front Desk Staff Privileges (Restricted DML on operational attendance/enrollments/members)
GRANT SELECT, INSERT, UPDATE ON TABLE public.members, public.attendance, public.class_enrollments TO data_entry_grp;
GRANT SELECT ON TABLE public.trainers, public.membership_plans, public.memberships, public.payments, public.classes TO data_entry_grp;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO data_entry_grp;