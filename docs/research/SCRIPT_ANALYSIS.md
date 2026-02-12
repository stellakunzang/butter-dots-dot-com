# Analysis: Paul Hackett's Tibetan Spell Checker (2011)

**Source**: Columbia University, Paul G. Hackett  
**License**: GNU GPL (we can use it!)  
**Approach**: "Exclusive" rule-based (identifies INVALID patterns)

---

## How It Works

**Method**: Uses regex patterns to find INVALID letter combinations

**Color Coding** (3 severity levels):

- 🔴 **RED**: Encoding errors (wrong Unicode characters)
- 🟡 **YELLOW**: Invalid Tibetan letter combinations
- 🔵 **BLUE/TURQUOISE**: Sanskrit transliterations (not errors, just flagged)

**Key Insight**:

> "Exclusive spell-checker" = looks for what's WRONG, not what's RIGHT Faster
> than checking every possible valid combination!

---

## Rule Categories (13 pattern groups)

### **1. General Invalid Combos** (Lines 119-268)

- Too many letters (8+, 5+, etc.)
- Invalid 3-4 letter sequences
- Double vowel issues
- Malformed stacking

**Example patterns**:

- 8+ consecutive Tibetan letters = error
- Certain consonant+consonant+suffix combos

### **2. Bad Prefix Rules** (Lines 330-389)

Specific invalid prefix + base combinations:

- `[\u0F42]` (ga) prefix → invalid before certain letters
- `[\u0F51]` (da) prefix → invalid before certain letters
- `[\u0F56]` (ba) prefix → invalid before certain letters
- `[\u0F58]` (ma) prefix → invalid before certain letters
- `[\u0F60]` (ra) prefix → invalid before certain letters

**What this means**: Only 5 letters can be prefixes (ga, da, ba, ma, ra) And
each can only prefix specific base consonants

### **3. Bad Superscript "ra-mgo" (རྒ)** (Lines 392-450)

Invalid patterns with superscript ra:

- U+0F62 (ra) + certain subjoined consonants = invalid
- Complex rules about what can/can't stack with ra

### **4. Bad Superscript "la-mgo" (ལྒ)** (Lines 453-511)

Invalid patterns with superscript la:

- U+0F63 (la) + certain subjoined consonants = invalid

### **5. Bad Superscript "sa-mgo" (སྒ)** (Lines 514-571)

Invalid patterns with superscript sa:

- U+0F66 (sa) + certain subjoined consonants = invalid

### **6. Bad Subscript "ya-rtags" (གྱ)** (Lines 575-602)

Invalid patterns with subscript ya:

- U+0FB1 (ya-btags) can only combine with certain letters

### **7. Bad Subscript "ra-rtags" (བྲ)** (Lines 605-632)

Invalid patterns with subscript ra:

- U+0FB2 (ra-btags) can only combine with certain letters

### **8. Bad Subscript "la-rtags" (ཀླ)** (Lines 635-662)

Invalid patterns with subscript la:

- U+0FB3 (la-btags) can only combine with certain letters

### **9. Bad Subscript "wa-zur" (དྭ)** (Lines 665-692)

Invalid patterns with subscript wa:

- U+0FAD (wa-zur) can only combine with certain letters

### **10. Sanskrit Markers** (Lines 695-753)

**BLUE/TURQUOISE** (not errors, just flags):

- Sanskrit vowels (long vowels not in Tibetan)
- Aspirated consonants with ha subscript (གྷ, དྷ, བྷ, etc.)
- Special Sanskrit combinations (hr, shr, etc.)
- Invalid superscript-subscript pairs (valid in Sanskrit only)

### **11. Chinese Transliteration** (Lines 756-783)

**BLUE** flag for:

- Tsa-phru mark (U+0F39) used in Chinese transliterations

### **12. Encoding Errors** (Lines 786-814)

**RED** (critical):

