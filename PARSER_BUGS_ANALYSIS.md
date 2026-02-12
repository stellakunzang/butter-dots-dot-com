# Critical Parser Bugs Found

**Date**: February 11, 2026

## Bug 1: Incorrect Root Identification

**Example**: ཅཡིག (ca + ya + i + ga)

**Current (Wrong) Parsing**:

- root: ཅ (ca)
- suffix: ཡ (ya)
- Missing: vowel ི and suffix ག

**Expected (Correct) Parsing**:

- prefix: ཅ (ca) _[or root if ca is not a valid prefix]_
- root: ཡ (ya)
- vowel: ི (i)
- suffix: ག (ga)

**Root Cause**: Parser doesn't look ahead for vowels when determining root vs
suffix. Vowels ALWAYS attach to the root, so if there's a vowel after a
consonant, that consonant must be the root.

## Bug 2: No Maximum Syllable Length Validation

**Issue**: Tibetan syllables have maximum 4 consonants (prefix +
superscript/subscript + root + suffix + post-suffix = 5 components max, but
overlapping roles).

**Examples of invalid structures**:

- Multiple suffixes beyond post-suffix (e.g., root + 3 suffixes)
- Too many consonants

**Current**: No validation for syllable length

## Bug 3: No Validation of Multiple Suffixes

**Issue**: Only TWO suffixes allowed maximum:

1. Primary suffix (10 valid: ག ང ད ན བ མ འ ར ལ ས)
2. Post-suffix (2 valid: ད ས)

**Current**: Parser might accept more suffixes without flagging error

## Proposed Fixes

### Fix 1: Look-Ahead for Vowels

When determining if a consonant is root vs suffix, check if there are vowels
following it:

```python
def parse(self, syllable: str):
    # ... existing prefix detection ...

    # NEW: Look ahead for vowels to identify root
    # The consonant before the first vowel is the root!
    first_vowel_index = None
    for idx, char in enumerate(chars):
        if is_vowel(char):
            first_vowel_index = idx
            break

    # If we have vowels, the preceding consonant is the root
    # (after accounting for prefix/superscript)
```

### Fix 2: Add Syllable Length Validation

```python
def validate_syllable_structure(parsed: dict) -> list:
    errors = []

    # Count consonants
    consonant_count = 0
    if parsed['prefix']: consonant_count += 1
    if parsed['superscript']: consonant_count += 1
    if parsed['root']: consonant_count += 1
    consonant_count += len(parsed['subscripts'])
    if parsed['suffix']: consonant_count += 1
    if parsed['post_suffix']: consonant_count += 1

    # Maximum 5 components (prefix + superscript + root + suffix + post-suffix)
    # Or maximum 4-5 consonants depending on structure
    if consonant_count > 5:
        errors.append({
            'error_type': 'syllable_too_long',
            'severity': 'error',
            'message': f'Syllable has too many consonants ({consonant_count})'
        })

    return errors
```

### Fix 3: Validate Suffix Rules

```python
# In validate_syllable_structure:

# Check for invalid multiple suffixes
if parsed['suffix'] and parsed['post_suffix']:
    # This is allowed (suffix + post-suffix)
    # But verify post-suffix is valid (ད or ས)
    if parsed['post_suffix'] not in VALID_POST_SUFFIXES:
        errors.append({
            'error_type': 'invalid_post_suffix',
            'severity': 'error',
            'message': f"'{parsed['post_suffix']}' is not a valid post-suffix"
        })

    # Verify suffix is valid
    if parsed['suffix'] not in VALID_SUFFIXES:
        errors.append({
            'error_type': 'invalid_suffix',
            'severity': 'error',
            'message': f"'{parsed['suffix']}' is not a valid suffix"
        })

# Check if we somehow have more than 2 suffixes (parser bug)
# This would be caught by syllable_too_long above
```

## Testing Requirements

### Test Cases for Bug 1

- ཅཡིག → should parse ཡ as root (has vowel after it)
- བརྗེད → བ prefix, ར superscript, ཇ root, ེ vowel, ད suffix
- རྒྱལ → ར prefix, ྒ root, ྱ subscript, ལ suffix

### Test Cases for Bug 2

- 6+ consonant syllables → should flag as too long
- Valid 5-component syllables → should pass

### Test Cases for Bug 3

- root + valid suffix + valid post-suffix → pass
- root + valid suffix + invalid post-suffix → error
- root + 3 suffixes → error (too long)

## Impact

**High Priority**: These bugs cause:

1. Incorrect error reporting (flagging wrong component)
2. Missing real errors (extra suffixes not caught)
3. User confusion (error messages point to wrong letters)

## Next Steps

1. Rewrite parser with vowel look-ahead
2. Add comprehensive syllable validation
3. Add test cases for all bugs
4. Update documentation
