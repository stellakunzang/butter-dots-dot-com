# Tibetan Syllable Structure Reference

## Overview

A Tibetan syllable has up to 7 components in this order:

```
[PREFIX] + [SUPERSCRIPT] + ROOT + [SUBSCRIPT(S)] + [VOWEL] + [SUFFIX] + [POST-SUFFIX]
```

Only the **root** is required. Everything else is optional.


## Components

### 1. Prefix (sngon-'jug) -- optional

5 letters can be prefixes:

| Letter | Name | Unicode |
|--------|------|---------|
| ག | ga | U+0F42 |
| ད | da | U+0F51 |
| བ | ba | U+0F56 |
| མ | ma | U+0F58 |
| འ | achung | U+0F60 |

Position: before the root (or before the superscript, if present).

Each prefix can only precede certain roots. The valid prefix+root sets
are defined in `rules/stacking.py` using positive validation -- if the
combination is not in the valid set, it is invalid. For example, ག can
prefix ང (གང) but cannot prefix ཀ (གཀ is invalid).

**These same letters can also appear as roots or suffixes.** A letter's
role depends on its position in the syllable, not its identity.

### 2. Superscript (mgo-can) -- optional

3 letters can be superscripts:

| Letter | Name | Unicode |
|--------|------|---------|
| ར | ra-mgo | U+0F62 |
| ལ | la-mgo | U+0F63 |
| ས | sa-mgo | U+0F66 |

Position: above the root. In Unicode, the superscript is a base-form
character immediately followed by a subjoined root.

Each superscript can only sit above certain roots. See
`VALID_STACKS_REFERENCE.md` for the complete list, and `rules/stacking.py`
for the sets used in code.

**Being superscript-capable is necessary but not sufficient.** The parser
confirms a superscript+root pair only when the stacking rules say the
combination is valid. For example, ས followed by subjoined ཀ is a valid
sa-mgo stack (སྐ), but ས followed by subjoined ར is not -- in that case
ས is the root and ྲ is a subscript (སྲ).

### 3. Root (ming-gzhi) -- REQUIRED

Any of the 30 Tibetan consonants (U+0F40 to U+0F6C) can be a root.

This is the central consonant of the syllable. Everything else is
positioned relative to it. The root is always stored in base form in the
parsed output, making it directly usable as a dictionary lookup key.

### 4. Subscript (btags) -- optional

4 letters can be subscripts (written in subjoined form below the root):

| Letter | Name | Unicode (subjoined) |
|--------|------|---------------------|
| ྱ | ya-btags | U+0FB1 |
| ྲ | ra-btags | U+0FB2 |
| ླ | la-btags | U+0FB3 |
| ྭ | wa-zur | U+0FAD |

Position: below the root.

Each subscript can only attach to certain roots. A syllable may have
more than one subscript (e.g. གྲྭ has both ra-btags and wa-zur).

### 5. Vowel -- optional

4 explicit vowel marks:

