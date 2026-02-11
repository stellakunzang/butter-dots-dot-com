"""
Character typing stage of the spellcheck pipeline.

Classifies each character in a string by its Unicode type.

Re-exports:
    type_characters: Classify characters in a Tibetan string
"""
from .char_typer import type_characters

__all__ = ['type_characters']
