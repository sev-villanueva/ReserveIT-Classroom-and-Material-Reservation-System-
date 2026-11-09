-- =============================================================================
-- COMP 018: Activity 6 - Post-Restore Role & Privilege Re-application Script
-- Database: healthbridge_db_test
-- Description: Re-creates Activity 4 cluster roles and object grants
-- =============================================================================

-- 1. Create Group Roles (NOLOGIN)
DO $$
BEGIN
   IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'hbcms_app_grp') THEN
      CREATE ROLE hbcms_app_grp NOLOGIN;
   END IF;
   IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'hbcms_readonly_grp') THEN
      CREATE ROLE hbcms_readonly_grp NOLOGIN;
   END IF;
END $$;

-- 2. Create Login Accounts
DO $$
BEGIN
   IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'hbcms_app_user') THEN
      CREATE ROLE hbcms_app_user LOGIN PASSWORD 'HBCMSAppPass2026!';
   END IF;
   IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'hbcms_auditor') THEN
      CREATE ROLE hbcms_auditor LOGIN PASSWORD 'HBCMSAuditor2026!';
   END IF;
END $$;

-- 3. Assign Role Memberships
GRANT hbcms_app_grp TO hbcms_app_user;
GRANT hbcms_readonly_grp TO hbcms_auditor;

-- 4. Database Connection & Schema Access
GRANT CONNECT ON DATABASE healthbridge_db_test TO hbcms_app_grp, hbcms_readonly_grp;
GRANT USAGE ON SCHEMA public TO hbcms_app_grp, hbcms_readonly_grp;

-- 5. Table & Sequence Grants
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO hbcms_app_grp;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO hbcms_readonly_grp;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO hbcms_app_grp;