# Tibetan Syllable Structure Reference

## Critical Understanding

**The root letter (base consonant) is NOT the same as a prefix!**

## Complete Syllable Structure

A Tibetan syllable can have up to 7 components in this order:

```
[PREFIX] + [SUPERSCRIPT] + ROOT + [SUBSCRIPT] + [VOWEL] + [SUFFIX] + [POST-SUFFIX]
```

Only the **ROOT** is required. Everything else is optional.

## 1. PREFIX (optional)

**Only 5 letters can be prefixes:**
- ག (ga) - U+0F42
- ད (da) - U+0F51
- བ (ba) - U+0F56
- མ (ma) - U+0F58
- ར (ra) - U+0F60

**Position:** BEFORE the root letter  
**Purpose:** Affects pronunciation (tone, aspiration, voicing)

**Examples:**
- བསྒྲུབས = ba + sa-mgo + ga + ra-btags + vowel + suffix
- གཡང་ = ga + ya + vowel + suffix

## 2. SUPERSCRIPT (optional)

**Only 3 letters can be superscripts:**
- ར (ra-mgo) - U+0F62
- ལ (la-mgo) - U+0F63
- ས (sa-mgo) - U+0F66

**Position:** ABOVE the root letter  
**Purpose:** Modifies the root consonant

**Examples:**
- རྒ = ra superscript + ga root
- ལྒ = la superscript + ga root
- སྒ = sa superscript + ga root

## 3. ROOT LETTER (REQUIRED)

**Any of the 30 Tibetan consonants can be a root letter**

**This is the MAIN consonant - the center of the syllable!**

Range: U+0F40 to U+0F68

**Examples:**
- ཀ (ka) - root only
- ལ (la) - root only
- བོད - ba + vowel o + da suffix (where ba is the root)

## 4. SUBSCRIPT (optional)

**Only 4 letters can be subscripts:**
- ྱ (ya-btags) - U+0FB1
- ྲ (ra-btags) - U+0FB2
- ླ (la-btags) - U+0FB3
- ྭ (wa-zur) - U+0FAD

**Position:** BELOW the root letter  
**Purpose:** Modifies the root consonant

**Examples:**
- གྱ = ga root + ya subscript
- བྲ = ba root + ra subscript
- ཀླ = ka root + la subscript

## 5. VOWEL (optional, default is 'a')

**4 vowel marks:**
- ི (i) - U+0F72
- ུ (u) - U+0F74
- ེ (e) - U+0F7A
- ོ (o) - U+0F7C

**Default:** If no vowel mark, the vowel is 'a'

## 6. SUFFIX (optional)

**10 letters can be suffixes:**
- ག (ga) - U+0F42
- ང (nga) - U+0F44 ← THIS IS VALID!
- ད (da) - U+0F51
- ན (na) - U+0F53
- བ (ba) - U+0F56
- མ (ma) - U+0F58
- འ (ah) - U+0F60
- ར (ra) - U+0F62
- ལ (la) - U+0F63
- ས (sa) - U+0F66

**Position:** AFTER the root letter (and vowel if present)  
**Purpose:** Marks grammatical function, affects pronunciation  
**Tibetan term:** "jen juke" (from "jey" = after, "juke" = enter)

**Six straightforward suffixes** (don't change vowel pronunciation):
- GA, NGA, BA, MA, AH, RA

**Four special suffixes** (cause vowel pronunciation changes):
- DA, NA, LA, SA

## 7. POST-SUFFIX (optional)

**Only 2 letters can be post-suffixes:**
- ད (da) - U+0F51
- ས (sa) - U+0F66

**Position:** AFTER the suffix  
**Requirement:** Can ONLY appear if there's already a suffix

## Example Analysis

### ལང་ (lang)
```
ལ = ROOT LETTER (la)
ང = SUFFIX (nga) ← VALID suffix!
་ = tsheg (syllable separator)

Structure: ROOT + SUFFIX
This is VALID Tibetan!
```

### བོད (bod)
```
བ = ROOT LETTER (ba)
ོ = VOWEL (o)
ད = SUFFIX (da)

Structure: ROOT + VOWEL + SUFFIX
This is VALID Tibetan!
```

### གཡང (g.yang - with ga prefix)
```
ག = PREFIX (ga)
ཡ = ROOT LETTER (ya)
ང = SUFFIX (nga)

Structure: PREFIX + ROOT + SUFFIX
This is VALID Tibetan!
```

### བསྒྲུབས (bsgrubs)
```
བ = PREFIX (ba)
ས = SUPERSCRIPT (sa-mgo) above the next letter
ག = ROOT LETTER (ga)
ྲ = SUBSCRIPT (ra-btags) below ga
ུ = VOWEL (u)
བ = SUFFIX (ba)
ས = POST-SUFFIX (sa)

Structure: PREFIX + SUPERSCRIPT + ROOT + SUBSCRIPT + VOWEL + SUFFIX + POST-SUFFIX
This is VALID Tibetan (all 7 components!)
```

## Common Mistakes

### ❌ WRONG: Treating all initial consonants as prefixes
```
ལང་
❌ "la is a prefix before nga"
✓ "la is the ROOT, nga is a SUFFIX"
```

### ❌ WRONG: Thinking only 5 letters can be roots
```
Only 5 letters can be PREFIXES (ga, da, ba, ma, ra)
But ANY consonant can be a ROOT!
```

### ✓ CORRECT: Understanding the position
```
PREFIX comes BEFORE the root
SUFFIX comes AFTER the root
```

## Finding the Root Letter

To find the root letter in a syllable:

1. **If there's a subscript** (ya-btags, ra-btags, la-btags, wa-zur):
   - The letter ABOVE the subscript is the root

2. **If there's a superscript** (ra-mgo, la-mgo, sa-mgo):
   - The letter BELOW the superscript is the root

3. **If there's a prefix** (ga, da, ba, ma, ra as first letter):
   - The SECOND consonant is the root

4. **Otherwise**:
   - The first consonant is the root

## Paul Hackett's Approach

Paul Hackett's spellchecker uses **"exclusive" checking**:
- It looks for INVALID patterns
- It does NOT validate that things are correct
- If a syllable doesn't match any invalid pattern, it's considered valid

**What this means:**
- Hackett checks for invalid prefix combinations
- Hackett checks for invalid superscript/subscript combinations
- Hackett does NOT explicitly validate suffixes
- Suffixes are implicitly valid if they don't trigger other invalid patterns

## Sources

1. FPMT Mandala: "Suffixes and Finding the Root Letter of a Syllable"
2. Rigpa Wiki: "Tibetan Grammar - Formation of the Tibetan Syllable"
3. Paul Hackett's Tibetan Spellchecker VBA (2011)
4. Tibetan Language Learning Resources

## For Implementation

When parsing a Tibetan syllable:

1. **Don't assume the first letter is a prefix!**
2. **Identify the root letter first** (using the rules above)
3. **Then identify what comes before (prefix/superscript) and after (suffix/post-suffix)**
4. **Validate each component according to its role**

```python
# Example parsing logic
def parse_syllable(syllable):
    # 1. Check for subscripts to identify root
    # 2. Check for superscripts to identify root
    # 3. Check if first letter is one of 5 prefixes
    # 4. Identify root based on above
    # 5. Everything after root (excluding vowels) is suffix/post-suffix
    pass
```
