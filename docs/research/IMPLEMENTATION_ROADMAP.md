# Implementation Roadmap - Phase 1 Spellchecker

**Status**: Ready to implement with validated understanding  
**Date**: 2026-02-09

## What We've Learned

### 1. Syllable Structure ✅
- Tibetan syllables have up to 7 components
- Only the ROOT is required, everything else is optional
- Structure: PREFIX + SUPERSCRIPT + ROOT + SUBSCRIPT + VOWEL + SUFFIX + POST-SUFFIX

### 2. Unicode Encoding ✅
**CRITICAL DISCOVERY:** Tibetan uses different Unicode ranges depending on position:
- **BASE range (U+0F40-0F6C)**: prefix, superscript, suffix, post-suffix, standalone root
- **SUBJOINED range (U+0F90-0FBC)**: root under superscript, subscripts
- **Offset**: Subjoined = Base + 0x50

### 3. Prefix Rules ✅
- Only 5 letters can be prefixes: ག, ད, བ, མ, ར
- Each has specific invalid combinations (documented in `PREFIX_RULES_REFERENCE.md`)
- Example: ག cannot prefix ཀ, པ, ཧ, etc.

### 4. Common Mistakes Identified ✅
- ❌ Assuming first letter is always a prefix
- ❌ Not distinguishing root from prefix
- ❌ Thinking ལང is invalid (it's valid! ལ=root, ང=suffix)
- ❌ Thinking གང is invalid (it's valid! ག=prefix, ང=root)

### 5. Valid Suffixes ✅
10 letters can be suffixes: ག, ང, ད, ན, བ, མ, འ, ར, ལ, ས

### 6. Test Suite Created ✅
- `test_real_tibetan_words.py` with actual Tibetan vocabulary
- Tests simple, complex, valid, and invalid patterns
- Pressure tests our understanding

## Implementation Order

### Step 1: Syllable Parser (NEXT)
**File**: `backend/app/spellcheck/syllable_parser.py`

```python
class TibetanSyllableParser:
    def parse(self, syllable: str) -> dict:
        """
        Parse syllable into components based on Unicode ranges.
        
        Returns:
            {
                'prefix': str | None,
                'superscript': str | None,
                'root': str,
                'subscripts': list[str],
                'vowels': list[str],
                'suffix': str | None,
                'post_suffix': str | None
            }
        """
```

**Key features:**
- Use Unicode ranges to identify position
- Handle BASE vs SUBJOINED forms
- Return structured components

**Tests**: `backend/tests/test_syllable_parser.py` (already exists)

### Step 2: Rules Validator
**File**: `backend/app/spellcheck/rules.py`

```python
# Constants
VALID_PREFIXES = {'ག', 'ད', 'བ', 'མ', 'ར'}
VALID_SUPERSCRIPTS = {'ར', 'ལ', 'ས'}
VALID_SUBSCRIPTS = {'\u0FB1', '\u0FB2', '\u0FB3', '\u0FAD'}
VALID_SUFFIXES = {'ག', 'ང', 'ད', 'ན', 'བ', 'མ', 'འ', 'ར', 'ལ', 'ས'}
VALID_POST_SUFFIXES = {'ད', 'ས'}

# Invalid prefix combinations
INVALID_PREFIX_COMBOS = {
    'ག': {'\u0F40', '\u0F41', '\u0F46', '\u0F47', ...},
    'ད': {'\u0F41', '\u0F45', '\u0F46', '\u0F47', ...},
    # ... (see PREFIX_RULES_REFERENCE.md)
}

def is_valid_prefix_combination(prefix: str, root: str) -> bool:
    """Check if prefix + root combination is valid"""
    
def is_valid_superscript_combination(superscript: str, root: str) -> bool:
    """Check if superscript + root combination is valid"""
    
def is_valid_subscript_combination(root: str, subscript: str) -> bool:
    """Check if root + subscript combination is valid"""
```

**Tests**: `backend/tests/test_rules.py` (already exists)

### Step 3: Pattern Validator
**File**: `backend/app/spellcheck/patterns.py`

Implement "exclusive" validation patterns:
- Syllable too long (8+ letters)
- Invalid stacking patterns
- Encoding errors
- etc.

**Reference**: `docs/research/Tibetan_Spellchecker_vba.txt` lines 119-881

### Step 4: Main Engine
**File**: `backend/app/spellcheck/engine.py`

```python
class TibetanSpellChecker:
    def check_text(self, text: str) -> list[dict]:
        """
        Check Tibetan text for spelling errors.
        
        Returns list of errors with position info.
        """
        # 1. Normalize text (NFD)
        # 2. Split into syllables (by tsheg)
        # 3. Parse each syllable
        # 4. Validate structure
        # 5. Check against invalid patterns
        # 6. Return errors
```

**Tests**: `backend/tests/test_engine.py` (already exists)

### Step 5: Integration Tests
Run full tests with:
- Real Tibetan words (from `test_real_tibetan_words.py`)
- Pressure test suite
- Edge cases

## Testing Strategy

### Phase 1: Unit Tests
- Test each component independently
- Verify Unicode range detection
- Test prefix/suffix rules

### Phase 2: Integration Tests
- Test full syllable parsing
- Test full validation pipeline
- Use real Tibetan words

### Phase 3: Pressure Testing
- 100+ real Tibetan words
- Buddhist terminology
- Common vocabulary
- Edge cases

### Phase 4: Validation with Test Data
- Run tests with real Tibetan texts
- Validate results against expected outcomes
- Fix any discrepancies

## Reference Documents

All in `/docs/research/`:
- ✅ `TIBETAN_SYLLABLE_STRUCTURE.md` - Syllable components explained
- ✅ `CRITICAL_FINDINGS_SYLLABLE_STRUCTURE.md` - Mistakes we found
- ✅ `UNICODE_ENCODING_RULES.md` - How Unicode encodes syllables
- ✅ `PREFIX_RULES_REFERENCE.md` - Complete prefix rules
- ✅ `PRESSURE_TEST_WORDS.md` - Test words and expected results
- ✅ `Tibetan_Spellchecker_vba.txt` - Historical VBA reference
- ✅ `SCRIPT_ANALYSIS.md` - Historical analysis of VBA approach

## Implementation Checklist

### Syllable Parser
- [ ] Implement Unicode range detection
- [ ] Parse prefix
- [ ] Parse superscript
- [ ] Parse root (BASE vs SUBJOINED)
- [ ] Parse subscripts
- [ ] Parse vowels
- [ ] Parse suffix
- [ ] Parse post-suffix
- [ ] Handle edge cases
- [ ] Run unit tests

### Rules Validator
- [ ] Implement prefix validation
- [ ] Load invalid prefix combinations
- [ ] Implement superscript validation
- [ ] Implement subscript validation
- [ ] Implement suffix validation
- [ ] Run unit tests

### Pattern Validator
- [ ] Port validation regex patterns to Python
- [ ] Implement "too long" check
- [ ] Implement invalid stacking check
- [ ] Implement encoding error check
- [ ] Run unit tests

### Main Engine
- [ ] Implement text normalization
- [ ] Implement syllable splitting
- [ ] Integrate parser
- [ ] Integrate validators
- [ ] Implement error reporting
- [ ] Run integration tests

### Validation
- [ ] Test with 100+ real Tibetan words
- [ ] Validate against expected results
- [ ] Document any discrepancies
- [ ] Fix edge cases
- [ ] Update docs

## Success Criteria

Phase 1 is complete when:
1. ✅ All unit tests pass
2. ✅ All integration tests pass
3. ✅ Real Tibetan words test correctly
4. ✅ Results validated against linguistic rules
5. ✅ Edge cases documented
6. ✅ Code is well-documented
7. ✅ Ready for API integration

## Timeline Estimate

- Syllable Parser: 2-3 hours
- Rules Validator: 2-3 hours
- Pattern Validator: 3-4 hours
- Main Engine: 2-3 hours
- Testing & Validation: 3-4 hours
- Documentation: 1-2 hours

**Total: ~15-20 hours** for complete Phase 1 implementation

## Next Immediate Step

**START HERE:** Implement `TibetanSyllableParser` in `backend/app/spellcheck/syllable_parser.py`

Use the parsing algorithm from `UNICODE_ENCODING_RULES.md` as the starting point.

Test with:
- བོད (simple)
- དབང (prefix)
- རྒྱལ (superscript + subscript)
- བསྒྲུབས (all 7 components)
