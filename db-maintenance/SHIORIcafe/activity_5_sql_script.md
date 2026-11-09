-- =============================================================================
-- COMP 018: Activity 5 - Routine Maintenance & Performance Script
-- Target Database: shioricafe_db
-- Run with DBA Privileges (e.g., dba_admin)
-- =============================================================================

-- 1. Database Health & Activity Checks
SELECT version();
SELECT current_database(), pg_size_pretty(pg_database_size(current_database()));

-- Active Connections Check
SELECT pid, usename, state, wait_event_type, wait_event, query_start, query
FROM pg_stat_activity
WHERE datname = current_database()
ORDER BY query_start NULLS LAST;

-- 2. Maintenance Tasks (Run as standalone statements, not inside transaction block)
ANALYZE public.menu_items;
ANALYZE public.orders;
ANALYZE public.reservations;
ANALYZE public.contacts;

VACUUM (VERBOSE, ANALYZE) public.orders;
VACUUM (VERBOSE, ANALYZE) public.reservations;

-- 3. Query Performance Analysis
EXPLAIN (ANALYZE, BUFFERS)
SELECT o.id, o.order_date, o.total_amount, m.item_name
FROM orders o
JOIN order_items oi ON o.id = oi.order_id
JOIN menu_items m ON oi.menu_item_id = m.id
WHERE o.status = 'Pending';

-- 4. Recommended Performance Index Tuning (Optional execution based on evaluation)
CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);
CREATE INDEX IF NOT EXISTS idx_order_items_order_id ON order_items(order_id);
