# Edge cases branch — planned work

## Sequence

1. Bug fix: ཧཧིབ་ not triggering error
2. Excepted words (ནའང་, ལའང་)
3. Particle spelling rules
4. Numbers
5. Naro at end of sentence
6. Superscript/subscript invalid patterns (ra-mgo, la-mgo, sa-mgo)
7. Double vowel detection
8. Encoding error detection (wrong 'a', wrong ra, etc.)
9. Error message architecture review — assess current structure, identify
   improvements that will scale as we add more rule types
10. Spelling rules documentation — publish a learning resource on the website
    explaining Tibetan spelling rules (particles, suffixes, structure) for users

---

## Details

### Structural / grammatical checks

- numbers
- the syllable at the end of the sentence with naro
- the spelling rules related to particles
  - Genitive:
    - ཀྱི་ used with words ending in suffix ད་བ་ས་
    - གི་ used with words ending in suffix ག་ང་
    - གྱི་ used with words ending in suffix ན་མ་ར་ལ་
    - འི་ used with words ending in suffix འ་ or no suffix
    - ཡི་ is sometimes used in place of འི་
  - Agentive
    - ཀྱིས་ used with words ending in suffix ད་བ་ས་
    - གིས་ used with words ending in suffix ག་ང་
    - གྱིས་ used with words ending in suffix ན་མ་ར་ལ་
    - ས་ replaces suffix འ་ or added when no suffix
    - ཡིས་ is sometimes used in place of ས་
  - Locative
    - ན་ can be used after any suffix or with no suffix
    - ལ་ can be used after any suffix or with no suffix
    - སུ་ is used after words ending in ས་
    - ཏུ་ is used after suffixes ག་བ་ as well as second suffix ད་
    - ར་ can be used after words ending is suffix འ་
    - རུ་ can be used after words ending in the suffix འ་ or after words with no
      suffix
    - དུ་ is used after words ending in suffixes ང་ད་ན་མ་ར་ལ་
  - Indefinite Article
    - ཅིག་ used with words ending in ག་ད་བ་
    - ཤིག་ used with words ending in ས་
    - ཞིག་ used with all other cases
- Words that are excepted
  - ནའང་
  - ལའང་
- Superscript/subscript invalid patterns (ra-mgo, la-mgo, sa-mgo — partial,
  needs completing)
- Double vowel detection
- Encoding error detection:
  - wrong 'a' vowel (U+0FB0 instead of U+0F71)
  - wrong ra (U+0F6A instead of U+0F62)
  - other encoding substitution errors

### Error message architecture

Review the current error message structure and identify improvements that will
scale as we add more rule types (particles, encoding errors, structural checks,
eventually dictionary-level errors). Questions to explore:
- Are error types and severity levels consistent across rule categories?
- Is the structure extensible without breaking the frontend contract?
- Are messages useful to a learner, not just a developer?

### Spelling rules documentation (website)

Publish a learning resource on the site explaining Tibetan spelling rules for
users — particularly the rules we're enforcing in the spellchecker. Intended
audience is someone learning to read/write Tibetan, not a developer. Topics
likely include:
- Syllable structure (prefix, root, suffix, post-suffix)
- Particle rules and how they depend on the preceding syllable's suffix
- Common structural errors and what they mean

---

Bugs:

- ཧཧིབ་ doesn't trigger an error. Ha cannot be a prefix.

Future feature:

- submit bug report

Distant future features:

- Add word to dictionary
- star a definition so that one is preferred in the future when looking up this
  word (basically give users a nudge that this is a word they've looked up
  before and they should memorize it)
- when looking up a long passage, the words found in the dictionary are
  exportable into a glossary that can be edited.
- The cur
