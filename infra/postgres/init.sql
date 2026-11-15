CREATE TABLE service_centers (
    service_center_id VARCHAR(10) PRIMARY KEY,
    name TEXT NOT NULL,
    address TEXT NOT NULL,
    lat DOUBLE PRECISION NOT NULL,
    lon DOUBLE PRECISION NOT NULL,
    opening_hours JSONB NOT NULL,
    restock_duration_min INT NOT NULL
);

CREATE TABLE work_types (
    code VARCHAR(50) PRIMARY KEY,
    name TEXT NOT NULL,
    profiles TEXT[] NOT NULL,
    duration_min INT NOT NULL,
    max_start_delay_min INT,
    deadline_kind VARCHAR(20) NOT NULL,
    deadline_value INT,
    repeat_deadline_value INT,
    pgp_relevant BOOLEAN NOT NULL
);

CREATE TABLE staff (
    staff_id VARCHAR(10) PRIMARY KEY,
    display_name TEXT,
    service_center_id VARCHAR(10) REFERENCES service_centers(service_center_id),
    profiles TEXT[] NOT NULL,
    technologies TEXT[] NOT NULL,
    height_permit BOOLEAN NOT NULL,
    shift JSONB NOT NULL,
    equipment_start JSONB NOT NULL,
    equipment_capacity JSONB NOT NULL,
    experience_years DOUBLE PRECISION
);

CREATE TABLE buildings (
    building_id VARCHAR(10) PRIMARY KEY,
    address TEXT NOT NULL,
    lat DOUBLE PRECISION NOT NULL,
    lon DOUBLE PRECISION NOT NULL,
    building_type VARCHAR(10) NOT NULL,
    overhead_line BOOLEAN NOT NULL,
    zone_service_center_id VARCHAR(10)
);

CREATE TABLE access_nodes (
    access_node_id VARCHAR(10) PRIMARY KEY,
    node_type VARCHAR(20) NOT NULL,
    technology VARCHAR(20) NOT NULL,
    name TEXT NOT NULL,
    address TEXT,
    lat DOUBLE PRECISION NOT NULL,
    lon DOUBLE PRECISION NOT NULL
);

-- Связь узлов и домов (дом может быть в нескольких узлах)
CREATE TABLE access_node_buildings (
    access_node_id VARCHAR(10) REFERENCES access_nodes(access_node_id) ON DELETE CASCADE,
    building_id VARCHAR(10) REFERENCES buildings(building_id) ON DELETE CASCADE,
    PRIMARY KEY (access_node_id, building_id)
);

-- Дни
CREATE TABLE days (
    date DATE PRIMARY KEY,
    model_now TIMESTAMPTZ NOT NULL,
    absent_staff_ids TEXT[],
    event_received BOOLEAN DEFAULT FALSE
);

-- Наряды
CREATE TABLE orders (
    order_id VARCHAR(20) PRIMARY KEY,
    work_type_code VARCHAR(50) REFERENCES work_types(code),
    technology VARCHAR(20) NOT NULL,
    building_id VARCHAR(10) REFERENCES buildings(building_id),
    address TEXT NOT NULL,
    lat DOUBLE PRECISION NOT NULL,
    lon DOUBLE PRECISION NOT NULL,
    building_type VARCHAR(10) NOT NULL,
    requires_height BOOLEAN NOT NULL,
    access_node_id VARCHAR(10),
    registered_at TIMESTAMPTZ NOT NULL,
    slot_start TIMESTAMPTZ NOT NULL,
    slot_end TIMESTAMPTZ NOT NULL,
    latest_start TIMESTAMPTZ NOT NULL,
    deadline TIMESTAMPTZ NOT NULL,
    req_ont INT NOT NULL,
    req_router INT NOT NULL,
    req_stb INT NOT NULL,
    is_repeat BOOLEAN NOT NULL,
    previous_order_id VARCHAR(20),
    status VARCHAR(20) DEFAULT 'pending',
    planned_start TIMESTAMPTZ,
    planned_end TIMESTAMPTZ,
    assigned_staff_id VARCHAR(10) REFERENCES staff(staff_id),
    pgp_group_id VARCHAR(20),
    unassigned_reason_code VARCHAR(50),
    unassigned_reason_text TEXT,
    unassigned_suggested_action VARCHAR(20)
);

CREATE INDEX idx_orders_slot ON orders(slot_start);
CREATE INDEX idx_orders_status ON orders(status);
CREATE INDEX idx_orders_node_ts ON orders(access_node_id, registered_at) WHERE access_node_id IS NOT NULL;

-- Фактические длительности завершенных работ для прогноза по истории
CREATE TABLE IF NOT EXISTS order_facts (
    order_id VARCHAR(20) PRIMARY KEY,
    work_type_code VARCHAR(50) NOT NULL,
    technology VARCHAR(20) NOT NULL,
    actual_duration_min INT NOT NULL CHECK (actual_duration_min > 0),
    occurred_at TIMESTAMPTZ NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_order_facts_type_technology
    ON order_facts(work_type_code, technology);

-- Действия отдельного мобильного приложения сотрудника
CREATE TABLE IF NOT EXISTS mobile_visit_actions (
    id BIGSERIAL PRIMARY KEY,
    date DATE NOT NULL,
    staff_id VARCHAR(10) NOT NULL,
    order_id VARCHAR(20) NOT NULL,
    action VARCHAR(20) NOT NULL
        CHECK (action IN ('CALL_CUSTOMER', 'ARRIVED', 'COMPLETED')),
    occurred_at TIMESTAMPTZ NOT NULL,
    UNIQUE (date, staff_id, order_id, action)
);

CREATE INDEX IF NOT EXISTS idx_mobile_visit_actions_route
    ON mobile_visit_actions(date, staff_id);

-- События
CREATE TABLE events (
    id BIGSERIAL PRIMARY KEY,
    date DATE REFERENCES days(date),
    event_id VARCHAR(50) NOT NULL,
    type VARCHAR(50) NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL,
    payload JSONB NOT NULL,
    processed_at TIMESTAMPTZ,
    response_ms INT,
    UNIQUE(date, event_id)
);

-- Версии плана
CREATE TABLE plan_versions (
    id BIGSERIAL PRIMARY KEY,
    date DATE REFERENCES days(date),
    version INT NOT NULL,
    based_on_event_id VARCHAR(50),
    as_of TIMESTAMPTZ NOT NULL,
    payload JSONB NOT NULL,
    computed_ms INT,
    UNIQUE(date, version)
);

-- Алерты (только append)
CREATE TABLE alerts (
    alert_id VARCHAR(50) PRIMARY KEY,
    date DATE REFERENCES days(date),
    created_at TIMESTAMPTZ NOT NULL,
    type VARCHAR(50) NOT NULL,
    status VARCHAR(20) NOT NULL,
    resolved_at TIMESTAMPTZ,
    order_id VARCHAR(20),
    group_id VARCHAR(20),
    staff_id VARCHAR(10),
    forecast_start TIMESTAMPTZ,
    lateness_min INT,
    suggested_action VARCHAR(50) NOT NULL,
    suggested_staff_id VARCHAR(10),
    proposed_slot JSONB,
    applied BOOLEAN DEFAULT FALSE,
    message TEXT NOT NULL
);

CREATE TABLE travel_matrix_meta (
    matrix_id VARCHAR(50) PRIMARY KEY,
    points TEXT[] NOT NULL,
    loaded_at TIMESTAMPTZ DEFAULT NOW()
);