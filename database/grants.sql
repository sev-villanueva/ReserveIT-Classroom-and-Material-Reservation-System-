-- ReserveIT table privileges (least privilege). Run by the owner account after the tables exist:
--
--     python manage.py grants        (init-db and reset-db run this automatically)
--
-- Safe to run again. Re-run it whenever you add a table. The reason for each privilege is explained in
-- docs/access-requirements.md. In short: the web app can only do what its code actually does.

GRANT USAGE ON SCHEMA public TO app_runtime_grp, app_readonly_grp, app_admin_grp;

-- Start from nothing so re-running always gives the same result
REVOKE ALL ON ALL TABLES    IN SCHEMA public FROM app_runtime_grp, app_readonly_grp, app_admin_grp;
REVOKE ALL ON ALL SEQUENCES IN SCHEMA public FROM app_runtime_grp, app_readonly_grp, app_admin_grp;

-- ------------------------------------------------------------------ app_runtime_grp (the web app)
-- Lookup and account tables: create rows, read them, change only the status column. No deletes.
GRANT SELECT, INSERT ON department TO app_runtime_grp;
GRANT SELECT, INSERT ON app_user   TO app_runtime_grp;
GRANT SELECT, INSERT ON staff      TO app_runtime_grp;
GRANT UPDATE (status) ON app_user  TO app_runtime_grp;
GRANT UPDATE (status) ON staff     TO app_runtime_grp;

-- Catalogs staff manage: full create, read, update, delete
GRANT SELECT, INSERT, DELETE ON room     TO app_runtime_grp;
GRANT SELECT, INSERT, DELETE ON material TO app_runtime_grp;
GRANT UPDATE (room_name, building, capacity, room_type, status) ON room TO app_runtime_grp;
GRANT UPDATE (material_name, category, total_quantity, available_quantity) ON material TO app_runtime_grp;

-- Reservations: records are never deleted, only moved between statuses
GRANT SELECT, INSERT ON reservation          TO app_runtime_grp;
GRANT UPDATE (status, staff_id) ON reservation TO app_runtime_grp;
GRANT SELECT, INSERT ON reservation_material TO app_runtime_grp;

-- Penalties: issued once, then only the payment fields change
GRANT SELECT, INSERT ON penalty TO app_runtime_grp;
GRANT UPDATE (paid_status, paid_date) ON penalty TO app_runtime_grp;

-- New ID numbers for the tables the app inserts into (reservation_material has no ID column)
GRANT USAGE ON SEQUENCE department_department_id_seq, app_user_user_id_seq, staff_staff_id_seq,
                        room_room_id_seq, material_material_id_seq, reservation_reservation_id_seq,
                        penalty_penalty_id_seq TO app_runtime_grp;

-- ------------------------------------------------------------------ app_readonly_grp (reports)
GRANT SELECT ON department, room, material, reservation, reservation_material, penalty TO app_readonly_grp;
-- People tables: no email addresses and never the password hashes
GRANT SELECT (user_id, first_name, last_name, role, department_id, status) ON app_user TO app_readonly_grp;
GRANT SELECT (staff_id, full_name, role, status) ON staff TO app_readonly_grp;

-- ------------------------------------------------------------------ app_admin_grp (maintenance)
-- Can correct data but cannot change the structure (only the owner can) or create roles and databases
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO app_admin_grp;
GRANT USAGE, SELECT, UPDATE ON ALL SEQUENCES IN SCHEMA public TO app_admin_grp;
