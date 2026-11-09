-- =============================================================================
-- COMP 018: Activity 4 - Access Control & Role Management Script
-- Target Database: pawpaw_db
-- =============================================================================

-- Step 1: Clean up existing test roles if re-running
DROP ROLE IF EXISTS pawpaw_app_user;
DROP ROLE IF EXISTS pawpaw_auditor;
DROP ROLE IF EXISTS pawpaw_staff;
DROP ROLE IF EXISTS pawpaw_dba;
DROP ROLE IF EXISTS pawpaw_app_grp;
DROP ROLE IF EXISTS pawpaw_readonly_grp;
DROP ROLE IF EXISTS pawpaw_dataentry_grp;

-- Step 2: Create Group Roles (NOLOGIN)
CREATE ROLE pawpaw_app_grp NOLOGIN;
CREATE ROLE pawpaw_readonly_grp NOLOGIN;
CREATE ROLE pawpaw_dataentry_grp NOLOGIN;

-- Step 3: Create Login Accounts
CREATE ROLE pawpaw_dba WITH LOGIN CREATEDB CREATEROLE PASSWORD 'PawpawAdmin2026!';
CREATE ROLE pawpaw_app_user WITH LOGIN PASSWORD 'PawpawAppPass2026!';
CREATE ROLE pawpaw_auditor WITH LOGIN PASSWORD 'PawpawAuditor2026!';
CREATE ROLE pawpaw_staff WITH LOGIN PASSWORD 'PawpawStaffPass2026!';

-- Step 4: Role Memberships
GRANT pawpaw_app_grp TO pawpaw_app_user;
GRANT pawpaw_readonly_grp TO pawpaw_auditor;
GRANT pawpaw_dataentry_grp TO pawpaw_staff;

-- Step 5: Schema Privileges & Hardening
REVOKE ALL ON SCHEMA public FROM PUBLIC;
GRANT CONNECT ON DATABASE pawpaw_db TO pawpaw_app_grp, pawpaw_readonly_grp, pawpaw_dataentry_grp;
GRANT USAGE ON SCHEMA public TO pawpaw_app_grp, pawpaw_readonly_grp, pawpaw_dataentry_grp;

-- Step 6: Object Privileges
-- App Runtime Privileges
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO pawpaw_app_grp;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO pawpaw_app_grp;

-- Read-Only Auditor Privileges
GRANT SELECT ON ALL TABLES IN SCHEMA public TO pawpaw_readonly_grp;

-- Data Entry Specialist Privileges
GRANT SELECT, INSERT ON TABLE public.clients, public.patients, public.appointments TO pawpaw_dataentry_grp;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO pawpaw_dataentry_grp;