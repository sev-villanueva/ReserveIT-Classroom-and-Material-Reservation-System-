-- =============================================================================
-- COMP 018: Activity 4 - Access Control & Role Management Script
-- Target Database: shioricafe_db
-- =============================================================================

-- Step 1: Clean up existing test roles if re-running
DROP ROLE IF EXISTS shiori_app;
DROP ROLE IF EXISTS shiori_auditor;
DROP ROLE IF EXISTS shiori_staff;
DROP ROLE IF EXISTS shiori_dba;
DROP ROLE IF EXISTS cafe_app_grp;
DROP ROLE IF EXISTS cafe_readonly_grp;
DROP ROLE IF EXISTS cafe_staff_grp;

-- Step 2: Create Group Roles (NOLOGIN)
CREATE ROLE cafe_app_grp NOLOGIN;
CREATE ROLE cafe_readonly_grp NOLOGIN;
CREATE ROLE cafe_staff_grp NOLOGIN;

-- Step 3: Create Login Accounts
CREATE ROLE shiori_dba WITH LOGIN CREATEDB CREATEROLE PASSWORD 'ShioriAdmin2026!';
CREATE ROLE shiori_app WITH LOGIN PASSWORD 'CafeAppPass2026!';
CREATE ROLE shiori_auditor WITH LOGIN PASSWORD 'CafeAuditorPass2026!';
CREATE ROLE shiori_staff WITH LOGIN PASSWORD 'BaristaStaffPass2026!';

-- Step 4: Role Memberships
GRANT cafe_app_grp TO shiori_app;
GRANT cafe_readonly_grp TO shiori_auditor;
GRANT cafe_staff_grp TO shiori_staff;

-- Step 5: Schema Privileges & Hardening
REVOKE ALL ON SCHEMA public FROM PUBLIC;
GRANT CONNECT ON DATABASE shioricafe_db TO cafe_app_grp, cafe_readonly_grp, cafe_staff_grp;
GRANT USAGE ON SCHEMA public TO cafe_app_grp, cafe_readonly_grp, cafe_staff_grp;

-- Step 6: Object Privileges
-- Cafe App Group Privileges
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO cafe_app_grp;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO cafe_app_grp;

-- Read-Only Auditor Privileges
GRANT SELECT ON ALL TABLES IN SCHEMA public TO cafe_readonly_grp;

-- Staff Group Privileges
GRANT SELECT, UPDATE ON TABLE public.orders, public.order_items, public.inventory TO cafe_staff_grp;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO cafe_staff_grp;