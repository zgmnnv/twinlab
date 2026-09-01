-- Runs once on first cluster init. The twin database is created from
-- POSTGRES_DB; here we add a separate database for Superset's own metadata
-- so the two never share a schema.
SELECT 'CREATE DATABASE superset OWNER ' || current_user
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'superset')\gexec

\connect twin
CREATE EXTENSION IF NOT EXISTS timescaledb;
