-- =============================================================================
-- COMP 018: Activity 4 - Access Control & Role Management Script
-- Target Repository: School_Event_Management_Web_Appli-main
-- Target Database: school_event_db
-- =============================================================================

-- Step 1: Cleanup Existing Roles
DROP ROLE IF EXISTS school_app_runtime;
DROP ROLE IF EXISTS school_auditor;
DROP ROLE IF EXISTS school_staff_user;
DROP ROLE IF EXISTS school_dba_admin;
DROP ROLE IF EXISTS school_app_runtime_grp;
DROP ROLE IF EXISTS school_readonly_grp;
DROP ROLE IF EXISTS school_staff_grp;

-- Step 2: Create Group Roles (NOLOGIN)
CREATE ROLE school_app_runtime_grp NOLOGIN;
CREATE ROLE school_readonly_grp NOLOGIN;
CREATE ROLE school_staff_grp NOLOGIN;

-- Step 3: Create Login Accounts
CREATE ROLE school_dba_admin WITH LOGIN CREATEDB CREATEROLE PASSWORD 'SecureSchoolAdmin2026!';
CREATE ROLE school_app_runtime WITH LOGIN PASSWORD 'SchoolAppPass2026!';
CREATE ROLE school_auditor WITH LOGIN PASSWORD 'AuditorSchoolPass2026!';
CREATE ROLE school_staff_user WITH LOGIN PASSWORD 'StaffPass2026!';

-- Step 4: Assign Role Memberships
GRANT school_app_runtime_grp TO school_app_runtime;
GRANT school_readonly_grp TO school_auditor;
GRANT school_staff_grp TO school_staff_user;

-- Step 5: Restrict Schema Access
REVOKE ALL ON SCHEMA public FROM PUBLIC;
GRANT CONNECT ON DATABASE school_event_db TO school_app_runtime_grp, school_readonly_grp, school_staff_grp;
GRANT USAGE ON SCHEMA public TO school_app_runtime_grp, school_readonly_grp, school_staff_grp;

-- Step 6: Object Privileges
-- Application Runtime
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO school_app_runtime_grp;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO school_app_runtime_grp;

-- Read-Only Auditor
GRANT SELECT ON ALL TABLES IN SCHEMA public TO school_readonly_grp;

-- Staff Coordinator
GRANT SELECT, INSERT, UPDATE ON TABLE public.events, public.participants, public.attendance TO school_staff_grp;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO school_staff_grp;