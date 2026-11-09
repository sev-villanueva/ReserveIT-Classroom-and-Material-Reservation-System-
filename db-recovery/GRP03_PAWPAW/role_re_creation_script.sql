-- =============================================================================
-- COMP 018: Activity 6 - Post-Restore Role & Privilege Re-application Script
-- Database: pawpaw_db_test
-- Description: Re-creates Activity 4 cluster roles and object grants
-- =============================================================================

-- 1. Create Group Roles (NOLOGIN)
DO $$
BEGIN
   IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'pawpaw_app_grp') THEN
      CREATE ROLE pawpaw_app_grp NOLOGIN;
   END IF;
   IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'pawpaw_readonly_grp') THEN
      CREATE ROLE pawpaw_readonly_grp NOLOGIN;
   END IF;
END $$;

-- 2. Create Login Accounts
DO $$
BEGIN
   IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'pawpaw_app_user') THEN
      CREATE ROLE pawpaw_app_user LOGIN PASSWORD 'PawpawAppPass2026!';
   END IF;
   IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'pawpaw_auditor') THEN
      CREATE ROLE pawpaw_auditor LOGIN PASSWORD 'PawpawAuditor2026!';
   END IF;
END $$;

-- 3. Assign Role Memberships
GRANT pawpaw_app_grp TO pawpaw_app_user;
GRANT pawpaw_readonly_grp TO pawpaw_auditor;

-- 4. Database Connection & Schema Access
GRANT CONNECT ON DATABASE pawpaw_db_test TO pawpaw_app_grp, pawpaw_readonly_grp;
GRANT USAGE ON SCHEMA public TO pawpaw_app_grp, pawpaw_readonly_grp;

-- 5. Table & Sequence Grants
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO pawpaw_app_grp;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO pawpaw_readonly_grp;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO pawpaw_app_grp;