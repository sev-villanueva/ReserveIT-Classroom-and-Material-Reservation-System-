-- ReserveIT database roles (least privilege). Run ONCE by a PostgreSQL superuser, after the empty database exists:
--
--     python manage.py setup-roles
--
-- manage.py replaces __DBNAME__ with your quoted database name and the four password placeholders
-- (owner_pw, app_pw, report_pw, dba_pw) with the DB_*_PASSWORD values from your .env file, so no password is
-- stored in this file or in Git. To run it by hand in pgAdmin instead, replace those five items yourself,
-- for example __DBNAME__ with "ReserveIT" and each placeholder with a quoted password such as 'my_password'.
--
-- Account design
--   reserveit_owner     owns the database and tables; used only for setup (init-db, seed, reset-db). Not a superuser.
--   reserveit_app       the web application's account. Member of app_runtime_grp.
--   reserveit_reporter  read-only reporting account. Member of app_readonly_grp.
--   reserveit_dba       maintenance account. Member of app_admin_grp.
-- None of these accounts is a superuser and none can create roles or databases.
-- Table-level privileges are granted afterwards by database/grants.sql.

DO $$
BEGIN
    -- Group roles: hold privileges, cannot log in
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'app_runtime_grp') THEN CREATE ROLE app_runtime_grp NOLOGIN; END IF;
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'app_readonly_grp') THEN CREATE ROLE app_readonly_grp NOLOGIN; END IF;
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'app_admin_grp')    THEN CREATE ROLE app_admin_grp NOLOGIN; END IF;

    -- Login accounts (re-running this script also resets their passwords to match .env)
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'reserveit_owner') THEN
        CREATE ROLE reserveit_owner LOGIN PASSWORD %(owner_pw)s NOSUPERUSER NOCREATEDB NOCREATEROLE;
    ELSE
        ALTER ROLE reserveit_owner LOGIN PASSWORD %(owner_pw)s NOSUPERUSER NOCREATEDB NOCREATEROLE;
    END IF;
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'reserveit_app') THEN
        CREATE ROLE reserveit_app LOGIN PASSWORD %(app_pw)s NOSUPERUSER NOCREATEDB NOCREATEROLE;
    ELSE
        ALTER ROLE reserveit_app LOGIN PASSWORD %(app_pw)s NOSUPERUSER NOCREATEDB NOCREATEROLE;
    END IF;
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'reserveit_reporter') THEN
        CREATE ROLE reserveit_reporter LOGIN PASSWORD %(report_pw)s NOSUPERUSER NOCREATEDB NOCREATEROLE;
    ELSE
        ALTER ROLE reserveit_reporter LOGIN PASSWORD %(report_pw)s NOSUPERUSER NOCREATEDB NOCREATEROLE;
    END IF;
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'reserveit_dba') THEN
        CREATE ROLE reserveit_dba LOGIN PASSWORD %(dba_pw)s NOSUPERUSER NOCREATEDB NOCREATEROLE;
    ELSE
        ALTER ROLE reserveit_dba LOGIN PASSWORD %(dba_pw)s NOSUPERUSER NOCREATEDB NOCREATEROLE;
    END IF;
END
$$;

-- Memberships: each login account gets exactly one group
GRANT app_runtime_grp TO reserveit_app;
GRANT app_readonly_grp TO reserveit_reporter;
GRANT app_admin_grp TO reserveit_dba;

-- The owner role owns the database, so it can create the tables and the btree_gist extension
ALTER DATABASE __DBNAME__ OWNER TO reserveit_owner;

-- Nobody connects unless they are given CONNECT below, and nobody can create objects in the public schema
REVOKE ALL ON DATABASE __DBNAME__ FROM PUBLIC;
GRANT CONNECT ON DATABASE __DBNAME__ TO reserveit_owner, app_runtime_grp, app_readonly_grp, app_admin_grp;
REVOKE CREATE ON SCHEMA public FROM PUBLIC;
