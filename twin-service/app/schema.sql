-- TwinLab lean schema: one PostgreSQL/TimescaleDB database holds both the
-- twin's domain model and its time-series history. Statements are split on
-- ";\n" and executed one by one, so keep one statement per block.

CREATE EXTENSION IF NOT EXISTS timescaledb;

CREATE TABLE IF NOT EXISTS twin (
    id         text PRIMARY KEY,
    name       text NOT NULL,
    kind       text NOT NULL DEFAULT 'process',
    config     jsonb NOT NULL DEFAULT '{}'::jsonb,
    state      jsonb NOT NULL DEFAULT '{}'::jsonb,
    flow       jsonb NOT NULL DEFAULT '{"nodes": [], "edges": []}'::jsonb,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS twin_state_history (
    twin_id text NOT NULL REFERENCES twin(id) ON DELETE CASCADE,
    ts      timestamptz NOT NULL DEFAULT now(),
    state   jsonb NOT NULL
);

SELECT create_hypertable('twin_state_history', 'ts', if_not_exists => TRUE);

CREATE TABLE IF NOT EXISTS measurement (
    twin_id text NOT NULL REFERENCES twin(id) ON DELETE CASCADE,
    ts      timestamptz NOT NULL DEFAULT now(),
    metric  text NOT NULL,
    value   double precision NOT NULL
);

SELECT create_hypertable('measurement', 'ts', if_not_exists => TRUE);

CREATE INDEX IF NOT EXISTS measurement_twin_metric_ts
    ON measurement (twin_id, metric, ts DESC);

CREATE TABLE IF NOT EXISTS event (
    id      bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    twin_id text NOT NULL REFERENCES twin(id) ON DELETE CASCADE,
    ts      timestamptz NOT NULL DEFAULT now(),
    type    text NOT NULL,
    payload jsonb NOT NULL DEFAULT '{}'::jsonb
);

CREATE INDEX IF NOT EXISTS event_twin_ts ON event (twin_id, ts DESC);

CREATE TABLE IF NOT EXISTS plan (
    id         bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    twin_id    text NOT NULL REFERENCES twin(id) ON DELETE CASCADE,
    created_at timestamptz NOT NULL DEFAULT now(),
    params     jsonb NOT NULL,
    result     jsonb NOT NULL,
    active     boolean NOT NULL DEFAULT false
);

CREATE INDEX IF NOT EXISTS plan_twin_active ON plan (twin_id, active);

CREATE MATERIALIZED VIEW IF NOT EXISTS measurement_daily
WITH (timescaledb.continuous) AS
SELECT twin_id,
       metric,
       time_bucket('1 day', ts) AS day,
       avg(value)        AS avg_value,
       max(value)        AS max_value,
       min(value)        AS min_value,
       last(value, ts)   AS last_value
FROM measurement
GROUP BY twin_id, metric, day
WITH NO DATA;

SELECT add_continuous_aggregate_policy('measurement_daily',
       start_offset      => INTERVAL '30 days',
       end_offset        => INTERVAL '1 hour',
       schedule_interval => INTERVAL '1 hour',
       if_not_exists     => TRUE);

-- Flat views for BI (Superset builds datasets on these, not on jsonb).

CREATE OR REPLACE VIEW v_daily AS
SELECT twin_id,
       day::date AS day,
       metric,
       last_value,
       avg_value,
       min_value,
       max_value
FROM measurement_daily;

CREATE OR REPLACE VIEW v_active_plan AS
SELECT twin_id,
       created_at,
       (result ->> 'daily_avg_consumption')::float AS daily_avg_consumption,
       (result ->> 'forecast_stock')::float        AS forecast_stock,
       (result ->> 'safety_stock')::float          AS safety_stock,
       (result ->> 'current_stock')::float         AS current_stock,
       (result ->> 'required_production')::float   AS required_production,
       (result ->> 'stock_ok')::boolean            AS stock_ok
FROM plan
WHERE active;

CREATE OR REPLACE VIEW v_plan_history AS
SELECT twin_id,
       id,
       created_at,
       active,
       (params ->> 'forecast_days')::int          AS forecast_days,
       (params ->> 'weekend_factor')::float       AS weekend_factor,
       (params ->> 'safety_factor')::float        AS safety_factor,
       (result ->> 'required_production')::float  AS required_production,
       (result ->> 'forecast_stock')::float       AS forecast_stock
FROM plan;
