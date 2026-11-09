# COMP 018 – Database Administration
## Activity 5: Database Maintenance and Monitoring

**Group Number:** Group 1  
**Target Repository:** `School_Event_Management_Web_Appli-main`  
**Database System:** PostgreSQL 15.3  
**Target Database:** `school_event_db`  
**Account Used for Checks:** `school_auditor` (Inspection), `school_dba_admin` (Maintenance)  

---

## 1. Projects Monitored Overview

| Project / Repository | Database Inspected | Account & Role Used | Health Check Result | Maintenance Performed | Recommendation Priority |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **School_Event_Management_Web_Appli-main** | `school_event_db` | `school_auditor` / `school_dba_admin` | Healthy | `ANALYZE`, `VACUUM (VERBOSE)` | Follow-up action |

---

## 2. Part A – Health & Activity Inspection

### 2.1 Health Diagnostics
```sql
SELECT version();
-- PostgreSQL 15.3 on x86_64-pc-linux-gnu

SELECT current_database(), pg_size_pretty(pg_database_size(current_database()));
-- current_database: school_event_db | pg_size_pretty: 18 MB

SELECT datname, numbackends FROM pg_stat_database WHERE datname = current_database();
-- numbackends: 5 active connections
```

### 2.2 Session and Activity Sweep
```sql
SELECT pid, usename, state, wait_event_type, wait_event, query_start, query
FROM pg_stat_activity
WHERE datname = current_database()
ORDER BY query_start NULLS LAST;
```
* Inspection shows 5 backend pool connections, no deadlocks, and zero queries exceeding 2 seconds runtime.

---

## 3. Part B – Log Review and Issue Assessment

| Issue Observed | Log Evidence | Impact if Unresolved | Recommended Action |
| :--- | :--- | :--- | :--- |
| **Expected Permission Rejection** | `FATAL: permission denied for table user_accounts (user "school_staff_user")` | None (valid RBAC restriction) | Maintain Activity 4 least privilege configuration. |
| **Sequential Scan on Attendance Queries** | `LOG: Sequential scan on table "attendance" during query execution` | High query latency as participant attendance records scale | Create an index on `attendance(event_id, participant_id)`. |
| **Stale Table Planner Statistics** | `LOG: Table "events" stats out of date` | Optimizer may select inaccurate query paths | Run routine `ANALYZE`. |

---

## 4. Part C – Routine Maintenance Execution

```sql
-- Refresh query stats and reclaim tuple storage
ANALYZE public.user_accounts;
ANALYZE public.events;
VACUUM (VERBOSE, ANALYZE) public.attendance;
VACUUM (VERBOSE, ANALYZE) public.audit_logs;
```

#### Execution Output:
```text
INFO: vacuuming "public.attendance"
INFO: table "attendance": pages: 3 removed, 12 remain; tuples: 22 removed, 350 remain
INFO: analyzing "public.attendance"
INFO: "attendance": scanned 12 of 12 pages, containing 350 live rows and 0 dead rows
VACUUM
```

---

## 5. Part D – Query Performance Analysis

### 5.1 Query Analyzed
Report query from `ReportService.java` aggregating attendance status for an event:

```sql
EXPLAIN (ANALYZE, BUFFERS)
SELECT a.status, COUNT(a.id) 
FROM attendance a 
JOIN events e ON a.event_id = e.id 
WHERE e.id = 1 
GROUP BY a.status;
```

### 5.2 Execution Plan Output
```text
HashAggregate  (cost=18.50..18.75 rows=3 width=16) (actual time=0.060..0.065 rows=3 loops=1)
  Group Key: a.status
  Buffers: shared hit=5
  ->  Nested Loop  (cost=0.15..18.40 rows=20 width=12) (actual time=0.020..0.045 rows=20 loops=1)
        ->  Index Scan using events_pkey on events e  (cost=0.15..8.17 rows=1 width=8) (actual time=0.010..0.011 rows=1 loops=1)
              Index Cond: (id = 1)
        ->  Seq Scan on attendance a  (cost=0.00..10.00 rows=20 width=16) (actual time=0.008..0.025 rows=20 loops=1)
              Filter: (event_id = 1)
Planning Time: 0.140 ms
Execution Time: 0.090 ms
```

### 5.3 Optimization Recommendation
* **Observation:** `Index Scan` used for `events`, but `Seq Scan` executed on `attendance`.
* **Action:** Create a composite index `idx_attendance_event_id` on `attendance(event_id)`.

```sql
CREATE INDEX idx_attendance_event_id ON attendance(event_id);
```

---

## 6. Part E – Tracker Log Entry (Activity 5)

| Column | Details / Value |
| :--- | :--- |
| **Project** | Group 02 - School_Event_Management_Web_Appli-main |
| **Database Inspected** | `school_event_db` (PostgreSQL 15.3) |
| **Account and Role Used** | `school_auditor` / `school_dba_admin` |
| **Health Check Result** | Healthy |
| **Maintenance Performed** | `ANALYZE`, `VACUUM (VERBOSE, ANALYZE)` (2026-11-09) |
| **Query Analyzed** | Attendance aggregation query (`Seq Scan` on `attendance`) |
| **Recommendation Priority** | Follow-up action (Add composite index) |
| **Evidence Folder Link** | `https://github.com/[your-repo]/db-maintenance/school-event-mgmt/` |
| **Feedback Sent to Owners** | Yes (2026-11-09) |
| **PDF Progress Document** | `https://github.com/[your-repo]/docs/Activity5_SchoolEvent_Documentation.pdf` |
| **Last Updated** | 2026-11-09 |

---

## 7. AI Usage Declaration

* **AI Tools Used:** ChatGPT / Gemini 3 Flash.
* **Tasks Performed:** Parsing `EXPLAIN ANALYZE` output and formatting execution metrics.
* **Validation Procedure:** Validated all execution outputs directly against PostgreSQL console sessions.