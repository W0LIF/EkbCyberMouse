CREATE TABLE service_centers (
    id              TEXT PRIMARY KEY,
    name            TEXT NOT NULL,
    lat             DOUBLE PRECISION NOT NULL,
    lon             DOUBLE PRECISION NOT NULL,
    opens_at        TIME NOT NULL DEFAULT '08:00',
    closes_at       TIME NOT NULL DEFAULT '22:00'
);

CREATE TABLE access_nodes (
    id              TEXT PRIMARY KEY,
    type            TEXT NOT NULL CHECK (type IN ('olt','switch')),
    lat             DOUBLE PRECISION NOT NULL,
    lon             DOUBLE PRECISION NOT NULL
);

CREATE TABLE staff (
    id              TEXT PRIMARY KEY,
    service_center_id TEXT NOT NULL REFERENCES service_centers(id),
    profile         TEXT NOT NULL CHECK (profile IN ('installation','3ltp','both')),
    technologies    TEXT[] NOT NULL,
    height_access   BOOLEAN NOT NULL DEFAULT FALSE,
    shift_start     TIME NOT NULL,
    shift_end       TIME NOT NULL,
    lunch_start     TIME NOT NULL,
    lunch_end       TIME NOT NULL,
    backpack_ont    INT NOT NULL DEFAULT 0,
    backpack_router INT NOT NULL DEFAULT 0,
    backpack_tv     INT NOT NULL DEFAULT 0
);

CREATE TABLE work_types (
    code            TEXT PRIMARY KEY,
    name            TEXT NOT NULL,
    profile         TEXT NOT NULL,
    requires_height BOOLEAN NOT NULL DEFAULT FALSE,
    norm_minutes    INT NOT NULL,
    deadline_hours  INT,           -- для 3ЛТП и подобных
    deadline_days   INT            -- для инсталляций
);

CREATE TABLE orders (
    id              TEXT PRIMARY KEY,
    work_type_code  TEXT NOT NULL REFERENCES work_types(code),
    technology      TEXT NOT NULL,
    lat             DOUBLE PRECISION NOT NULL,
    lon             DOUBLE PRECISION NOT NULL,
    address         TEXT,
    access_node_id  TEXT REFERENCES access_nodes(id),
    registered_at   TIMESTAMPTZ NOT NULL,
    slot_start      TIMESTAMPTZ NOT NULL,
    slot_end        TIMESTAMPTZ NOT NULL,
    is_repeat       BOOLEAN NOT NULL DEFAULT FALSE,
    req_ont         INT NOT NULL DEFAULT 0,
    req_router      INT NOT NULL DEFAULT 0,
    req_tv          INT NOT NULL DEFAULT 0,
    status          TEXT NOT NULL DEFAULT 'pending', -- pending|planned|unassigned|pgp|done|cancelled
    pgp_group_id    TEXT,
    assigned_staff_id TEXT REFERENCES staff(id),
    planned_start   TIMESTAMPTZ,
    planned_end     TIMESTAMPTZ,
    unassigned_reason TEXT
);

CREATE INDEX idx_orders_slot ON orders (slot_start, slot_end);
CREATE INDEX idx_orders_status ON orders (status);
CREATE INDEX idx_orders_node ON orders (access_node_id) WHERE access_node_id IS NOT NULL;

CREATE TABLE events (
    id              BIGSERIAL PRIMARY KEY,
    received_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    type            TEXT NOT NULL, -- new_order|cancel_visit|delay|staff_unavailable
    payload         JSONB NOT NULL,
    processed_at    TIMESTAMPTZ,
    response_ms     INT
);

CREATE TABLE plans (
    id              BIGSERIAL PRIMARY KEY,
    plan_date       DATE NOT NULL,
    generated_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    payload         JSONB NOT NULL -- полный план, как отдаем в API
);