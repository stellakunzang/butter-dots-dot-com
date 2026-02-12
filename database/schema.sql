-- Tibetan Spellchecker Database Schema
-- PostgreSQL 15+
-- NOTE: Database not used yet - planned for Block 5 (PDF Processing)

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
