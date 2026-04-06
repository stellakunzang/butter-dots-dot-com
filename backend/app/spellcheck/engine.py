"""
Tibetan Spell Check Engine

Main spell checking engine that orchestrates the pipeline:
1. Normalize (Unicode normalization)
2. Split text into syllables
3. For each syllable:
   a. Check patterns (encoding errors, unusual marks)
   b. Classify characters and parse structure
   c. Check structural completeness (raw string vs parsed)
   d. Validate components against stacking rules
"""
from typing import List, Dict, Optional
from .normalizer import normalize_tibetan, normalize_tibetan_with_position_map, is_tibetan_char, validate_tibetan_text, is_numeral_syllable, is_punctuation_syllable
from .splitter import split_syllables_with_position
from .char_typing import type_characters
from .parsing import parse_syllable
from .validation import (
    validate_syllable,
    check_syllable_patterns,
    check_syllable_structure_completeness,
    check_particle_context,
)
from .rules.exceptions import is_excepted
from .dictionary import DictionaryService


class TibetanSpellChecker:
    """
    Main Tibetan spell checking engine.

    Integrates Unicode normalization, syllable parsing, and validation
    to check Tibetan text for spelling errors.

    Phase 1: structural/grammatical validation (always active)
    Phase 2: dictionary lookup against the word corpus (active when a database
             is configured and the spelling_reference table has been populated)
    """

    def __init__(self, dictionary: DictionaryService | None = None):
        """
        Initialize the spell checker.

        Args:
            dictionary: A pre-built DictionaryService instance.  When None
                        (the default) a new instance is created, which
                        attempts to connect to the database.  Pass an explicit
                        instance to share one service across multiple checker
                        instances (e.g. in tests).
        """
        self._dictionary = dictionary if dictionary is not None else DictionaryService()

    def check_syllable(self, syllable: str) -> Optional[Dict]:
        """
        Check a single syllable for spelling errors.

        Pipeline:
        1. Pattern checks (raw string)
        2. Parse into TibetanSyllable
        3. Structural completeness check (raw vs parsed)
        4. Component validation (stacking rules)

        Args:
            syllable: Tibetan syllable to check

        Returns:
            Dictionary with error details if error found, None if valid
        """
        # Normalize
        syllable = normalize_tibetan(syllable)
        if not syllable:
            return None

        # 0a. Numeral syllables — skip silently, no structural rules apply
        if is_numeral_syllable(syllable):
            return None

        # 0b. Punctuation/mark syllables — yig mgo openers, decorative shads,
        #     gter tsheg, astrological marks, etc. Skip silently.
        if is_punctuation_syllable(syllable):
            return None

        # 0c. Exception list — valid by grammatical convention, not structure
        if is_excepted(syllable):
            return None

        # 1. Pattern checks (raw string, before parsing)
        pattern_error = check_syllable_patterns(syllable)
        if pattern_error:
            pattern_error['word'] = syllable
            return pattern_error

        # 2. Parse: classify characters -> parse structure
        typed_chars = type_characters(syllable)
        parsed_model = parse_syllable(typed_chars)

        # 3. Structural completeness (raw string vs parsed)
        # Uses the old dict format for backwards compatibility
        parsed_dict = parsed_model.to_dict()
        completeness_error = check_syllable_structure_completeness(syllable, parsed_dict)
        if completeness_error:
            completeness_error['word'] = syllable
            return completeness_error

        # 4. Component validation (stacking rules)
        errors = validate_syllable(parsed_model)
        if errors:
            error_dict = errors[0].to_dict()
            error_dict['word'] = syllable
            # Even though Phase 1 flagged this syllable, check whether it
            # exists in the corpus.  corpus_hit=True on a structural error
            # is a signal that the Phase 1 rule may be producing a false
            # positive on a real word — useful data for future tuning.
            in_corpus = self._dictionary.is_valid_syllable(syllable)
            error_dict['corpus_hit'] = None if in_corpus is None else bool(in_corpus)
            return error_dict

        # 5. Dictionary lookup (Phase 2) — only runs when corpus is loaded.
        # is_valid_syllable returns None when the corpus is unavailable, in
        # which case we skip rather than flag everything as unknown.
        in_corpus = self._dictionary.is_valid_syllable(syllable)
        if in_corpus is False:
            return {
                'word': syllable,
                'error_type': 'unknown_word',
                'severity': 'warning',
                'message': (
                    f"'{syllable}' is structurally valid but not found in the "
                    "word corpus. It may be a spelling error or a word we don't "
                    "have yet."
                ),
                'component': None,
                'corpus_hit': False,
            }

        # No errors found
        return None

    def check_text(self, text: str) -> List[Dict]:
        """
        Check full Tibetan text for spelling errors.

        Args:
            text: Tibetan text to check

        Returns:
            List of error dictionaries

        Raises:
            TypeError: If text is None
        """
        if text is None:
            raise TypeError("text cannot be None")

        if not text:
            return []

        # Check for non-Tibetan characters (on original text)
        non_tibetan_summary = validate_tibetan_text(text)

        # Normalize and get a mapping from normalized positions → original positions
        normalized, pos_map = normalize_tibetan_with_position_map(text)

        # Split into syllables with position tracking (positions in normalized text)
        syllables = split_syllables_with_position(normalized)

        # Check each syllable
        errors = []
        prev_parsed = None   # parsed structure of the most recent valid Tibetan syllable
        prev_had_error = False

        for item in syllables:
            syllable = item['syllable']

            if not any(is_tibetan_char(c) for c in syllable):
                # Non-Tibetan content breaks particle context
                prev_parsed = None
                prev_had_error = False
                continue

            norm_pos = item['position']
            mapped_pos = pos_map[norm_pos] if norm_pos < len(pos_map) else norm_pos

            normalized_syl = normalize_tibetan(syllable)

            # Numeral and punctuation syllables are skipped and break particle context
            if is_numeral_syllable(normalized_syl) or is_punctuation_syllable(normalized_syl):
                prev_parsed = None
                prev_had_error = False
                continue

            # Single-syllable structural check
            error = self.check_syllable(syllable)
            if error:
                error['position'] = mapped_pos
                errors.append(error)

            # Particle context check (only when current syllable is structurally valid
            # and the preceding syllable was also valid)
            if error is None and prev_parsed is not None and not prev_had_error:
                particle_error = check_particle_context(normalized_syl, prev_parsed)
                if particle_error:
                    particle_error['word'] = syllable
                    particle_error['position'] = mapped_pos
                    errors.append(particle_error)

            # Parse this syllable's structure for the next iteration's particle check.
            # check_syllable already normalizes internally, but we need the parsed
            # model here too -- reuse normalized_syl to avoid a third normalization.
            if error is None:
                typed_chars = type_characters(normalized_syl)
                prev_parsed = parse_syllable(typed_chars)
            else:
                prev_parsed = None

            prev_had_error = error is not None

        # Informational note for non-Tibetan characters
        if non_tibetan_summary['has_non_tibetan']:
            errors.append({
                'word': '',
                'position': 0,
                'error_type': 'non_tibetan_skipped',
                'severity': 'info',
                'message': f"{non_tibetan_summary['count']} non-Tibetan character(s) were skipped during spell checking"
            })

        return errors
