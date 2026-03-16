# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project uses [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

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