- Wrong ra used: U+0F6A (full-height ra) instead of proper ra-mgo
- Wrong a-chung: U+0FB0 (subjoined 'a) instead of U+0F71 (vowel sign a)

### **13. False Positive Patch** (Lines 847-874)

Removes highlighting from patterns that were incorrectly flagged

---

## Key Takeaways

### **1. "Exclusive" is Smart**

Rather than defining all valid combinations (millions), define invalid ones
(thousands)

```
Valid combinations: ~∞ (need dictionary)
Invalid combinations: ~1000 (can enumerate)
```

### **2. Three Error Levels**

```python
class ErrorSeverity:
    CRITICAL = "critical"      # RED - encoding errors
    ERROR = "error"            # YELLOW - invalid Tibetan
    INFO = "info"              # BLUE - Sanskrit/foreign
```

### **3. Prefix Rules (5 letters)**

Only these can be prefixes: ག (ga), ད (da), བ (ba), མ (ma), ར (ra) And each has
specific bases it can prefix

### **4. Superscript Rules (3 letters)**

Only these can be superscripts: ར (ra), ལ (la), ས (sa) Called: ra-mgo, la-mgo,
sa-mgo

### **5. Subscript Rules (4 letters)**

Only these can be subscripts: ྱ (ya), ྲ (ra), ླ (la), ྭ (wa) Called: ya-rtags,
ra-rtags, la-rtags, wa-zur

### **6. Sanskrit is Separate**

Don't treat as errors, just flag for user awareness

---

## What We Can Reuse

### **Directly Portable:**

✅ All the regex patterns (convert VBA → Python) ✅ The categorization
(prefixes, superscripts, subscripts) ✅ Three-level severity system ✅ Exclude
Sanskrit approach

### **Architecture We'll Improve:**

- VBA runs all patterns sequentially (slow)
- We can: Compile patterns once, run efficiently
- We can: Return structured errors, not just highlight
- We can: Add position information for PDF annotation
- We can: Make testable with unit tests

### **What This Gives Us:**

✅ Complete set of invalid Tibetan patterns  
✅ No need to research rules from scratch  
✅ Proven approach (used since 2011)  
✅ GPL license (we can use/modify)  
✅ Academic credibility (Columbia University)

---

## Implementation Plan

### Convert to Python:

```python
import regex  # Better Unicode support than 're'

class TibetanSpellChecker:
    def __init__(self):
        # Compile all patterns once
        self.patterns = self._compile_patterns()

    def _compile_patterns(self):
        """Convert VBA patterns to Python regex"""
        return {
            'invalid_general': [
                # Pattern 1 from line 122
                regex.compile(r'[\u0F40-\u0F6C\u0F71-\u0F85\u0F90-\u0FBC]{8,}'),
                # ... more patterns
            ],
            'invalid_prefix': [
                # Pattern from line 334
                regex.compile(r'[\u0F42][\u0F40\u0F41\u0F46...]'),
                # ... more
            ],
            'invalid_ra_mgo': [...],
            'invalid_la_mgo': [...],
            'invalid_sa_mgo': [...],
            'invalid_ya_rtags': [...],
            'invalid_ra_rtags': [...],
            'invalid_la_rtags': [...],
            'invalid_wa_zur': [...],
            'sanskrit_markers': [...],  # Flag as info
            'encoding_errors': [...],   # Critical
        }

    def check_text(self, text):
        """Run all patterns, return structured errors"""
        errors = []

        for category, patterns in self.patterns.items():
            for pattern in patterns:
                matches = pattern.finditer(text)
                for match in matches:
                    errors.append({
                        'word': match.group(),
                        'position': match.start(),
                        'category': category,
                        'severity': self._get_severity(category)
                    })

        return errors

    def _get_severity(self, category):
        if category == 'encoding_errors':
            return 'critical'
        elif category == 'sanskrit_markers':
            return 'info'
        else:
            return 'error'
```

---

## Updated Task 3

**Task 3: Review Existing Script**

- ✅ Reviewed: Paul Hackett's VBA spell checker
- ✅ Documented: 13 rule categories
- ✅ Identified: All regex patterns to port
- ✅ License: GPL, can use/modify
- ✅ Approach: Exclusive (find invalid, not validate valid)

**Next**: Port patterns to Python in Task 5

---

## Prior Art

This project builds on Paul Hackett's spell checker (Columbia, 2011, GPL license).
Key insight adopted: the "exclusive" approach defines INVALID patterns rather than
enumerating all valid combinations. This is efficient because valid Tibetan
combinations are potentially infinite (requiring a dictionary), while invalid
combinations are ~1000 patterns that can be enumerated.

The original VBA regex patterns were ported to Python, organized into testable
categories, and augmented with structured error reporting and position tracking.

---

## Credit & Attribution

**Must Include:**

```
Based on Tibetan Spell-checker v1.0 (2011)
by Paul G. Hackett, Columbia University
Licensed under GNU GPL v3
Original: VBA/Microsoft Word
Modernized: Python/Web-based
```

Add to README, About page, and code comments
