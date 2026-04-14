# Tibetan Word Corpus - Sourcing Plan

**Goal**: Build 30,000-50,000 word spelling reference  
**Method**: Multi-source cross-referencing  
**Quality**: Only words appearing in 2+ sources

---

## Recommended Sources

### 1. THDL (Tibetan & Himalayan Digital Library)

**URL**: https://www.thlib.org  
**Access**: Public, academic project (UVA)

**What They Have:**
- Tibetan dictionaries (downloadable)
- Word frequency lists
- Academic corpora
- Free for research/educational use

**How to Access:**
- Dictionary downloads available on their site
- Look for: "Tibetan Dictionaries" section
- Format: Usually XML or plain text
- License: Check their terms, usually allows educational use

**Estimated Words**: ~40,000-50,000

---

### 2. Monlam IT Dictionary

**URL**: https://www.monlam.ai  
**Access**: API available, may require permission

**What They Have:**
- Grand Tibetan Dictionary (largest modern dictionary)
- ~100,000+ entries
- Modern, well-maintained
- Mobile apps available

**How to Access:**
- Check if they have public API
- Contact them for dataset access
- May have downloadable database
- Likely requires permission/attribution

**Estimated Words**: ~100,000+

**Action Item**: Email/contact Monlam for research/educational access

---

### 3. Rangjung Yeshe Wiki

**URL**: https://rywiki.tsadra.org  
**Access**: Public wiki

**What They Have:**
- Buddhist terminology dictionary
- Community-maintained
- Focused on Dharma terms
- MediaWiki format (can be exported)

**How to Access:**
- Wiki export tools
- Or scrape respectfully
- Check their API (MediaWiki has standard API)

**Estimated Words**: ~30,000

**Pros:**
- Excellent for Buddhist texts
- Free access
- Good quality

**Cons:**
- Domain-specific (Dharma heavy)
- May miss common everyday words

---

### 4. Frequency Corpus Method (Fallback)

**If licensing issues arise, build our own:**

**Sources of Public Domain Tibetan Texts:**
- Buddhist sutras (public domain)
- Historical texts
- Government publications
- Open-access academic papers

**Process:**
```python
# Extract all unique words from texts
def build_frequency_corpus(texts):
    word_freq = {}
    
    for text in texts:
        words = extract_words(text)
        for word in words:
            normalized = normalize_tibetan(word)
            word_freq[normalized] = word_freq.get(normalized, 0) + 1
    
    # Keep words appearing 3+ times (filter typos)
    return {w: f for w, f in word_freq.items() if f >= 3}
```

**Pros:**
- ✅ Fully legal (public domain)
- ✅ Frequency data built-in
- ✅ Reflects actual usage

**Cons:**
- ❌ More work to build
- ❌ Lower coverage initially
- ❌ Depends on text quality

---

## Cross-Referencing Strategy

### Step 1: Extract Words from Each Source

```python
# scripts/extract_sources.py

def extract_thdl(filepath):
    """Parse THDL dictionary XML/text"""
    words = []
    # Parse their format
    # Extract just the Tibetan headwords
    return words

def extract_monlam(filepath_or_api):
    """Extract from Monlam dataset"""
    words = []
    # If API available, fetch via API
    # Otherwise parse their export
    return words

def extract_rangjung_yeshe():
    """Extract from RY wiki"""
    words = []
    # Use MediaWiki API or export
    return words
```

### Step 2: Cross-Reference

```python
# scripts/build_corpus.py

def cross_reference(sources):
    """Combine sources, keep only validated words"""
    
    word_data = {}
    
    # Collect all words
    for source_name, words in sources.items():
        for word in words:
            normalized = normalize_tibetan(word)
            
            if normalized not in word_data:
                word_data[normalized] = {
                    'word': word,
                    'sources': [],
                    'source_count': 0
                }
            
            word_data[normalized]['sources'].append(source_name)
            word_data[normalized]['source_count'] += 1
    
    # Filter: Keep only words in 2+ sources
    validated = {
        word: data 
        for word, data in word_data.items() 
        if data['source_count'] >= 2
    }
    
    print(f"Total unique words: {len(word_data)}")
    print(f"Validated (2+ sources): {len(validated)}")
    
    return validated

# Usage
sources = {
    'thdl': extract_thdl('data/thdl_dict.xml'),
    'monlam': extract_monlam('data/monlam_export.json'),
    'rangjung_yeshe': extract_rangjung_yeshe(),
}

corpus = cross_reference(sources)
```

### Step 3: Quality Checks