| Mark | Sound | Unicode |
|------|-------|---------|
| ི | i (gi-gu) | U+0F72 |
| ུ | u (zhabs-kyu) | U+0F74 |
| ེ | e ('greng-bu) | U+0F7A |
| ོ | o (na-ro) | U+0F7C |

If no vowel mark is present, the inherent vowel is "a".

### 6. Suffix (rjes-'jug) -- optional

10 letters can be suffixes:

| Letter | Name | Unicode |
|--------|------|---------|
| ག | ga | U+0F42 |
| ང | nga | U+0F44 |
| ད | da | U+0F51 |
| ན | na | U+0F53 |
| བ | ba | U+0F56 |
| མ | ma | U+0F58 |
| འ | achung | U+0F60 |
| ར | ra | U+0F62 |
| ལ | la | U+0F63 |
| ས | sa | U+0F66 |

Position: after the root and vowel.

### 7. Post-suffix (yang-'jug) -- optional

Only 2 letters can be post-suffixes:

| Letter | Name | Unicode |
|--------|------|---------|
| ད | da | U+0F51 |
| ས | sa | U+0F66 |

Position: after the suffix. A post-suffix can only appear when a suffix
is already present.


## Finding the Root Letter

The root is the centre of the syllable. The parser identifies it using
a three-step decision process (see `parsing/parser.py`):

**Step 1 -- Superscript check.** Scan for a base character from {ར, ལ, ས}
immediately followed by a subjoined character. If the stacking rules say
that combination is valid, the base character is the superscript and the
subjoined character's base form is the root.

**Step 2 -- Vowel position.** If there is no superscript, look for the
first vowel mark. The vowel always sits on the root, so work backwards
from the vowel to find the base consonant it attaches to.

**Step 3 -- No vowel, no superscript.** Use structural heuristics:
if the first character is followed by a subjoined character, it is the
root (with subscripts). Otherwise, check whether the first character
is a valid prefix with enough structure after it to justify a prefix
reading. If not, the first character is the root.

Once the root is identified, everything before it is a prefix (or
superscript), everything subjoined below it is a subscript, and base
consonants after the vowel are the suffix and optional post-suffix.


## Worked Examples

### ལང (lang) -- root + suffix
```
ལ  U+0F63  ROOT (la)
ང  U+0F44  SUFFIX (nga)

Result: VALID  --  ང is one of the 10 valid suffixes
```

### བོད (bod) -- root + vowel + suffix
```
བ  U+0F56  ROOT (ba)
ོ  U+0F7C  VOWEL (o)
ད  U+0F51  SUFFIX (da)

Result: VALID
```

### སྐད (skad) -- superscript + root + suffix
```
ས  U+0F66  SUPERSCRIPT (sa-mgo)
ྐ  U+0F90  ROOT (ka, subjoined form -- base form ཀ)
ད  U+0F51  SUFFIX (da)

Parser logic: ས is superscript-capable, ྐ's base form ཀ is in
VALID_SA_MGO_ROOTS, so this is confirmed as sa-mgo + ka.
Result: VALID
```

### གཡང (g.yang) -- prefix + root + suffix
```
ག  U+0F42  PREFIX (ga)
ཡ  U+0F61  ROOT (ya)
ང  U+0F44  SUFFIX (nga)

Parser logic: ག is a valid prefix, and ཡ is in VALID_GA_PREFIX_ROOTS.
Result: VALID
```

### བསྒྲུབས (bsgrubs) -- all 7 components
```
བ  U+0F56  PREFIX (ba)
ས  U+0F66  SUPERSCRIPT (sa-mgo)
ྒ  U+0F92  ROOT (ga, subjoined form -- base form ག)
ྲ  U+0FB2  SUBSCRIPT (ra-btags)
ུ  U+0F74  VOWEL (u)
བ  U+0F56  SUFFIX (ba)
ས  U+0F66  POST-SUFFIX (sa)

Result: VALID  --  all 7 positions filled
```

### སྲ (sra) -- NOT a superscript
```
ས  U+0F66  ROOT (sa)
ྲ  U+0FB2  SUBSCRIPT (ra-btags)

Parser logic: ས is superscript-capable, but ྲ's base form ར is NOT
in VALID_SA_MGO_ROOTS. So ས is the root, not a superscript.
Result: VALID
```


## Common Mistakes

**Treating the first letter as a prefix.** Only 5 letters can be
prefixes, and only when a root follows. In ལང, the ལ is the root
and ང is the suffix -- ལ is not a prefix.

**Confusing superscript-capable with superscript.** A letter from
{ར, ལ, ས} is only a superscript when the stacking rules confirm
the combination. Otherwise it is the root.


## Code Architecture

The syllable structure knowledge is spread across these modules:

| Module | Responsibility |
|--------|----------------|
| `rules/stacking.py` | Data: valid component sets, combination lookups |
| `char_typing/char_typer.py` | Stage 1: classify each character by Unicode type |
| `parsing/parser.py` | Stage 2: assemble characters into a TibetanSyllable |
| `validation/` | Stage 3: check patterns, completeness, and component rules |
| `data_types/` | Canonical data structures (TibetanSyllable, TypedChar, SpellError) |

All validation uses **positive checking**: a combination must appear in
the valid set to be accepted. This is consistent across prefixes,
superscripts, and subscripts, and avoids the errors that come from
maintaining a negative (invalid-only) list.
