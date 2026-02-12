# Tibetan Words Pressure Test

**Purpose**: Validate our understanding of syllable structure rules with real Tibetan words before implementation

## Test Strategy

For each word, we need to:
1. Break down the syllable structure (prefix, superscript, root, subscript, vowel, suffix, post-suffix)
2. Verify against invalid pattern rules
3. Confirm expected result (valid/invalid)

## Common Tibetan Words

### Basic Words (Expected: ALL VALID)

| Word | Structure | Breakdown | Valid? |
|------|-----------|-----------|---------|
| བོད | root+vowel+suffix | བ(root) + ོ(vowel) + ད(suffix) | ✓ |
| ལང | root+suffix | ལ(root) + ང(suffix) | ✓ |
| དབང | prefix+root+suffix | ད(prefix) + བ(root) + ང(suffix) | ✓ |
| རྒྱལ | prefix+superscript+root+subscript+suffix | ར(prefix) + superscript ག + ཡ(subscript) + ལ(suffix) | ? |
| སངས | superscript+root+suffix+post-suffix | ས(superscript) + ང(root) + ས(suffix) + ས(post-suffix)? | ? |
| རྒྱ | prefix+superscript+root+subscript | ར(prefix) + superscript ག + ཡ(subscript) | ? |
| དཀར | prefix+root+suffix | ད(prefix) + ཀ(root) + ར(suffix) | ✓ |
| དམར | prefix+root+suffix | ད(prefix) + མ(root) + ར(suffix) | ✓ |
| སེར | superscript+root+vowel+suffix | ས(superscript) + ེ(root) + ེ(vowel) + ར(suffix) | ? |
| ལྗོངས | superscript+root+vowel+suffix+post-suffix | ལ(superscript) + ྗ + ོ + ང + ས | ? |

### Words with Prefixes (Test prefix rules)

| Word | Structure | Prefix Rules Check | Valid? |
|------|-----------|-------------------|---------|
| གང | prefix+root | ག(prefix) + ང(root) - ང NOT in ga invalid list | ✓ |
| གཡང | prefix+root+suffix | ག(prefix) + ཡ(root) + ང(suffix) | ✓ |
| གཡོག | prefix+root+vowel+suffix | ག(prefix) + ཡ(root) + ོ(vowel) + ག(suffix) | ✓ |
| གཉིས | prefix+root+vowel+suffix+post-suffix | ག(prefix) + ཉ(root) + ི(vowel) + ས(suffix) | ✓ |
| དགོན | prefix+root+vowel+suffix | ད(prefix) + ག(root) + ོ(vowel) + ན(suffix) | ✓ |
| དཀར | prefix+root+suffix | ད(prefix) + ཀ(root) + ར(suffix) | ✓ |
| བགྲོད | prefix+superscript+root+subscript+vowel+suffix | བ(prefix) + ག(superscript?) + ྲ + ོ + ད | ? |
| མགོ | prefix+root+vowel | མ(prefix) + ག(root) + ོ(vowel) | ✓ |
| མཁན | prefix+root+suffix | མ(prefix) + ཁ(root) + ན(suffix) | ✓ |
| རྒྱལ | prefix+superscript+root+subscript+suffix | Need to analyze | ? |

### Invalid Prefix Combinations (Expected: INVALID)

| Word | Structure | Why Invalid | Valid? |
|------|-----------|-------------|---------|
| གཀ | prefix+root | ག cannot prefix ཀ | ✗ |
| གཔ | prefix+root | ག cannot prefix པ | ✗ |
| དཡ | prefix+root | ད cannot prefix ཡ | ✗ |
| བཡ | prefix+root | བ cannot prefix ཡ | ✗ |
| མཀ | prefix+root | མ cannot prefix ཀ | ✗ |
| རཀ | prefix+root | ར cannot prefix ཀ | ✗ |

### Words with Superscripts

| Word | Unicode Breakdown | Structure | Valid? |
|------|-------------------|-----------|---------|
| རྒ | ? | Need to check if this is ra prefix or ra superscript | ? |
| སྒ | ? | sa superscript + ga root | ? |
| ལྒ | ? | la superscript + ga root | ? |
| སྐ | ? | sa superscript + ka root | ? |
| སྣ | ? | sa superscript + na root | ? |
| སྦ | ? | sa superscript + ba root | ? |

