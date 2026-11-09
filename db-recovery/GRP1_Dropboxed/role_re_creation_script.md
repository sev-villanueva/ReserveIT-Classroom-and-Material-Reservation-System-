-- =============================================================================
-- COMP 018: Activity 6 - Post-Restore Role & Privilege Re-application Script
-- Database: group1_dropboxed_db_test
-- Description: Re-creates Activity 4 cluster roles and object grants
-- =============================================================================

-- 1. Create Group Roles (NOLOGIN)
DO $$
BEGIN
   IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'app_runtime_grp') THEN
      CREATE ROLE app_runtime_grp NOLOGIN;
   END IF;
   IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'app_readonly_grp') THEN
      CREATE ROLE app_readonly_grp NOLOGIN;
   END IF;
END $$;

-- 2. Create Login Accounts
DO $$
BEGIN
   IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'app_runtime') THEN
      CREATE ROLE app_runtime LOGIN PASSWORD 'AppRuntimePass2026!';
   END IF;
   IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'report_auditor') THEN
      CREATE ROLE report_auditor LOGIN PASSWORD 'AuditorPass2026!';
   END IF;
END $$;

-- 3. Assign Role Memberships
GRANT app_runtime_grp TO app_runtime;
GRANT app_readonly_grp TO report_auditor;

-- 4. Database Connection & Schema Access
GRANT CONNECT ON DATABASE group1_dropboxed_db_test TO app_runtime_grp, app_readonly_grp;
GRANT USAGE ON SCHEMA public TO app_runtime_grp, app_readonly_grp;

-- 5. Table & Sequence Grants
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO app_runtime_grp;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO app_readonly_grp;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO app_runtime_grp;