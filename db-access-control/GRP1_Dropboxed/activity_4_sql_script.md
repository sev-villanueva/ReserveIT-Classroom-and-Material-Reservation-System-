-- =============================================================================
-- COMP 018: Activity 4 - Access Control & Role Management Script
-- Target Database: group1_dropboxed_db
-- =============================================================================

-- Step 1: Clean up existing test roles if re-running
DROP ROLE IF EXISTS app_runtime;
DROP ROLE IF EXISTS report_auditor;
DROP ROLE IF EXISTS resident_entry_user;
DROP ROLE IF EXISTS dba_admin;
DROP ROLE IF EXISTS app_runtime_grp;
DROP ROLE IF EXISTS app_readonly_grp;
DROP ROLE IF EXISTS data_entry_grp;

-- Step 2: Create Group Roles (NOLOGIN)
CREATE ROLE app_runtime_grp NOLOGIN;
CREATE ROLE app_readonly_grp NOLOGIN;
CREATE ROLE data_entry_grp NOLOGIN;

-- Step 3: Create Login Accounts
CREATE ROLE dba_admin WITH LOGIN CREATEDB CREATEROLE PASSWORD 'SecureAdminPass2026!';
CREATE ROLE app_runtime WITH LOGIN PASSWORD 'AppRuntimePass2026!';
CREATE ROLE report_auditor WITH LOGIN PASSWORD 'AuditorPass2026!';
CREATE ROLE resident_entry_user WITH LOGIN PASSWORD 'DataEntryPass2026!';

-- Step 4: Role Memberships
GRANT app_runtime_grp TO app_runtime;
GRANT app_readonly_grp TO report_auditor;
GRANT data_entry_grp TO resident_entry_user;

-- Step 5: Schema Privileges & Hardening
REVOKE ALL ON SCHEMA public FROM PUBLIC;
GRANT CONNECT ON DATABASE group1_dropboxed_db TO app_runtime_grp, app_readonly_grp, data_entry_grp;
GRANT USAGE ON SCHEMA public TO app_runtime_grp, app_readonly_grp, data_entry_grp;

-- Step 6: Object Privileges
-- App Runtime Privileges
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO app_runtime_grp;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO app_runtime_grp;

-- Read-Only Auditor Privileges
GRANT SELECT ON ALL TABLES IN SCHEMA public TO app_readonly_grp;

-- Data Entry Specialist Privileges
GRANT SELECT, INSERT ON TABLE public.residents, public.users TO data_entry_grp;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO data_entry_grp;