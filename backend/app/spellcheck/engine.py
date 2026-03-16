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
from .normalizer import normalize_tibetan, normalize_tibetan_with_position_map, is_tibetan_char, validate_tibetan_text, is_numeral_syllable
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


class TibetanSpellChecker:
    """
    Main Tibetan spell checking engine.

    Integrates Unicode normalization, syllable parsing, and validation
    to check Tibetan text for spelling errors.
    """

    def __init__(self):
        """Initialize the spell checker."""
        pass

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

        # 0b. Exception list — valid by grammatical convention, not structure
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
            # Return the first error as a dict for backwards compatibility
            error_dict = errors[0].to_dict()
            error_dict['word'] = syllable
            return error_dict

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

            # Numeral syllables are skipped and break particle context
            if is_numeral_syllable(normalized_syl):
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
