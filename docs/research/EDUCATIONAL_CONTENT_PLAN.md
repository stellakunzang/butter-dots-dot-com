# Educational Content Plan

**Purpose**: Demystify Tibetan text processing complexity  
**Audience**: Developers, linguists, language learners  
**Location**: `/learn` section of website

---

## Page 1: Understanding Tibetan Script

**URL**: `/learn/tibetan-script`

### Section 1: Why Tibetan is Different

**Interactive Visualization:**
```
Compare English vs Tibetan

English: "hello"
[h] [e] [l] [l] [o]
↓
5 letters, processed individually ✓

Tibetan: "བོད"
[བ ོ ད]
↓  ↓  ↓
base vowel suffix
    mark

Must process as complete syllable ✓
```

**Key Points:**
- English is alphabetic (individual letters)
- Tibetan is syllabic (groups of letters)
- You can't check "b" "o" "d" separately
- Must check "bod" as a complete unit

### Section 2: Syllable Anatomy

**Interactive Tool:**
```tsx
// User types or selects Tibetan text
// We break it down with color coding

Input: བརྒྱད (brgyad - "eight")

Breakdown:
[བ] Prefix (blue)
[ར] Superscript (green)  
[ག] Base consonant (purple)
[ྱ] Subscript (orange)
[ད] Suffix (red)

Rules Applied:
✓ 'བ' can prefix 'ག'
✓ 'ར' can superscript 'ག'
✓ 'ྱ' can subscript 'ག'
✓ 'ད' is valid suffix
Result: Valid syllable!
```

### Section 3: Common Structures

**Examples with explanations:**
```
Simple: ཀ (ka)
- Base consonant only

With vowel: ཀི (ki)
- Base + vowel mark

With suffix: ཀབ (kab)
- Base + vowel + suffix

Complex: བསྒྲུབས (bsgrubs)
- Prefix + superscript + base + subscript + suffix
```

---

## Page 2: The Unicode Challenge

**URL**: `/learn/unicode-explained`

### Section 1: What You See vs What's Real

**Interactive Demo:**
```
What you see: བོད
What's actually there:

Character 1: བ
  Unicode: U+0F56
  Name: TIBETAN LETTER BA

Character 2: ོ  
  Unicode: U+0F7C
  Name: TIBETAN VOWEL SIGN O

Character 3: ད
  Unicode: U+0F51
  Name: TIBETAN LETTER DA

Total: 3 Unicode code points
Visual: 1 syllable
```

**Code Example:**
```python
# This surprises English developers:
text = "བོད"
print(len(text))  # 3 (not 1!)

# Each Unicode point is separate
for char in text:
    print(hex(ord(char)))
# 0xf56, 0xf7c, 0xf51
```

### Section 2: The Normalization Problem

**Visual explanation:**
```
Same Word, Different Bytes:

Version 1 (Composed):
བོད = [U+0F56, U+0F7C, U+0F51]

Version 2 (Decomposed):  
བོད = [U+0F56, U+0F7C, U+0F51] (same in this case)

Problem: Some chars can decompose differently!
Solution: Always normalize to NFC form
```

**Why This Matters:**
```
Without normalization:
- Database searches fail
- Comparisons return false
- Sorting breaks
- Spell checking misses errors

With normalization:
✓ Consistent representation
✓ Reliable comparisons
✓ Correct sorting
```

### Section 3: For Developers

**Best Practices:**
```python
# ✓ Always do this first:
import unicodedata
text = unicodedata.normalize('NFC', user_input)

# ✓ Use UTF-8 everywhere:
database: encoding='UTF8'
files: encoding='utf-8'
API: charset=utf-8

# ✓ Use 'regex' not 're':
import regex
pattern = r'\p{Tibetan}+'  # Works!

# ✗ Don't do this:
import re
pattern = r'[a-zA-Z]+'  # Only English!
```

---

## Page 3: Syllables vs Words

**URL**: `/learn/syllables-vs-words`

### Section 1: The Fundamental Difference

**Comparison:**
```
ENGLISH (Word-based):
"The quick brown fox"
 ↓
Words clearly separated by spaces
Each word can be checked independently

TIBETAN (Syllable-based):
"བོད་ཡིག་ནི་སྐད་ཡིག"
 ↓
Syllables separated by tsheg (་)
Words not clearly marked!

Where do words start/end?
བོད་ཡིག (one word: "Tibetan language")
ནི (one word: copula)
སྐད་ཡིག (one word: "language")
```

