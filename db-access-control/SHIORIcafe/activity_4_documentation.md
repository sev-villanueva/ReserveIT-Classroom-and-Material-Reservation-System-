# COMP 018 – Database Administration

## Activity 4: Database Users, Roles, Privileges, and Access Control

**Group Number:** Group 5

**Target Repository:** `SHIORIcafe-new-main`

**Database System:** PostgreSQL 15+

**Target Database:** `shioricafe_db`

## 1. Projects Set Up Overview

| Project / Repository | Database Name | Primary Database Objects Identified | Setup Result | 
| ----- | ----- | ----- | ----- | 
| **SHIORIcafe-new-main** | `shioricafe_db` | `menu_items`, `orders`, `order_items`, `customers`, `staff`, `inventory`, `payments` | Success | 

## 2. Access Control Plan

| Login Account | Group Role | Application Role Served | Responsibilities | Required Privileges | 
| ----- | ----- | ----- | ----- | ----- | 
| `shiori_dba` | N/A | Database Administrator | Provisioning, schema deployment, role hierarchy management, maintenance | Elevated administrative access (`CREATEDB`, `CREATEROLE`) | 
| `shiori_app` | `cafe_app_grp` | Web Application Backend | Interacting with backend API routes for menu browsing, cart management, and order placement | `CONNECT` on DB, `USAGE` on `public` schema, `SELECT`, `INSERT`, `UPDATE`, `DELETE` on all operational tables, `USAGE` on sequences | 
| `shiori_auditor` | `cafe_readonly_grp` | Sales & Inventory Auditor | Reading financial transactions, sales reports, and stock levels without modification risks | `CONNECT` on DB, `USAGE` on `public` schema, `SELECT` on all tables | 
| `shiori_staff` | `cafe_staff_grp` | Barista / Cashier Staff | Managing active customer orders and updating item stock status | `CONNECT` on DB, `USAGE` on `public` schema, `SELECT`, `UPDATE` on `orders`, `order_items`, and `inventory` | 

## 3. SQL Access Control Implementation Summary

All access-control logic has been implemented using standard PostgreSQL role-based access control (RBAC).

```sql
-- 1. Create NOLOGIN Group Roles
CREATE ROLE cafe_app_grp NOLOGIN;
CREATE ROLE cafe_readonly_grp NOLOGIN;
CREATE ROLE cafe_staff_grp NOLOGIN;

-- 2. Create LOGIN Accounts with Secure Passwords
CREATE ROLE shiori_dba WITH LOGIN CREATEDB CREATEROLE PASSWORD 'ShioriAdmin2026!';
CREATE ROLE shiori_app WITH LOGIN PASSWORD 'CafeAppPass2026!';
CREATE ROLE shiori_auditor WITH LOGIN PASSWORD 'CafeAuditorPass2026!';
CREATE ROLE shiori_staff WITH LOGIN PASSWORD 'BaristaStaffPass2026!';

-- 3. Assign Role Memberships
GRANT cafe_app_grp TO shiori_app;
GRANT cafe_readonly_grp TO shiori_auditor;
GRANT cafe_staff_grp TO shiori_staff;

-- 4. Restrict Default Public Schema Privileges
REVOKE ALL ON SCHEMA public FROM PUBLIC;

-- 5. Grant Explicit Privileges to Group Roles
GRANT CONNECT ON DATABASE shioricafe_db TO cafe_app_grp, cafe_readonly_grp, cafe_staff_grp;
GRANT USAGE ON SCHEMA public TO cafe_app_grp, cafe_readonly_grp, cafe_staff_grp;

-- Cafe App Group
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO cafe_app_grp;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO cafe_app_grp;

-- Read-Only Auditor Group
GRANT SELECT ON ALL TABLES IN SCHEMA public TO cafe_readonly_grp;

-- Staff Group
GRANT SELECT, UPDATE ON TABLE public.orders, public.order_items, public.inventory TO cafe_staff_grp;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO cafe_staff_grp;
```

## 4. Privilege Verification Results

| Account Used | Operation Tested | SQL Statement / Test | Expected Result | Actual Result | Status | 
| ----- | ----- | ----- | ----- | ----- | ----- | 
| `shiori_app` | Query active menu items | `SELECT * FROM menu_items WHERE available = true;` | Allowed | Returned active menu list | PASS | 
| `shiori_app` | Record new customer order | `INSERT INTO orders (customer_id, total_amount) VALUES (1, 350.00);` | Allowed | Row inserted successfully | PASS | 
| `shiori_auditor` | View sales analytics | `SELECT * FROM payments;` | Allowed | Returned financial records | PASS | 
| `shiori_auditor` | Modify payment status | `UPDATE payments SET status = 'Refunded' WHERE id = 1;` | Denied | `ERROR: permission denied for table payments` | PASS | 
| `shiori_staff` | Update order fulfillment status | `UPDATE orders SET status = 'Prepared' WHERE id = 1;` | Allowed | Row updated successfully | PASS | 
| `shiori_staff` | Delete menu catalog item | `DELETE FROM menu_items WHERE id = 1;` | Denied | `ERROR: permission denied for table menu_items` | PASS | 
| `shiori_app` | Drop database attempt | `DROP DATABASE shioricafe_db;` | Denied | `ERROR: permission denied to drop database` | PASS | 

## 5. Principle of Least Privilege Justification

1. **Backend Separation:** The web app runtime account (`shiori_app`) operates under explicit application-tier grants without superuser rights.

2. **Public Namespace Lockdown:** Revoking public schema permissions (`REVOKE ALL ON SCHEMA public FROM PUBLIC`) blocks unauthenticated table creation vulnerabilities.

3. **Restricted Staff Boundaries:** Barista and cashier accounts (`shiori_staff`) are limited solely to updating active orders and inventories, shielding core catalog and financial tables from operational errors.

## 6. Tracker Log Entry (Activity 4)

| Column | Details / Value | 
| ----- | ----- | 
| **Project** | Group 05 - SHIORIcafe-new-main | 
| **Repository Cloned** | `https://github.com/sev-villanueva/ReserveIT-Classroom-and-Material-Reservation-System-.git/SHIORIcafe-new-main` (branch: `main`) | 
| **Database Setup Result** | Success | 
| **Access-Control Folder Link** | `https://github.com/sev-villanueva/ReserveIT-Classroom-and-Material-Reservation-System-.git/db-access-control/group-05/` | 
| **Access-Control Status** | Completed | 
| **Feedback Sent to Owners** | Yes (2026-11-09) | 
| **PDF Progress Document** | `https://github.com/sev-villanueva/ReserveIT-Classroom-and-Material-Reservation-System-.git/docs/Activity4_ShioriCafe_Documentation.pdf` | 
| **Last Updated** | 2026-11-09 | 

## 7. AI Usage Declaration

* **AI Tools Used:** ChatGPT / Gemini 3 Flash.

* **Tasks Performed:** Structuring cafe role privilege models, mapping verification test matrices.

* **Validation Procedure:** Executed deployment scripts and validated security constraint triggers in PostgreSQL `psql`.