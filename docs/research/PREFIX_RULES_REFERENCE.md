# Tibetan Prefix Rules - Complete Reference

**Source**: Traditional Tibetan grammar rules and linguistic research

## The 5 Valid Prefixes

Only these 5 letters can function as prefixes:
- ག (ga) - U+0F42
- ད (da) - U+0F51
- བ (ba) - U+0F56
- མ (ma) - U+0F58
- ར (ra) - U+0F60

**Note**: These same letters can also be:
- Root letters (when they're the main consonant)
- Suffixes (when they come after the root)

## Invalid Prefix + Root Combinations

Validation approach: **"Exclusive" checking** - only flag what's INVALID

### ག (ga) prefix - CANNOT prefix these roots:

- ཀ (ka) - U+0F40
- ཁ (kha) - U+0F41
- ཆ (cha) - U+0F46
- ཇ (ja) - U+0F47
- ཐ (tha) - U+0F50
- ཚ (tsa) - U+0F5A
- པ (pa) - U+0F54
- ཕ (pha) - U+0F55
- ཛ (dza) - U+0F5B
- ཝ (wa) - U+0F5D
- ཧ (ha) - U+0F67

**Examples of INVALID:**
```
གཀ = ga + ka = INVALID
གཔ = ga + pa = INVALID
གཧ = ga + ha = INVALID
```

**Examples of VALID:**
```
གང = ga + nga = VALID
གཡ = ga + ya = VALID
གད = ga + da = VALID
གཉ = ga + nya = VALID
```

### ད (da) prefix - CANNOT prefix these roots:

- ཁ (kha) - U+0F41
- ཅ (ca) - U+0F45
- ཆ (cha) - U+0F46
- ཇ (ja) - U+0F47
- ཉ (nya) - U+0F49
- ཐ (tha) - U+0F50
- ཕ (pha) - U+0F55
- ཙ (tsa) - U+0F59
- ཚ (tsa) - U+0F5A
- ཛ (dza) - U+0F5B
- ཝ (wa) - U+0F5D
- ཞ (zha) - U+0F5E
- ཟ (za) - U+0F5F
- ཡ (ya) - U+0F61
- ལ (la) - U+0F64
- ཧ (ha) - U+0F67

**Examples of INVALID:**
```
དཁ = da + kha = INVALID
དཕ = da + pha = INVALID
དཡ = da + ya = INVALID
```

**Examples of VALID:**
```
དཀ = da + ka = VALID
དག = da + ga = VALID
དབ = da + ba = VALID
དམ = da + ma = VALID
དང = da + nga = VALID
```

### བ (ba) prefix - CANNOT prefix these roots:

- ཁ (kha) - U+0F41
- ཆ (cha) - U+0F46
- ཇ (ja) - U+0F47
- ཊ (tta) - U+0F49
- ཐ (tha) - U+0F50
- པ (pa) - U+0F54
- ཕ (pha) - U+0F55
- ཚ (tsa) - U+0F5A
- ཛ (dza) - U+0F5B
- ཝ (wa) - U+0F5D
- ཡ (ya) - U+0F61
- ཧ (ha) - U+0F67

**Examples of INVALID:**
```
བཁ = ba + kha = INVALID
བཔ = ba + pa = INVALID
བཡ = ba + ya = INVALID
```

**Examples of VALID:**
```
བཀ = ba + ka = VALID
བག = ba + ga = VALID
བད = ba + da = VALID
བང = ba + nga = VALID
```

### མ (ma) prefix - CANNOT prefix these roots:

- ཀ (ka) - U+0F40
- ཅ (ca) - U+0F45
- ཎ (nna) - U+0F4F
- པ (pa) - U+0F54
- ཕ (pha) - U+0F55
- ཙ (tsa) - U+0F59
- ཝ (wa) - U+0F5D
- ཞ (zha) - U+0F5E
- ཟ (za) - U+0F5F
- ཡ (ya) - U+0F61
- ལ (la) - U+0F64
- ཧ (ha) - U+0F67

**Examples of INVALID:**
```
མཀ = ma + ka = INVALID
མཔ = ma + pa = INVALID
མཡ = ma + ya = INVALID
```

**Examples of VALID:**
```
མག = ma + ga = VALID
མང = ma + nga = VALID
མད = ma + da = VALID
མཁ = ma + kha = VALID
```

### ར (ra) prefix - CANNOT prefix these roots:

- ཀ (ka) - U+0F40
- ཅ (ca) - U+0F45
- ཊ (tta) - U+0F49
- པ (pa) - U+0F54
- ཎ (nna) - U+0F4F
- ཙ (tsa) - U+0F59
- ཞ (zha) - U+0F5E
- ཟ (za) - U+0F5F
- ཡ (ya) - U+0F61
- ལ (la) - U+0F64
- ཝ (wa) - U+0F5D
- ཧ (ha) - U+0F67

**Examples of INVALID:**
```
རཀ = ra + ka = INVALID
རཔ = ra + pa = INVALID
རཡ = ra + ya = INVALID
```

**Examples of VALID:**
```
རག = ra + ga = VALID
རང = ra + nga = VALID
རད = ra + da = VALID
རཁ = ra + kha = VALID
```

## Implementation Strategy

```python
# Define invalid combinations as sets for O(1) lookup
INVALID_PREFIX_COMBOS = {
    'ག': {'\u0F40', '\u0F41', '\u0F46', '\u0F47', '\u0F50', 
          '\u0F5A', '\u0F54', '\u0F55', '\u0F5B', '\u0F5D', '\u0F67'},
    'ད': {'\u0F41', '\u0F45', '\u0F46', '\u0F47', '\u0F49', '\u0F50',
          '\u0F55', '\u0F59', '\u0F5A', '\u0F5B', '\u0F5D', '\u0F5E',
          '\u0F5F', '\u0F61', '\u0F64', '\u0F67'},
    'བ': {'\u0F41', '\u0F46', '\u0F47', '\u0F49', '\u0F50', '\u0F54',
          '\u0F55', '\u0F5A', '\u0F5B', '\u0F5D', '\u0F61', '\u0F67'},
    'མ': {'\u0F40', '\u0F45', '\u0F4F', '\u0F54', '\u0F55', '\u0F59',
          '\u0F5D', '\u0F5E', '\u0F5F', '\u0F61', '\u0F64', '\u0F67'},
    'ར': {'\u0F40', '\u0F45', '\u0F49', '\u0F54', '\u0F4F', '\u0F59',
          '\u0F5E', '\u0F5F', '\u0F61', '\u0F64', '\u0F5D', '\u0F67'}
}

def is_valid_prefix_combination(prefix, root):
    """
    Check if a prefix + root combination is valid.
    
    Returns:
        True if valid
        False if invalid
    """
    # If the prefix is not one of the 5 valid prefixes, return False
    if prefix not in VALID_PREFIXES:
        return False
    
    # Check if this specific combination is invalid
    if prefix in INVALID_PREFIX_COMBOS:
        if root in INVALID_PREFIX_COMBOS[prefix]:
            return False
    
    return True
```

## Key Points

1. **Exclusive checking**: Only INVALID combinations are listed, not all valid ones
2. **If not listed as invalid → it's valid**: If a prefix+root pair isn't in the invalid list, assume it's valid
3. **Context matters**: ག can be a prefix (before the root), a root (main letter), or a suffix (after the root)
4. **Common mistakes**:
   - Assuming all first letters are prefixes (WRONG)
   - Not distinguishing between prefix+root vs root+suffix
   - Thinking prefixes need to be "valid" - they just can't be in the invalid list

## Testing Strategy

```python
# Test that known valid combinations pass
assert is_valid_prefix_combination("ག", "ང") is True  # གང
assert is_valid_prefix_combination("ག", "ཡ") is True  # གཡ
assert is_valid_prefix_combination("ད", "ཀ") is True  # དཀ

# Test that known invalid combinations fail
assert is_valid_prefix_combination("ག", "ཀ") is False  # གཀ invalid
assert is_valid_prefix_combination("ག", "པ") is False  # གཔ invalid
assert is_valid_prefix_combination("ད", "ཡ") is False  # དཡ invalid

# Test that non-prefixes fail
assert is_valid_prefix_combination("ལ", "ཀ") is False  # la not a prefix
```

## References

- Traditional Tibetan grammar rules
- `/docs/research/Tibetan_Spellchecker_vba.txt` (historical VBA reference)
- `/docs/research/TIBETAN_SYLLABLE_STRUCTURE.md`
