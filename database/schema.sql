-- Tibetan Spellchecker Database Schema
-- PostgreSQL 15+

-- Jobs table: Track PDF spell check jobs
CREATE TABLE jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    status VARCHAR(50) NOT NULL,  -- 'pending', 'processing', 'completed', 'failed'
    file_name VARCHAR(255) NOT NULL,
    file_size INTEGER,
    file_path TEXT NOT NULL,      -- Path to uploaded file: /app/uploads/{job_id}/{filename}
    result_path TEXT,              -- Path to result file: /app/results/{job_id}_annotated.pdf
    error_count INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Spell errors table: Errors found in PDF jobs
CREATE TABLE spell_errors (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id UUID NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
    word TEXT NOT NULL,
    position INTEGER NOT NULL,
    page_number INTEGER,           -- PDF page number (1-indexed)
    error_type VARCHAR(50) NOT NULL,  -- 'invalid_prefix_combination', 'invalid_superscript', etc.
    severity VARCHAR(20) NOT NULL,    -- 'error', 'warning', 'info'
    message TEXT,                  -- Human-readable error message
    component VARCHAR(50),         -- Which syllable component has error (prefix, root, etc.)
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX idx_jobs_status ON jobs(status);
CREATE INDEX idx_jobs_created_at ON jobs(created_at DESC);
CREATE INDEX idx_spell_errors_job_id ON spell_errors(job_id);

-- Lexicon: word corpus (Phase 2 spelling) and provenance (WORD_CORPUS_PLAN.md)
-- The word list used for per-syllable spellcheck: DictionaryService loads
-- word.word_normalized for all rows. Provenance is word_source + source;
-- full gloss text lives in definition (ingest pipeline, later PRs).
CREATE TABLE source (
    id SERIAL PRIMARY KEY,
    source_key TEXT UNIQUE NOT NULL,
    display_name TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE word (
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

CREATE TABLE word_source (
    id SERIAL PRIMARY KEY,
    word_id INTEGER NOT NULL REFERENCES word(id) ON DELETE CASCADE,
    source_id INTEGER NOT NULL REFERENCES source(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT uq_word_source_word_source UNIQUE (word_id, source_id)
);

CREATE TABLE definition (
    id SERIAL PRIMARY KEY,
    word_id INTEGER NOT NULL REFERENCES word(id) ON DELETE CASCADE,
    source_id INTEGER NOT NULL REFERENCES source(id) ON DELETE CASCADE,
    body TEXT NOT NULL,
    sort_order INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Raw import lines for replay/QA (optional for early ingest tooling)
CREATE TABLE lexicon_staging_line (
    id BIGSERIAL PRIMARY KEY,
    import_batch_id UUID NOT NULL,
    file_ref TEXT,
    line_number INTEGER,
    raw_line TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_word_display ON word (word);
CREATE INDEX idx_word_dialect ON word (dialect);
CREATE INDEX idx_word_source_word_id ON word_source (word_id);
CREATE INDEX idx_word_source_source_id ON word_source (source_id);
CREATE INDEX idx_definition_word_id ON definition (word_id);
CREATE INDEX idx_definition_source_id ON definition (source_id);
CREATE INDEX idx_definition_word_source ON definition (word_id, source_id);
CREATE INDEX idx_lexicon_staging_batch ON lexicon_staging_line (import_batch_id);
