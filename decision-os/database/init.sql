-- Decision OS v3.0 PostgreSQL bootstrap script
-- Usage:
--   psql -U admin -d decision_os_prod -f init.sql
--
-- Notes:
-- 1. This script is intended for PostgreSQL/psql.
-- 2. It enables UUID support, then applies the canonical schema.
-- 3. Seed data, if any, should be applied after this bootstrap.

\echo 'Initializing Decision OS schema'

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

\i schema.sql

\echo 'Decision OS schema initialization complete'
