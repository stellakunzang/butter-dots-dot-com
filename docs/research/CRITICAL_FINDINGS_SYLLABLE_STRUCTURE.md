# CRITICAL FINDINGS: Tibetan Syllable Structure Misunderstanding

**Date**: 2026-02-09  
**Status**: 🚨 CRITICAL - Affects core spellchecker logic  
**Reporter**: User (Stella)

## The Problem

**Test on line 176 of `test_engine.py` incorrectly marks ལང་ as invalid.**

```python
text = "བོད་ལང་ཡིག་"  # valid + invalid + valid  ← WRONG COMMENT!
```

**ལང་ is VALID Tibetan!**

## Why This Matters

This reveals a fundamental misunderstanding of Tibetan syllable structure that affects the entire spellchecker implementation.

## The Misunderstanding

### ❌ WRONG Assumption:
"ལ (la) is a prefix before ང (nga), so it needs to be validated as a prefix+root combination"

### ✅ CORRECT Understanding:
"ལ (la) is the ROOT LETTER, and ང (nga) is a SUFFIX"

## Tibetan Syllable Structure (Corrected)

```
[PREFIX] + [SUPERSCRIPT] + **ROOT** + [SUBSCRIPT] + [VOWEL] + [SUFFIX] + [POST-SUFFIX]
                           ^^^^^^^^
                         ONLY THIS IS REQUIRED
```

### Position 1: PREFIX (optional)
**ONLY 5 letters can be prefixes:**
- ག (ga) - U+0F42
- ད (da) - U+0F51  
- བ (ba) - U+0F56
- མ (ma) - U+0F58
- ར (ra) - U+0F60

**Position:** BEFORE the root
**ལ (la) is NOT a prefix!**

### Position 2: SUPERSCRIPT (optional)
**Only 3 letters can be superscripts:**
- ར (ra-mgo) - U+0F62
- ལ (la-mgo) - U+0F63  ← la CAN be a superscript
- ས (sa-mgo) - U+0F66

**Position:** ABOVE the root (requires combining with another letter below)
**In ལང་, la is NOT functioning as a superscript**

### Position 3: ROOT (REQUIRED)
**ANY of the 30 Tibetan consonants can be a root letter**

Range: U+0F40 to U+0F68

**In ལང་, ལ (la) is the ROOT LETTER!**

### Position 6: SUFFIX (optional)
**10 letters can be suffixes:**
- ག (ga) - U+0F42
- **ང (nga) - U+0F44** ← VALID SUFFIX!
- ད (da) - U+0F51
- ན (na) - U+0F53
- བ (ba) - U+0F56
- མ (ma) - U+0F58
- འ (ah) - U+0F60
- ར (ra) - U+0F62
- ལ (la) - U+0F63
- ས (sa) - U+0F66

**Position:** AFTER the root (and vowel if present)
**In ལང་, ང (nga) is a VALID SUFFIX!**

## Analysis of ལང་

```
Unicode breakdown:
ལ = U+0F63 (la)
ང = U+0F44 (nga)
་ = U+0F0B (tsheg - syllable separator)

Structure:
ལ = ROOT LETTER
ང = SUFFIX

Validation:
✓ Has required root letter
✓ Suffix (nga) is one of the 10 valid suffixes
✓ No invalid patterns detected

Result: VALID TIBETAN SYLLABLE
```

## Examples of Valid Syllables

### Simple root + suffix:
```
ལང་ = ལ (root) + ང (suffix) = VALID
བོད = བ (root) + vowel o + ད (suffix) = VALID
ཡིག = ཡ (root) + vowel i + ག (suffix) = VALID
```

### With prefix:
```
གཡང་ = ག (prefix) + ཡ (root) + ང (suffix) = VALID
དབང་ = ད (prefix) + བ (root) + ང (suffix) = VALID
```

### With superscript:
```
ལྒ = ལ (superscript la-mgo) + ག (root) = VALID
      ↑ HERE la is a superscript, not a root!
```

## What Paul Hackett's VBA Actually Does

Paul Hackett uses **"exclusive" spellchecking**:
- Looks for INVALID patterns only
- Does NOT validate entire syllable structures
- If a syllable doesn't match any invalid pattern → it's considered valid

**Key insight:** Hackett's patterns check for:
1. Invalid prefix + root combinations
2. Invalid superscript + subscript combinations  
3. Invalid subscript combinations
4. Too many letters
5. Encoding errors

**Hackett does NOT explicitly validate suffixes** because:
- Suffix validation would be "inclusive" checking
- His approach is "exclusive" - only flag what's wrong
- Valid suffixes are implicitly accepted

## Files That Need Updating

### 1. `/backend/tests/test_engine.py`
✅ FIXED - Lines 176 and 193

### 2. `/backend/app/spellcheck/syllable_parser.py` (when created)
**Must correctly identify:**
- What is a prefix (only 5 letters)
- What is a superscript (only when combining)
- What is the ROOT (the main consonant)
- What is a suffix (comes after root)

**Critical logic:**
```python
def identify_root(syllable):
    """
    Find the root letter:
    1. If there's a subscript -> letter ABOVE subscript is root
    2. If there's a superscript -> letter BELOW superscript is root
    3. If first letter is a prefix (ga/da/ba/ma/ra) -> second letter is root
    4. Otherwise -> first consonant is root
    """
```

### 3. `/backend/app/spellcheck/rules.py` (when created)
**Must implement:**
- Prefix validation (only for the 5 prefix letters)
- Superscript/subscript validation
- Suffix validation (10 valid suffixes)
- Post-suffix validation (only da and sa)

**Must NOT:**
- Treat every first letter as a prefix
- Assume suffixes need special validation rules
- Confuse root letters with prefixes

### 4. All test files
**Review every test that uses Tibetan text** to ensure:
- Comments correctly identify structure
- "Valid" examples are actually valid
- "Invalid" examples are actually invalid

## Action Items

- [x] Fix test comments in `test_engine.py`
- [x] Create `TIBETAN_SYLLABLE_STRUCTURE.md` reference doc
- [x] Create this `CRITICAL_FINDINGS` document
- [ ] Implement correct syllable parsing logic
- [ ] Verify all Tibetan examples in tests are correctly labeled
- [ ] Test with known valid words: བོད་, ལང་, དབང་, རྒྱ་, etc.
- [ ] Re-read Paul Hackett's VBA patterns with correct understanding

## References

1. FPMT Mandala: "Suffixes and Finding the Root Letter of a Syllable"
2. Rigpa Wiki: "Tibetan Grammar - Formation of the Tibetan Syllable"  
3. Paul Hackett's Tibetan Spellchecker VBA (2011) - `/docs/research/Tibetan_Spellchecker_vba.txt`
4. Our reference: `/docs/research/TIBETAN_SYLLABLE_STRUCTURE.md`

## Key Takeaway

**Don't assume the first letter is a prefix!**

The root letter is the center of the syllable. Everything else positions itself relative to the root:
- Prefix comes BEFORE root
- Superscript goes ABOVE root
- Subscript goes BELOW root
- Suffix comes AFTER root

Only by correctly identifying the root can we properly validate the syllable structure.