### Section 2: Why Our MVP Checks Syllables

**Phase 1: Syllable Checking**
```
What we check:
✓ Is each syllable grammatically valid?
✓ Are letter combinations allowed?
✓ Do prefix/suffix rules hold?

Example:
Input: བོད་ཡིབ
Check: བོད (valid) ✓
       ཡིབ (valid) ✓
Result: No errors found

But wait! ཡིབ isn't a real word!
Phase 1 can't catch this.
```

**Phase 2: Word Checking** (Coming Later)
```
What we'll add:
✓ Dictionary lookup
✓ Word boundary detection  
✓ Contextual checking

Same example:
Input: བོད་ཡིབ
Syllables: Valid ✓
Dictionary: ཡིབ not found ✗
Suggestion: Did you mean བོད་ཡིག?
```

### Section 3: The Trade-off

**Why start with syllables?**
```
Pros:
✓ Faster to build
✓ No huge dictionary needed
✓ Catches ~40% of errors
✓ Educational (teaches structure)
✓ Good foundation for Phase 2

Cons:
✗ Misses nonsense words
✗ Can't suggest corrections
✗ No context awareness
```

**Interactive Comparison:**
```
Try it yourself!

[Text input box]
User types: བོད་ཡིབ

Phase 1 Result:
✓ Valid Tibetan syllables
0 errors found

Phase 2 Result: (Coming soon)
✗ Word not found: ཡིབ
Suggestion: བོད་ཡིག (96% match)
1 error found
```

---

## Page 4: Wylie vs Pronunciation

**URL**: `/learn/wylie-problem`

### Section 1: What is Wylie?

**Definition:**
```
Wylie Transliteration:
- System for typing Tibetan with ASCII keyboard
- Maps Tibetan script → English letters
- Created by Turrell Wylie (1959)
- Standard in scholarship

Example:
Tibetan: བོད་
Wylie:   bod
Meaning: Tibet
```

**Useful for:**
- ✓ Typing Tibetan without special keyboard
- ✓ Academic papers (ASCII-only)
- ✓ Understanding script structure
- ✓ Computer input systems

### Section 2: The Problem

**Wylie Represents Writing, Not Sound:**

**Example 1:**
```
Written:     བསྟན་པ
Wylie:       bstan-pa
Pronounced:  "ten-pa"

All those letters existed in Old Tibetan!
Modern pronunciation dropped them.
```

**Example 2:**
```
Written:     དབྱངས
Wylie:       dbyangs  
Pronounced:  "yang"

Try saying "d-b-y-a-ng-s" fast → becomes "yang"
```

**Example 3:**
```
Written:     སྒྲ
Wylie:       sgra
Pronounced:  "dra"

Historical: s-g-ra
Modern: The 's' and 'g' merged into 'd' sound
```

### Section 3: The Disconnect

**Two Mastery Paths:**

```
Path 1: Scholar
├─ Learns Wylie transliteration
├─ Can read Tibetan texts
├─ Understands grammar
└─ Often can't speak/understand spoken Tibetan

Path 2: Native Speaker
├─ Speaks fluently
├─ Understands spoken language
├─ May struggle with written form
└─ Might not know Wylie at all

The Gap:
Written ←─────────→ Spoken
       Wylie only helps with one side!
```

**Real-world impact:**
```
Scenario: Scholarly Conference

Scholar reads paper using Wylie:
"The bstan-pa of bla-ma..."

Tibetan speaker hears:
"The ten-pa of la-ma..."

Communication breakdown! 
Same words, pronounced differently.
```

### Section 4: Our Solution

**Multi-System Support:**

```tsx
// In our spell checker
<Word tibetan="བོད་">
  
  <Display mode="wylie">
    bod
    <Info>Represents written form</Info>
  </Display>

  <Display mode="phonetic">
    pö
    <Info>Represents pronunciation</Info>
  </Display>

  <Display mode="thl">
    bö  
    <Info>Simplified Wylie</Info>
  </Display>

  <Toggle>Switch views</Toggle>
</Word>
```

**User Control:**
- Beginners: Default to phonetic
- Scholars: Default to Wylie
- Everyone: Can toggle anytime
- Tooltips: Explain the difference

### Section 5: Educational Stance

**Our Position:**

> **Both Are Valuable**
> 
> Wylie helps you understand written Tibetan structure.  
> Phonetic helps you speak and listen.  
> Neither is "wrong" - they serve different purposes.
>
> We provide both and educate about the difference.

