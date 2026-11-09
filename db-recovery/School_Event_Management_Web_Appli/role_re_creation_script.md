-- =============================================================================
-- COMP 018: Activity 6 - Post-Restore Role & Privilege Re-application Script
-- Database: school_event_db_test
-- =============================================================================

-- 1. Create Group Roles
DO $$
BEGIN
   IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'school_app_runtime_grp') THEN
      CREATE ROLE school_app_runtime_grp NOLOGIN;
   END IF;
   IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'school_readonly_grp') THEN
      CREATE ROLE school_readonly_grp NOLOGIN;
   END IF;
END $$;

-- 2. Create Login Accounts
DO $$
BEGIN
   IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'school_app_runtime') THEN
      CREATE ROLE school_app_runtime LOGIN PASSWORD 'SchoolAppPass2026!';
   END IF;
   IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'school_auditor') THEN
      CREATE ROLE school_auditor LOGIN PASSWORD 'AuditorSchoolPass2026!';
   END IF;
END $$;

-- 3. Assign Role Memberships
GRANT school_app_runtime_grp TO school_app_runtime;
GRANT school_readonly_grp TO school_auditor;

-- 4. Database & Schema Privileges
GRANT CONNECT ON DATABASE school_event_db_test TO school_app_runtime_grp, school_readonly_grp;
GRANT USAGE ON SCHEMA public TO school_app_runtime_grp, school_readonly_grp;

-- 5. Table & Sequence Grants
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO school_app_runtime_grp;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO school_readonly_grp;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO school_app_runtime_grp;