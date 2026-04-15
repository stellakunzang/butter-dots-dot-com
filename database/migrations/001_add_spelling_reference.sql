-- Migration 001: Add spelling_reference table
-- Phase 2 — word corpus for dictionary-based spell checking
--
-- Apply to an existing database (one that already has the jobs/spell_errors
-- tables from the initial schema) with:
--
--   psql $DATABASE_URL -f database/migrations/001_add_spelling_reference.sql
--
-- The docker-compose postgres container and CI both use schema.sql directly
-- (full create), so this migration is only needed when upgrading a live database.
--
-- Future extensions (Phase 3+) hang off this table's primary key:
--   word_definitions (word_id → spelling_reference.id)  — definitions, part of speech
--   word_relationships (word_id, related_word_id)       — synonyms, dialect variants
--   word_etymology (word_id)                            — origin language, root form

CREATE TABLE IF NOT EXISTS spelling_reference (
    id SERIAL PRIMARY KEY,
    word TEXT UNIQUE NOT NULL,
    word_normalized TEXT NOT NULL,
    source_count INTEGER NOT NULL DEFAULT 1,
    sources JSONB NOT NULL DEFAULT '[]',
    first_seen_in VARCHAR(50),
    times_seen INTEGER NOT NULL DEFAULT 0,
    dialect VARCHAR(20),
    is_sanskrit BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_spelling_ref_word ON spelling_reference(word);
CREATE INDEX IF NOT EXISTS idx_spelling_ref_word_normalized ON spelling_reference(word_normalized);
CREATE INDEX IF NOT EXISTS idx_spelling_ref_dialect ON spelling_reference(dialect);
