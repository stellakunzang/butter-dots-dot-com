# Tibetan Unicode Encoding Rules - CRITICAL FOR PARSING

**Date**: 2026-02-09  
**Status**: 🔥 CRITICAL - This is how Tibetan syllables are ACTUALLY encoded

## The Key Insight

Tibetan uses **TWO different Unicode ranges** for consonants depending on their position in the syllable stack!

## Unicode Ranges

### 1. BASE CONSONANTS (U+0F40 - U+0F6C)
Used when the consonant is:
- A **prefix** (before the stack)
- A **superscript** (above the root)
- A **suffix** (after the root)
- A **post-suffix** (after the suffix)
- A **standalone root** (no superscript above it)

**Examples:**
- ཀ (ka) = U+0F40
- ག (ga) = U+0F42
- ད (da) = U+0F51
- བ (ba) = U+0F56
- ར (ra) = U+0F62
- ལ (la) = U+0F63
- ས (sa) = U+0F66

### 2. SUBJOINED CONSONANTS (U+0F90 - U+0FBC)
Used when the consonant is:
- A **root below a superscript**
- A **subscript below the root**

**Examples:**
- ྐ (subjoined ka) = U+0F90
- ྒ (subjoined ga) = U+0F92
- ྱ (subjoined ya/ya-btags) = U+0FB1
- ྲ (subjoined ra/ra-btags) = U+0FB2
- ླ (subjoined la/la-btags) = U+0FB3
- ྭ (subjoined wa/wa-zur) = U+0FAD

**Mapping:** Subjoined consonant = Base consonant + 0x50
- U+0F42 (ག ga) + 0x50 = U+0F92 (ྒ subjoined ga)
- U+0F40 (ཀ ka) + 0x50 = U+0F90 (ྐ subjoined ka)

### 3. VOWELS (U+0F71 - U+0F7C)
- ི (i) = U+0F72
- ུ (u) = U+0F74
- ེ (e) = U+0F7A
- ོ (o) = U+0F7C
- (a is unmarked)

## Real Word Examples

### རྒྱལ (rgyal - "king")

```
Unicode: ར ྒ ྱ ལ
         U+0F62 U+0F92 U+0FB1 U+0F63

Position 0: ར (U+0F62) BASE ra
  → SUPERSCRIPT (ra-mgo)

Position 1: ྒ (U+0F92) SUBJOINED ga
  → ROOT (below the superscript)

Position 2: ྱ (U+0FB1) SUBJOINED ya
  → SUBSCRIPT (ya-btags, below the root)

Position 3: ལ (U+0F63) BASE la
  → SUFFIX

Structure: SUPERSCRIPT + ROOT + SUBSCRIPT + SUFFIX
```

### བསྒྲུབས (bsgrubs - "accomplished")

```
Unicode: བ ས ྒ ྲ ུ བ ས
         U+0F56 U+0F66 U+0F92 U+0FB2 U+0F74 U+0F56 U+0F66

Position 0: བ (U+0F56) BASE ba
  → PREFIX

Position 1: ས (U+0F66) BASE sa
  → SUPERSCRIPT (sa-mgo)

Position 2: ྒ (U+0F92) SUBJOINED ga
  → ROOT (below superscript)

Position 3: ྲ (U+0FB2) SUBJOINED ra
  → SUBSCRIPT (ra-btags, below root)

Position 4: ུ (U+0F74) VOWEL u

Position 5: བ (U+0F56) BASE ba
  → SUFFIX

Position 6: ས (U+0F66) BASE sa
  → POST-SUFFIX

Structure: PREFIX + SUPERSCRIPT + ROOT + SUBSCRIPT + VOWEL + SUFFIX + POST-SUFFIX
(All 7 positions!)
```

### དབང (dbang - "power")

```
Unicode: ད བ ང
         U+0F51 U+0F56 U+0F44

Position 0: ད (U+0F51) BASE da
  → PREFIX

Position 1: བ (U+0F56) BASE ba
  → ROOT (no superscript, so uses base form)

Position 2: ང (U+0F44) BASE nga
  → SUFFIX

Structure: PREFIX + ROOT + SUFFIX
```

### སྒྲུབ (sgrub - "accomplish")

