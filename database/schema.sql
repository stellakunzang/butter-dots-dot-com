-- Tibetan Spellchecker Database Schema
-- PostgreSQL 15+

-- Jobs table: Track spell check jobs
CREATE TABLE jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_email VARCHAR(255),
    status VARCHAR(50) NOT NULL,  -- 'pending', 'processing', 'completed', 'failed'
    file_name VARCHAR(255),
    file_size INTEGER,
    file_path TEXT,               -- Path to uploaded file: /app/uploads/{job_id}/{filename}
    result_path TEXT,             -- Path to result file: /app/results/{job_id}_annotated.pdf
    error_count INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Spell errors table: Errors found in jobs
CREATE TABLE spell_errors (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id UUID REFERENCES jobs(id) ON DELETE CASCADE,
    word TEXT NOT NULL,
    position INTEGER NOT NULL,
    page_number INTEGER,
    error_type VARCHAR(50) NOT NULL,  -- 'invalid_prefix', 'invalid_stack', etc.
    severity VARCHAR(20) NOT NULL,    -- 'critical', 'error', 'info'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Spelling reference table: Known valid words/syllables
CREATE TABLE spelling_reference (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    word TEXT NOT NULL UNIQUE,
    word_type VARCHAR(50),  -- 'syllable', 'word', 'phrase'
    source VARCHAR(100),    -- 'THDL', 'Monlam', 'user_submitted'
    is_validated BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX idx_jobs_status ON jobs(status);
CREATE INDEX idx_jobs_created_at ON jobs(created_at DESC);
CREATE INDEX idx_spell_errors_job_id ON spell_errors(job_id);
CREATE INDEX idx_spelling_reference_word ON spelling_reference(word);
