-- PostgreSQL roles for ReserveIT. Run once as a superuser (e.g. postgres), connected to the project database:
--
--   psql -U postgres -d grp01_appdb -v app_pw="'choose_a_password'" -v report_pw="'choose_another'" -f database/roles_setup.sql
--
-- The passwords are passed on the command line so they never appear in this file or in Git.
-- Group roles (NOLOGIN) hold privileges; login roles are made members of a group.

-- 1. Group roles
SELECT 'CREATE ROLE app_readonly_grp  NOLOGIN' WHERE NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'app_readonly_grp')  \gexec
SELECT 'CREATE ROLE app_readwrite_grp NOLOGIN' WHERE NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'app_readwrite_grp') \gexec
SELECT 'CREATE ROLE app_admin_grp     NOLOGIN' WHERE NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'app_admin_grp')     \gexec

-- 2. Login roles
SELECT format('CREATE ROLE reserveit_app LOGIN PASSWORD %L', :app_pw)
WHERE NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'reserveit_app') \gexec
SELECT format('CREATE ROLE reserveit_reporter LOGIN PASSWORD %L', :report_pw)
WHERE NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'reserveit_reporter') \gexec

-- 3. Privileges on the project database
GRANT CONNECT ON DATABASE :"DBNAME" TO app_readonly_grp, app_readwrite_grp, app_admin_grp;
GRANT USAGE ON SCHEMA public TO app_readonly_grp, app_readwrite_grp, app_admin_grp;

GRANT SELECT ON ALL TABLES IN SCHEMA public TO app_readonly_grp;

GRANT INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO app_readwrite_grp;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO app_readwrite_grp;

GRANT ALL ON ALL TABLES IN SCHEMA public TO app_admin_grp;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO app_admin_grp;

-- Tables created later get the same privileges
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO app_readonly_grp;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT INSERT, UPDATE, DELETE ON TABLES TO app_readwrite_grp;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT USAGE, SELECT ON SEQUENCES TO app_readwrite_grp;

-- 4. Role hierarchy and membership
GRANT app_readonly_grp  TO app_readwrite_grp;   -- read/write also reads
GRANT app_readwrite_grp TO app_admin_grp;       -- admin also reads and writes
GRANT app_readwrite_grp TO reserveit_app;       -- the account the Flask app connects with
GRANT app_readonly_grp  TO reserveit_reporter;  -- reports and dashboards only
