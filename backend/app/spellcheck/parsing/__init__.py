"""
Parsing stage of the spellcheck pipeline.

Assembles TypedChar lists into a TibetanSyllable model,
using stacking rules to make structural decisions.

Re-exports:
    parse_syllable: Parse typed characters into a TibetanSyllable
"""
from .parser import parse_syllable

__all__ = ['parse_syllable']
