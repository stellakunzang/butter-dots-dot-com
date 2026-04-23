-- Migration 002: Lexicon schema (WORD_CORPUS_PLAN.md)
-- Replaces JSONB on spelling_reference with normalized source + word_source;
-- renames the spelling list table to "word" and adds definition + staging.
--
-- Apply to a database that was created with migration 001 (spelling_reference):
--   psql $DATABASE_URL -f database/migrations/002_lexicon_schema.sql
--
-- Fresh environments that use database/schema.sql directly (Docker, CI) already
-- include this shape and do not need this file unless upgrading an old DB.
--
-- Safe to run once. If spelling_reference is already gone, the DO block is a
-- no-op; CREATE TABLE IF NOT EXISTS is idempotent.

BEGIN;

CREATE TABLE IF NOT EXISTS source (
    id SERIAL PRIMARY KEY,
    source_key TEXT UNIQUE NOT NULL,
    display_name TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS word (
    id SERIAL PRIMARY KEY,
    word TEXT UNIQUE NOT NULL,
    word_normalized TEXT NOT NULL,
    first_seen_in VARCHAR(50),
    times_seen INTEGER NOT NULL DEFAULT 0,
    dialect VARCHAR(20),
    is_sanskrit BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT uq_word_normalized UNIQUE (word_normalized)
);

CREATE TABLE IF NOT EXISTS word_source (
    id SERIAL PRIMARY KEY,
    word_id INTEGER NOT NULL REFERENCES word(id) ON DELETE CASCADE,
    source_id INTEGER NOT NULL REFERENCES source(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT uq_word_source_word_source UNIQUE (word_id, source_id)
);

CREATE TABLE IF NOT EXISTS definition (
    id SERIAL PRIMARY KEY,
    word_id INTEGER NOT NULL REFERENCES word(id) ON DELETE CASCADE,
    source_id INTEGER NOT NULL REFERENCES source(id) ON DELETE CASCADE,
    body TEXT NOT NULL,
    sort_order INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS lexicon_staging_line (
    id BIGSERIAL PRIMARY KEY,
    import_batch_id UUID NOT NULL,
    file_ref TEXT,
    line_number INTEGER,
    raw_line TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_lexicon_staging_batch
    ON lexicon_staging_line (import_batch_id);
CREATE INDEX IF NOT EXISTS idx_definition_word_id ON definition (word_id);
CREATE INDEX IF NOT EXISTS idx_definition_source_id ON definition (source_id);
CREATE INDEX IF NOT EXISTS idx_definition_word_source
    ON definition (word_id, source_id);
CREATE INDEX IF NOT EXISTS idx_word_source_word_id ON word_source (word_id);
CREATE INDEX IF NOT EXISTS idx_word_source_source_id ON word_source (source_id);
CREATE INDEX IF NOT EXISTS idx_word_display ON word (word);
CREATE INDEX IF NOT EXISTS idx_word_dialect ON word (dialect);

-- Migrate from migration 001 spelling_reference into lexicon tables.
DO
$$
BEGIN
  IF to_regclass('public.spelling_reference') IS NULL THEN
    RAISE NOTICE 'spelling_reference absent — skipping data migration (already applied or new DB)';
  ELSE
    -- Distinct source keys from legacy JSONB arrays
    INSERT INTO source (source_key, display_name)
    SELECT DISTINCT
        src.t,
        src.t
    FROM spelling_reference sr
    CROSS JOIN LATERAL jsonb_array_elements_text (sr.sources) AS src (t)
    ON CONFLICT (source_key) DO NOTHING;

    INSERT INTO word
        (word, word_normalized, first_seen_in, times_seen, dialect, is_sanskrit, created_at)
    SELECT
        word,
        word_normalized,
        first_seen_in,
        times_seen,
        dialect,
        is_sanskrit,
        created_at
    FROM spelling_reference
    ON CONFLICT (word) DO NOTHING;

    INSERT INTO word_source (word_id, source_id)
    SELECT w.id, s.id
    FROM spelling_reference sr
    INNER JOIN word w ON w.word = sr.word
    CROSS JOIN LATERAL jsonb_array_elements_text (sr.sources) AS src (t)
    INNER JOIN source s ON s.source_key = src.t
    ON CONFLICT (word_id, source_id) DO NOTHING;

    DROP TABLE spelling_reference;
  END IF;
END;
$$;

COMMIT;
