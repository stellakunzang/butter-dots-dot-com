# DRY (Don't Repeat Yourself) Cleanup Summary

**Date**: February 9, 2026  
**Result**: Eliminated duplicate constant definitions ✅

## Problem Identified

Three constants were duplicated in both `syllable_parser.py` and `rules.py`:
- `VALID_PREFIXES` - The 6 valid prefix letters
- `VALID_SUPERSCRIPTS` - The 3 valid superscript letters  
- `VALID_POST_SUFFIXES` - The 2 valid post-suffix letters

This violated the **DRY principle** and created maintenance risk (updating one place but forgetting the other).

## Solution Applied

Consolidated all shared constants in **`rules.py`** (the authoritative source for validation rules) and have **`syllable_parser.py`** import them.

### Changes Made

**File**: `backend/app/spellcheck/syllable_parser.py`

**Before**:
```python
# The 6 valid prefixes (including 'a-chung)
VALID_PREFIXES = {'ག', 'ད', 'བ', 'མ', 'འ', 'ར'}

# The 3 valid superscripts
VALID_SUPERSCRIPTS = {'ར', 'ལ', 'ས'}

# Valid post-suffixes (only these 2)
VALID_POST_SUFFIXES = {'ད', 'ས'}
```

**After**:
```python
# Import shared constants from rules module (DRY principle)
from app.spellcheck.rules import (
    VALID_PREFIXES,
    VALID_SUPERSCRIPTS, 
    VALID_POST_SUFFIXES,
    VALID_SUFFIXES
)
```

Also removed duplicate import of `VALID_SUFFIXES` inside a function (line 236).

## Benefits

1. **Single Source of Truth**: Constants defined in one place only (`rules.py`)
2. **Easier Maintenance**: Updates only need to happen in one file
3. **Consistency Guaranteed**: No risk of constants getting out of sync
4. **Clearer Architecture**: `rules.py` owns validation rules, `syllable_parser.py` imports what it needs

## Constants Now Centralized in `rules.py`

### Basic Structure Constants
- `VALID_PREFIXES` - 6 valid prefixes: ག ད བ མ འ ར
- `VALID_SUPERSCRIPTS` - 3 valid superscripts: ར ལ ས
- `VALID_SUBSCRIPTS` - 4 valid subscripts (subjoined form)
- `VALID_SUFFIXES` - 10 valid suffixes
- `VALID_POST_SUFFIXES` - 2 valid post-suffixes: ད ས

### Detailed Combination Rules
- `VALID_WA_ZUR_ROOTS` - Roots that can take wa-zur subscript
- `VALID_YA_BTAGS_ROOTS` - Roots that can take ya-btags subscript
- `VALID_RA_BTAGS_ROOTS` - Roots that can take ra-btags subscript
- `VALID_LA_BTAGS_ROOTS` - Roots that can take la-btags subscript
- `VALID_RA_MGO_ROOTS` - Roots that can have ra-mgo superscript
- `VALID_LA_MGO_ROOTS` - Roots that can have la-mgo superscript
- `VALID_SA_MGO_ROOTS` - Roots that can have sa-mgo superscript
- `INVALID_PREFIX_COMBOS` - Invalid prefix + root combinations

## Verification

✅ **All 100 tests passing**  
✅ **Test file validates correctly (0 errors)**  
✅ **No circular import issues**  
✅ **Code cleaner and more maintainable**

## Files Modified

- `backend/app/spellcheck/syllable_parser.py` - Removed duplicates, added import
- Lines reduced: ~10 lines of duplicate code eliminated

## Architecture

```
rules.py (Authoritative Source)
    ↓ exports constants
syllable_parser.py (Consumer)
    ↓ uses constants for parsing
engine.py (Consumer)
    ↓ uses both modules
```

This establishes a clear dependency hierarchy with no circular imports.
