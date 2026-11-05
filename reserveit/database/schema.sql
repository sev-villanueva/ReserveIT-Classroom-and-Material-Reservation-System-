-- ReserveIT schema (PostgreSQL 16+; design target: PostgreSQL 18)
-- Matches Activity 2: 8 tables, 5 one-to-many relationships, 1 many-to-many
-- (RESERVATION <-> MATERIAL via RESERVATION_MATERIAL).
-- Changes from the Activity 2 draft are listed in docs/database.md.

CREATE EXTENSION IF NOT EXISTS btree_gist;   -- needed for the room-overlap constraint

CREATE TABLE department (
    department_id   BIGSERIAL PRIMARY KEY,
    department_name VARCHAR(100) NOT NULL UNIQUE
);

-- "user" is a reserved word in PostgreSQL, so the requester table is app_user.
CREATE TABLE app_user (
    user_id       BIGSERIAL PRIMARY KEY,
    first_name    VARCHAR(50)  NOT NULL,
    last_name     VARCHAR(50)  NOT NULL,
    email         VARCHAR(100) NOT NULL UNIQUE CHECK (email = lower(email)),
    password_hash VARCHAR(255) NOT NULL,
    role          VARCHAR(10)  NOT NULL CHECK (role IN ('STUDENT', 'FACULTY')),
    department_id BIGINT       NOT NULL REFERENCES department (department_id),
    status        VARCHAR(10)  NOT NULL DEFAULT 'ACTIVE'
                  CHECK (status IN ('ACTIVE', 'SUSPENDED'))
);

CREATE TABLE staff (
    staff_id      BIGSERIAL PRIMARY KEY,
    full_name     VARCHAR(100) NOT NULL,
    email         VARCHAR(100) NOT NULL UNIQUE CHECK (email = lower(email)),
    password_hash VARCHAR(255) NOT NULL,
    role          VARCHAR(10)  NOT NULL CHECK (role IN ('STAFF', 'ADMIN')),
    status        VARCHAR(10)  NOT NULL DEFAULT 'ACTIVE'
                  CHECK (status IN ('ACTIVE', 'INACTIVE'))
);

CREATE TABLE room (
    room_id   BIGSERIAL PRIMARY KEY,
    room_name VARCHAR(50) NOT NULL,
    building  VARCHAR(50) NOT NULL,
    capacity  INT         NOT NULL CHECK (capacity > 0),
    room_type VARCHAR(20) NOT NULL
              CHECK (room_type IN ('CLASSROOM', 'LABORATORY', 'CONFERENCE')),
    status    VARCHAR(20) NOT NULL DEFAULT 'AVAILABLE'
              CHECK (status IN ('AVAILABLE', 'UNDER_MAINTENANCE')),
    UNIQUE (building, room_name)
);

CREATE TABLE material (
    material_id        BIGSERIAL PRIMARY KEY,
    material_name      VARCHAR(100) NOT NULL UNIQUE,
    category           VARCHAR(20)  NOT NULL
                       CHECK (category IN ('AV_EQUIPMENT', 'FURNITURE', 'SUPPLIES')),
    total_quantity     INT NOT NULL CHECK (total_quantity >= 0),
    available_quantity INT NOT NULL,
    CHECK (available_quantity BETWEEN 0 AND total_quantity)
);

CREATE TABLE reservation (
    reservation_id   BIGSERIAL PRIMARY KEY,
    user_id          BIGINT NOT NULL REFERENCES app_user (user_id),
    room_id          BIGINT NOT NULL REFERENCES room (room_id),
    staff_id         BIGINT REFERENCES staff (staff_id),   -- NULL until reviewed
    reservation_date DATE   NOT NULL,
    start_time       TIME   NOT NULL,
    end_time         TIME   NOT NULL,
    purpose          VARCHAR(255) NOT NULL,
    status           VARCHAR(20)  NOT NULL DEFAULT 'PENDING'
                     CHECK (status IN ('PENDING', 'APPROVED', 'REJECTED', 'CANCELLED', 'COMPLETED')),
    CHECK (end_time > start_time),
    -- Business rule 4: approved/rejected/completed reservations must have a reviewer.
    CHECK (status IN ('PENDING', 'CANCELLED') OR staff_id IS NOT NULL),
    -- Business rule 3: two APPROVED reservations for the same room cannot overlap.
    CONSTRAINT no_overlapping_approved_reservations
        EXCLUDE USING gist (
            room_id WITH =,
            tsrange(reservation_date + start_time, reservation_date + end_time) WITH &&
        ) WHERE (status = 'APPROVED')
);

CREATE TABLE reservation_material (
    reservation_id     BIGINT NOT NULL REFERENCES reservation (reservation_id) ON DELETE CASCADE,
    material_id        BIGINT NOT NULL REFERENCES material (material_id),
    quantity_requested INT    NOT NULL CHECK (quantity_requested > 0),
    PRIMARY KEY (reservation_id, material_id)
);

CREATE TABLE penalty (
    penalty_id     BIGSERIAL PRIMARY KEY,
    reservation_id BIGINT NOT NULL UNIQUE REFERENCES reservation (reservation_id),
    reason         VARCHAR(30) NOT NULL
                   CHECK (reason IN ('NO_SHOW', 'DAMAGED_MATERIAL', 'LATE_RETURN')),
    amount         NUMERIC(10, 2) NOT NULL CHECK (amount >= 0),
    issue_date     DATE NOT NULL DEFAULT CURRENT_DATE,
    paid_status    VARCHAR(10) NOT NULL DEFAULT 'UNPAID' CHECK (paid_status IN ('UNPAID', 'PAID')),
    paid_date      DATE,
    CHECK ((paid_status = 'PAID') = (paid_date IS NOT NULL))
);

-- Indexes named in the Activity 2 handoff sheet, plus the requester lookup
CREATE INDEX idx_reservation_room   ON reservation (room_id);
CREATE INDEX idx_reservation_date   ON reservation (reservation_date);
CREATE INDEX idx_reservation_status ON reservation (status);
CREATE INDEX idx_reservation_user   ON reservation (user_id);