### Words with Subscripts

| Word | Unicode Breakdown | Structure | Valid? |
|------|-------------------|-----------|---------|
| གྱ | ག + \u0FB1 | ga root + ya subscript | ✓ |
| ཀྱ | ཀ + \u0FB1 | ka root + ya subscript | ✓ |
| ཁྱ | ཁ + \u0FB1 | kha root + ya subscript | ✓ |
| གྲ | ག + \u0FB2 | ga root + ra subscript | ✓ |
| ཀྲ | ཀ + \u0FB2 | ka root + ra subscript | ✓ |
| ཁྲ | ཁ + \u0FB2 | kha root + ra subscript | ✓ |
| གླ | ག + \u0FB3 | ga root + la subscript | ✓ |
| ཀླ | ཀ + \u0FB3 | ka root + la subscript | ✓ |
| གྭ | ག + \u0FAD | ga root + wa subscript | ✓ |
| ཀྭ | ཀ + \u0FAD | ka root + wa subscript | ✓ |

### Complex Syllables (Need careful analysis)

| Word | Components | Notes |
|------|-----------|-------|
| བསྒྲུབས | བ + ས + ག + ྲ + ུ + བ + ས | All 7 components? |
| སྒྲུབ | ས + ག + ྲ + ུ + བ | superscript + root + subscript + vowel + suffix |
| སྤྱོད | ས + པ + ྱ + ོ + ད | superscript + root + subscript + vowel + suffix |
| བརྒྱད | བ + ར + ག + ྱ + ད | prefix + superscript + root + subscript + suffix |

### Buddhist/Religious Terms

| Word | Meaning | Expected | Notes |
|------|---------|----------|-------|
| སངས་རྒྱས | Buddha | Valid | Two syllables: སངས + རྒྱས |
| དཀོན་མཆོག | Precious One | Valid | Two syllables |
| ལྷ | deity | Valid? | Simple: la + ha? Or subscript? |
| བླ་མ | lama | Valid | Two syllables |
| དབང་པོ | lord | Valid | Two syllables |

## Questions to Resolve

1. **Superscript vs Prefix**: How do we distinguish?
   - རྒ - Is this ར prefix + ག root? Or ར superscript + ག root?
   - Need to check: Are prefixes written at same height or above?

2. **Subscript forms**: 
   - Are subscripts always Unicode combining characters (U+0FB1-0FB3, U+0FAD)?
   - Or can they be subjoined consonants (U+0F90-0FBC)?

3. **Complex stacking**:
   - བསྒྲུབས - Is བ a prefix? Is ས a superscript? Or is བས together?
   - Need to understand the parsing order

4. **Post-suffix rules**:
   - Which suffixes can take post-suffixes?
   - Only ད and ས can be post-suffixes, but what can come before them?

## Testing Plan

### Phase 1: Verify Simple Cases
- Single root letters (ཀ, ལ, བ)
- Root + suffix (ལང, བོད)
- Root + vowel + suffix (བོད, ཡིག)

### Phase 2: Verify Prefix Rules
- All 5 prefixes with valid roots
- Test invalid combinations (གཀ, དཡ, etc.)

### Phase 3: Verify Superscripts/Subscripts
- Superscript combinations
- Subscript combinations
- Invalid stacking patterns

### Phase 4: Complex Real Words
- Multi-component syllables
- Buddhist terms
- Common vocabulary

### Phase 5: Edge Cases
- Sanskrit loanwords (Phase 3+)
- Unusual but valid combinations
- Near-misses (one letter off from valid)

## Next Steps

1. [ ] Get Unicode breakdown for all test words
2. [ ] Parse each syllable structure manually
3. [ ] Verify against invalid pattern rules
4. [ ] Document any ambiguous cases
5. [ ] Create automated test suite with these words
6. [ ] Research any words that don't match our understanding

## Resources Needed

- Tibetan dictionary with structural breakdowns
- Tool to show Unicode codepoints for each character
- Tibetan grammar validation rules reference
- Native speaker verification (if possible)
