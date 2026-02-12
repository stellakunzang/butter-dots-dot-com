"""
Tibetan Syllable Parser

Main parser for analyzing Tibetan syllable structure.

Delegates to the new pipeline (char_typing -> parsing) and provides
backwards-compatible dict output via TibetanSyllable.to_dict().

Syllable structure:
    PREFIX + SUPERSCRIPT + ROOT + SUBSCRIPT(S) + VOWEL + SUFFIX + POST-SUFFIX
"""
from typing import Dict
from .char_typing import type_characters
from .parsing import parse_syllable
from .splitter import split_syllables, split_syllables_with_position


class TibetanSyllableParser:
    """
    Parser for Tibetan syllable structure.

    Uses the new three-stage pipeline internally:
    1. Classify characters (char_typing)
    2. Parse structure (parsing) using stacking rules
    3. Return TibetanSyllable (or dict for backwards compatibility)
    """

    def parse(self, syllable: str) -> Dict[str, any]:
        """
        Parse a Tibetan syllable into its grammatical components.

        Returns dict for backwards compatibility. Use parse_to_model()
        for the TibetanSyllable dataclass.

        Args:
            syllable: Single Tibetan syllable (no tsheg)

        Returns:
            Dictionary with components:
            {
                'prefix': str | None,
                'superscript': str | None,
                'root': str,
                'subscripts': list[str],
                'vowels': list[str],
                'suffix': str | None,
                'post_suffix': str | None,
                'raw': str
            }
        """
        model = self.parse_to_model(syllable)
        return model.to_dict()

    def parse_to_model(self, syllable: str):
        """
        Parse a Tibetan syllable into a TibetanSyllable dataclass.

        This is the preferred method for new code.

        Args:
            syllable: Single Tibetan syllable (no tsheg)

        Returns:
            TibetanSyllable with all components identified
        """
        if not syllable:
            from .data_types import TibetanSyllable
            return TibetanSyllable(raw="")

        typed_chars = type_characters(syllable)
        return parse_syllable(typed_chars)


# Re-export splitting functions for backwards compatibility
__all__ = ['TibetanSyllableParser', 'split_syllables', 'split_syllables_with_position']