```
Unicode: ས ྒ ྲ ུ བ
         U+0F66 U+0F92 U+0FB2 U+0F74 U+0F56

Position 0: ས (U+0F66) BASE sa
  → SUPERSCRIPT (sa-mgo)

Position 1: ྒ (U+0F92) SUBJOINED ga
  → ROOT (below superscript)

Position 2: ྲ (U+0FB2) SUBJOINED ra
  → SUBSCRIPT (ra-btags)

Position 3: ུ (U+0F74) VOWEL u

Position 4: བ (U+0F56) BASE ba
  → SUFFIX

Structure: SUPERSCRIPT + ROOT + SUBSCRIPT + VOWEL + SUFFIX
```

## Parsing Algorithm

```python
def parse_tibetan_syllable(syllable_chars):
    """
    Parse a Tibetan syllable based on Unicode ranges.
    
    syllable_chars: list of Unicode characters (without tsheg)
    """
    prefix = None
    superscript = None
    root = None
    subscripts = []
    vowels = []
    suffix = None
    post_suffix = None
    
    i = 0
    
    # 1. Check for PREFIX (must be one of 5: ga, da, ba, ma, ra)
    if is_prefix(syllable_chars[i]):
        prefix = syllable_chars[i]
        i += 1
    
    # 2. Check for SUPERSCRIPT (next BASE consonant if followed by SUBJOINED)
    if i < len(syllable_chars) and is_base_consonant(syllable_chars[i]):
        if i+1 < len(syllable_chars) and is_subjoined_consonant(syllable_chars[i+1]):
            superscript = syllable_chars[i]
            i += 1
    
    # 3. Get ROOT
    if i < len(syllable_chars):
        if is_subjoined_consonant(syllable_chars[i]):
            # Root is below superscript
            root = syllable_chars[i]
            i += 1
        elif is_base_consonant(syllable_chars[i]):
            # Standalone root (no superscript)
            root = syllable_chars[i]
            i += 1
    
    # 4. Collect SUBSCRIPTS (any remaining subjoined consonants)
    while i < len(syllable_chars) and is_subjoined_consonant(syllable_chars[i]):
        subscripts.append(syllable_chars[i])
        i += 1
    
    # 5. Collect VOWELS
    while i < len(syllable_chars) and is_vowel(syllable_chars[i]):
        vowels.append(syllable_chars[i])
        i += 1
    
    # 6. Get SUFFIX (next base consonant)
    if i < len(syllable_chars) and is_base_consonant(syllable_chars[i]):
        suffix = syllable_chars[i]
        i += 1
    
    # 7. Get POST-SUFFIX (only da or sa after suffix)
    if i < len(syllable_chars) and suffix is not None:
        if is_post_suffix(syllable_chars[i]):
            post_suffix = syllable_chars[i]
            i += 1
    
    return {
        'prefix': prefix,
        'superscript': superscript,
        'root': root,
        'subscripts': subscripts,
        'vowels': vowels,
        'suffix': suffix,
        'post_suffix': post_suffix
    }

def is_base_consonant(char):
    return 0x0F40 <= ord(char) <= 0x0F6C

def is_subjoined_consonant(char):
    return 0x0F90 <= ord(char) <= 0x0FBC

def is_vowel(char):
    return 0x0F71 <= ord(char) <= 0x0F7C

def is_prefix(char):
    # Only 5 letters can be prefixes
    return char in ['ག', 'ད', 'བ', 'མ', 'ར']

def is_post_suffix(char):
    # Only da and sa can be post-suffixes
    return char in ['ད', 'ས']
```

## Validation Rules

After parsing, validate:

1. **Prefix rules**: If prefix exists, check against invalid prefix+root combinations
2. **Superscript rules**: If superscript exists, check against invalid superscript+root combinations
3. **Subscript rules**: Check each subscript is valid with the root
4. **Suffix rules**: Verify suffix is one of the 10 valid suffixes
5. **Post-suffix rules**: Verify post-suffix only appears after a suffix

## Critical Implications

1. **Parsing is position-based, not just character-based**
2. **The same phonetic sound uses DIFFERENT Unicode** depending on position:
   - ག (ga) as prefix/suffix = U+0F42 (BASE)
   - ྒ (ga) as root under superscript = U+0F92 (SUBJOINED)
3. **We can't just look at the character, we must look at the sequence**
4. **Validation patterns work with these ranges** - need to check both

## Next Steps

1. Update syllable parser to use these Unicode ranges
2. Test with real Tibetan words
3. Verify against validation regex patterns
4. Handle edge cases (standalone subscripts, etc.)