**Resources:**
- Learn Wylie: [Link to Wylie guide]
- Learn Pronunciation: [Link to phonetic guide]
- Understand the History: [Link to linguistic explanation]

---

## Page 5: How Spell Checking Works

**URL**: `/learn/how-it-works`

### Section 1: The Process

**Step-by-Step:**
```
1. Upload PDF
   └─ File stored securely

2. OCR (Text Extraction)
   └─ Convert images → Tibetan text
   └─ Challenge: Historically poor for Tibetan
   └─ Solution: Modern deep learning OCR

3. Normalization
   └─ Unicode normalization (NFC)
   └─ Ensure consistent representation

4. Syllable Splitting
   └─ Split on tsheg (་)
   └─ Parse syllable structure

5. Rule Checking (Phase 1)
   └─ Validate prefix rules
   └─ Check stacking rules
   └─ Verify suffix combinations
   └─ Flag violations

6. Dictionary Check (Phase 2 - Coming)
   └─ Look up each word
   └─ Generate suggestions
   └─ Rank by frequency

7. Annotate PDF
   └─ Mark errors in red
   └─ Add suggestions as comments
   └─ Return annotated file
```

### Section 2: What Gets Checked

**Phase 1 (Current):**
```
Structural Rules:
✓ Valid prefix + base combinations
  Example: བ + ག = བག (valid)
           ང + ག = X (invalid prefix)

✓ Valid stacking
  Example: ར above ག = རྒ (valid)
           ད above ག = X (invalid)

✓ Suffix rules  
  Example: ད after ག = གད (valid)
           ཀ after ག = X (invalid)

✓ Post-suffix rules
✓ Invalid sequences
```

**Phase 2 (Future):**
```
Dictionary & Context:
✓ Real word check
✓ Common phrases
✓ Contextual appropriateness
✓ Frequency-based ranking
```

### Section 3: Limitations & Honesty

**What We Can't Catch (Yet):**
```
✗ Meaning errors
  Example: "I ate a tree" 
  (grammatical, but nonsensical)

✗ Homophones
  Example: to/too/two
  (In Tibetan: སེ་ན vs སེ་ན་)

✗ Style issues
  Example: formal vs colloquial

✗ Regional variations
  Example: U-Tsang vs Amdo spelling
```

**We're honest about this:**
- Phase 1 catches ~40-50% of errors
- Phase 2 will catch ~80-90%
- Human review still important
- Tool assists, doesn't replace judgment

---

## Implementation Plan

### Technical Requirements

**Frontend Components:**
```tsx
// React components needed
<InteractiveBreakdown />      // Shows syllable parts
<UnicodeVisualizer />         // Shows code points
<TransliterationToggle />     // Wylie/Phonetic switch
<PhaseComparison />          // Phase 1 vs 2 demo
<CodeExample />              // Developer guides
```

**Pages Structure:**
```
/learn
  /tibetan-script      → Understanding structure
  /unicode-explained   → Technical deep dive  
  /syllables-vs-words  → Why our approach
  /wylie-problem       → Linguistic context
  /how-it-works        → System explanation
```

**Integration Points:**
```
1. Spell checker UI
   - Link to relevant learn pages
   - Inline tooltips with explanations
   - "Why am I seeing this?" → educational content

2. Resources page
   - Add "Learn" section
   - Link to all educational content

3. Homepage
   - Featured: "Understanding Tibetan Text"
   - Teaser for educational content
```

### Content Principles

1. **Visual First**: Interactive demos > walls of text
2. **Progressive Disclosure**: Start simple, add complexity
3. **Honest About Limitations**: What works, what doesn't
4. **Respectful**: Acknowledge linguistic complexity
5. **Actionable**: Developers can use code examples

### Success Metrics

**Educational Goals:**
- Users understand why syllable checking ≠ word checking
- Developers can handle Tibetan in their own projects
- Scholars and learners both feel served
- Reduces confusion about Wylie

**Interview Value:**
- Shows domain expertise
- Demonstrates user empathy
- Not just building features, educating users
- Attention to cultural/linguistic implications

---

## Next Steps

1. ✓ Document decisions (done)
2. Create page wireframes
3. Build interactive components
4. Write educational copy
5. Integrate with spell checker
6. User testing with both scholars and native speakers

**Questions:**
- Should this be separate from spell checker or integrated?
- How much technical detail for non-developers?
- Include videos/animations?
- Multilingual (English + Tibetan explanations)?