```python
def validate_corpus(corpus):
    """Sanity checks before importing"""
    
    issues = []
    
    for word, data in corpus.items():
        # Check 1: Valid Tibetan Unicode
        if not all('\u0F00' <= c <= '\u0FFF' for c in word 
                   if not c in [' ', '་', '།']):
            issues.append(f"Non-Tibetan chars: {word}")
        
        # Check 2: Not too long (likely extraction error)
        if len(word) > 50:
            issues.append(f"Suspiciously long: {word}")
        
        # Check 3: Not empty
        if not word.strip():
            issues.append(f"Empty word")
    
    print(f"Found {len(issues)} potential issues")
    return issues

# Manual review of issues
```

### Step 4: Load to Database

```python
def load_to_database(corpus):
    """Import validated corpus"""
    
    for word, data in corpus.items():
        SpellingReference.create(
            word=data['word'],
            word_normalized=word,
            source_count=data['source_count'],
            sources=data['sources'],  # Store as array
            confidence_score=calculate_confidence(data),
            first_seen_in=data['sources'][0]
        )
```

---

## Licensing Considerations

**Need to Check:**
- THDL: Likely open for educational use
- Monlam: Need permission for redistribution
- Rangjung Yeshe: Creative Commons (check specifics)

**Attribution Plan:**
```
In application footer/about:
"Word corpus sourced from:
- Tibetan & Himalayan Digital Library (THDL)
- Monlam IT Research Centre
- Rangjung Yeshe Wiki
With gratitude to these projects."
```

Corpus is sourced from academic and open resources, cross-referenced for quality, with proper attribution. This approach balances coverage, quality, and legal compliance.

---

## Recommended Approach

### Phase 1: Start with THDL + Rangjung Yeshe

**Why:**
- ✅ Both are accessible
- ✅ Likely open licensing
- ✅ ~70,000 words combined
- ✅ Good overlap for cross-referencing
- ✅ Can get started immediately

**Process:**
1. Download THDL dictionary
2. Export Rangjung Yeshe via MediaWiki API
3. Cross-reference (keep 2+ sources)
4. Results: ~20,000-30,000 validated words
5. Good enough for MVP!

### Phase 2: Add Monlam (If Accessible)

**If we get Monlam access:**
- Add as third source
- Re-run cross-reference
- Likely 40,000-50,000 words
- Higher confidence scores

### Fallback: Frequency Corpus

**If licensing problems:**
- Use public domain Tibetan texts
- Extract words with frequency
- Keep words appearing 5+ times
- Start smaller (~10,000-15,000 words)
- Grows over time

---

## Data Quality Metrics

**Track these in database:**

```sql
-- Corpus statistics table
CREATE TABLE corpus_metadata (
    id SERIAL PRIMARY KEY,
    total_words INTEGER,
    source_breakdown JSONB,  -- {"thdl": 45000, "monlam": 80000}
    build_date TIMESTAMP,
    cross_reference_threshold INTEGER,  -- Required sources
    notes TEXT
);
```

**Monitor during usage:**
```sql
-- Which words are users encountering that we don't have?
SELECT word, COUNT(*) as encounters
FROM spell_errors
WHERE error_type = 'not_in_dictionary'
GROUP BY word
ORDER BY encounters DESC
LIMIT 100;

-- These are candidates for Phase 3 user submissions
```

---

## Action Items Before Building

1. **Research THDL access**
   - Visit thlib.org
   - Locate dictionary downloads
   - Check license terms

2. **Test Rangjung Yeshe API**
   - Try MediaWiki API export
   - Check data format
   - Verify we can extract words

3. **Contact Monlam** (optional for MVP)
   - Email for research access
   - Can add later if approved

4. **Prepare test set**
   - Get your sample PDFs
   - Manual spell check one
   - Use as ground truth for testing

---

## Estimated Timeline for Corpus

**If THDL + RY available:**
- Download/extract: 2-4 hours
- Cross-reference script: 2 hours
- Quality checking: 2 hours
- Load to database: 1 hour
- **Total: ~1 day** (can be done early)

**Can work in parallel:**
- You/I extract word lists
- While that's happening: build spell check engine
- Integrate when corpus ready

---

## Corpus Approach Summary

The initial corpus uses a multi-source approach:

1. **Identified sources**: THDL (academic), Rangjung Yeshe (Buddhist), considered Monlam
2. **Cross-referenced**: Only kept words appearing in 2+ sources
3. **Quality over quantity**: ~30k validated words vs 100k uncertain
4. **Tracked provenance**: Database stores which sources confirm each word
5. **Confidence scoring**: Can tune threshold based on performance

This approach balances coverage with data quality and allows expansion over time.
Trade-off: could have a larger corpus with a single source, but at a higher error rate. Quality was prioritized for the MVP.

