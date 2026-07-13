-- =============================================================================
-- ASEP — PostgreSQL Initialisation Script
-- Runs once when the postgres container starts for the first time.
-- =============================================================================

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- TODO (Phase 0.2): Create schemas, tables, and indices
-- Example:
-- CREATE SCHEMA IF NOT EXISTS asep;
-- SET search_path TO asep, public;

\echo 'ASEP PostgreSQL initialisation complete.'
