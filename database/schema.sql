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

-- Spelling reference: validated Tibetan word corpus (Phase 2)
-- Words are stored at the dictionary-entry level (may be multi-syllable).
-- At runtime the DictionaryService extracts individual syllables from all
-- entries and builds an in-memory frozenset for O(1) per-syllable lookup.
-- Future Phase 3+ tables (word_definitions, word_relationships, word_etymology)
-- will reference this table via spelling_reference.id as a foreign key.
CREATE TABLE spelling_reference (
    id SERIAL PRIMARY KEY,
    word TEXT UNIQUE NOT NULL,           -- original form from source
    word_normalized TEXT NOT NULL,       -- NFC-normalized form, used for dedup
    source_count INTEGER NOT NULL DEFAULT 1,
    sources JSONB NOT NULL DEFAULT '[]', -- e.g. ["thdl", "rangjung_yeshe"]
    confidence_score DECIMAL(3,2),       -- 0.40–1.00 derived from source_count
    first_seen_in VARCHAR(50),           -- which source contributed it first
    times_seen INTEGER NOT NULL DEFAULT 0, -- incremented when found in checked docs
    dialect VARCHAR(20),                 -- 'amdo', 'u_tsang', NULL = pan-dialectal
    is_sanskrit BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_spelling_ref_word ON spelling_reference(word);
CREATE INDEX idx_spelling_ref_word_normalized ON spelling_reference(word_normalized);
CREATE INDEX idx_spelling_ref_dialect ON spelling_reference(dialect);
CREATE INDEX idx_spelling_ref_confidence ON spelling_reference(confidence_score DESC);
