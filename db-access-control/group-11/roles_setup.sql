-- Activity 4: Database Access Control Script
-- Group 11 | ReserveIT System

-- 1. Create Non-Login Group Roles
CREATE ROLE app_readonly_grp NOLOGIN;
CREATE ROLE app_readwrite_grp NOLOGIN;
CREATE ROLE app_admin_grp NOLOGIN;

-- 2. Create Login Accounts with Secure Passwords
CREATE ROLE reserveit_reporter WITH LOGIN PASSWORD 'SecuredReport#2026';
CREATE ROLE reserveit_app WITH LOGIN PASSWORD 'AppRuntimeKey#2026';
CREATE ROLE reserveit_dba WITH LOGIN PASSWORD 'DBAdminMaster#2026';

-- 3. Assign Role Memberships
GRANT app_readonly_grp TO app_readwrite_grp;
GRANT app_readwrite_grp TO app_admin_grp;
GRANT app_readonly_grp TO reserveit_reporter;
GRANT app_readwrite_grp TO reserveit_app;
GRANT app_admin_grp TO reserveit_dba;

-- 4. Grant Database & Schema Permissions
GRANT CONNECT ON DATABASE "ReserveIT" TO app_readonly_grp;
GRANT USAGE ON SCHEMA public TO app_readonly_grp;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO app_readonly_grp;
GRANT INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO app_readwrite_grp;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO app_readwrite_grp;
