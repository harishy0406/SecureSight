-- =============================================================================
-- SecureSight — Database Initialization Script
-- This script runs on first PostgreSQL container startup via
-- docker-entrypoint-initdb.d.
-- =============================================================================

-- Additional database for testing
SELECT 'CREATE DATABASE securesight_test'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'securesight_test')\gexec
