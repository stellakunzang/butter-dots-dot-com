# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project uses
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

---

## [0.2.0] - 2026-03-12

### Added

- Particle spelling rules — context-aware validation of relational, agentive,
  locative, and indefinite article particles against the suffix of the preceding
  word, with suggestions for the correct form
- Excepted words — ནའང་ and ལའང་ are now recognized as grammatically valid by
  convention and no longer flagged
- Tibetan numeral syllables (U+0F20–U+0F33) are now silently skipped; numbers no
  longer produce false positives or break particle context
- Tibetan punctuation and mark characters (yig mgo openers ༄ ༅, decorative shad
  variants ༑ ༒, gter tsheg ༔, etc.) are now silently skipped
- Spelling Rules page — learner-facing reference documenting syllable anatomy,
  particle rules by category, and an explanation of each error type
- Changelog page — release notes published on the frontend at /changelog

### Fixed

- ཧཧིབ་ was not being flagged as invalid; ཧ (ha) cannot act as a prefix and is
  now correctly detected as an unparsed character
- "Relational" used throughout in place of "genitive" for the bdag gi sgra
  particle category, matching standard English terminology for this community

### Changed

- Subscript validation re-enabled after confirming the rule data is correct and
  no false positives occur on attested Tibetan words

---

## [0.1.0] - 2026-02-09

### Added

- Tibetan syllable spellchecker — validates the structural correctness of
  Tibetan syllables against classical spelling rules
- Validates all five prefix consonants (ག་ ད་ བ་ མ་ ར་) against valid root
  consonant combinations
- Validates superscripts (ར་ ལ་ ས་), subscripts (ྱ ྲ ླ ྭ), suffixes, and
  post-suffixes
- Detects impossible syllable structures: subscripts appearing after vowels or
  suffixes, multiple vowel groups, unusual mark positions
- Detects syllables that exceed the maximum valid length
- Web interface for checking Tibetan text inline
- Wylie transliteration shown alongside each flagged syllable for reference
