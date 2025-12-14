-- Initialize test database with required extensions
-- This script runs automatically when the test container starts

-- Enable vector extension for embeddings
CREATE EXTENSION IF NOT EXISTS vector;

-- Enable pg_trgm for fuzzy text search
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- Enable UUID generation
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Verify extensions are loaded
SELECT extname, extversion 
FROM pg_extension 
WHERE extname IN ('vector', 'pg_trgm', 'uuid-ossp');
