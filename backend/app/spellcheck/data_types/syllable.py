"""
TibetanSyllable -- the canonical parsed syllable representation.
"""
from dataclasses import dataclass, field
from typing import Optional, List


@dataclass
class TibetanSyllable:
    """
    A fully parsed Tibetan syllable with all components identified.

    This is the canonical output of the parser. Root is always stored in
    base form, making it directly usable as a dictionary lookup key.

    Syllable structure:
        PREFIX + SUPERSCRIPT + ROOT + SUBSCRIPT(S) + VOWEL + SUFFIX + SUFFIX-VOWEL + POST-SUFFIX

    Attributes:
        raw: The original syllable string
        prefix: Optional prefix letter (one of ག ད བ མ འ ར)
        superscript: Optional superscript letter (one of ར ལ ས)
        root: The root consonant, always in base form
        subscripts: Subscript letters below root (ྱ ྲ ླ ྭ)
        vowel: The vowel mark, or None for inherent 'a'
        suffix: Optional suffix letter
        suffix_vowel: Optional vowel on the suffix (ི on འ for relational འི)
        post_suffix: Optional post-suffix letter (ད or ས)
        unparsed: Characters the parser could not assign to a component
    """
    raw: str
    prefix: Optional[str] = None
    superscript: Optional[str] = None
    root: Optional[str] = None
    subscripts: List[str] = field(default_factory=list)
    vowel: Optional[str] = None
    suffix: Optional[str] = None
    suffix_vowel: Optional[str] = None
    post_suffix: Optional[str] = None
    unparsed: list = field(default_factory=list)  # List[TypedChar]

    @property
    def root_letter(self) -> Optional[str]:
        """Root in base form -- the dictionary lookup key."""
        return self.root

    @property
    def has_superscript(self) -> bool:
        return self.superscript is not None

    @property
    def has_subscript(self) -> bool:
        return len(self.subscripts) > 0

    def to_dict(self) -> dict:
        """
        Convert to dictionary format for backwards compatibility.

        Returns the same dict shape as the old TibetanSyllableParser.parse()
        so existing code continues to work during migration.
        """
        return {
            'prefix': self.prefix,
            'superscript': self.superscript,
            'root': self.root,
            'subscripts': self.subscripts,
            'vowels': [self.vowel] if self.vowel else [],
            'suffix': self.suffix,
            'suffix_vowel': self.suffix_vowel,
            'post_suffix': self.post_suffix,
            'raw': self.raw,
        }
