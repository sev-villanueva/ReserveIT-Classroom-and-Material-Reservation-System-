-- =============================================================================
-- COMP 018: Activity 4 - Access Control & Role Management Script
-- Target Database: healthbridge_db
-- =============================================================================

-- Step 1: Clean up existing test roles if re-running
DROP ROLE IF EXISTS hbcms_app_user;
DROP ROLE IF EXISTS hbcms_auditor;
DROP ROLE IF EXISTS hbcms_staff;
DROP ROLE IF EXISTS hbcms_dba;
DROP ROLE IF EXISTS hbcms_app_grp;
DROP ROLE IF EXISTS hbcms_readonly_grp;
DROP ROLE IF EXISTS hbcms_dataentry_grp;

-- Step 2: Create Group Roles (NOLOGIN)
CREATE ROLE hbcms_app_grp NOLOGIN;
CREATE ROLE hbcms_readonly_grp NOLOGIN;
CREATE ROLE hbcms_dataentry_grp NOLOGIN;

-- Step 3: Create Login Accounts
CREATE ROLE hbcms_dba WITH LOGIN CREATEDB CREATEROLE PASSWORD 'HBCMSAdmin2026!';
CREATE ROLE hbcms_app_user WITH LOGIN PASSWORD 'HBCMSAppPass2026!';
CREATE ROLE hbcms_auditor WITH LOGIN PASSWORD 'HBCMSAuditor2026!';
CREATE ROLE hbcms_staff WITH LOGIN PASSWORD 'HBCMSStaffPass2026!';

-- Step 4: Role Memberships
GRANT hbcms_app_grp TO hbcms_app_user;
GRANT hbcms_readonly_grp TO hbcms_auditor;
GRANT hbcms_dataentry_grp TO hbcms_staff;

-- Step 5: Schema Privileges & Hardening
REVOKE ALL ON SCHEMA public FROM PUBLIC;
GRANT CONNECT ON DATABASE healthbridge_db TO hbcms_app_grp, hbcms_readonly_grp, hbcms_dataentry_grp;
GRANT USAGE ON SCHEMA public TO hbcms_app_grp, hbcms_readonly_grp, hbcms_dataentry_grp;

-- Step 6: Object Privileges
-- App Runtime Privileges
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO hbcms_app_grp;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO hbcms_app_grp;

-- Read-Only Auditor Privileges
GRANT SELECT ON ALL TABLES IN SCHEMA public TO hbcms_readonly_grp;

-- Data Entry Specialist Privileges
GRANT SELECT, INSERT ON TABLE public.patients, public.appointments TO hbcms_dataentry_grp;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO hbcms_dataentry_grp;