export interface SpellErrorExample {
  type: string
  example: string
  description: string
  fix: string
}

export const SPELL_ERROR_EXAMPLES: SpellErrorExample[] = [
  {
    type: 'Wrong particle form',
    example: 'བོད་གི་',
    description:
      "The particle doesn't match the suffix of the word before it. Here གི་ is used after བོད་ (which ends in ད), but ད calls for ཀྱི་.",
    fix: 'Use ཀྱི་ after words ending in ད, བ, or ས.',
  },
  {
    type: 'Invalid prefix combination',
    example: 'ཧཧིབ་',
    description:
      'The letter before the root is not a valid prefix for that root. ཧ cannot act as a prefix.',
    fix: 'Only the five prefix letters (ག ད བ མ འ) can precede a root, and only in attested combinations.',
  },
  {
    type: 'Invalid superscript combination',
    example: '',
    description:
      'A superscript letter is stacked above a root it cannot combine with. Each of the three superscripts (ར ལ ས) only stacks above specific roots — for example, ས can sit above ཀ to form སྐ, but not above ར.',
    fix: 'Check which roots are valid for that superscript.',
  },
  {
    type: 'Invalid subscript combination',
    example: 'ངྱི',
    description:
      'The subscript below the root is not valid for that root. ང cannot take ཡ་བཏགས.',
    fix: 'Subscripts (ྱ ྲ ླ ྭ) only combine with certain roots.',
  },
  {
    type: 'Invalid suffix',
    example: 'ཀཝ་',
    description: 'The letter after the root is not one of the ten valid suffixes.',
    fix: 'Only these ten letters can be suffixes: ག ང ད ན བ མ འ ར ལ ས.',
  },
  {
    type: 'Double vowel',
    example: '',
    description:
      'Two vowel marks appear on the same syllable, which is structurally impossible.',
    fix: 'Each syllable can only carry one vowel mark.',
  },
  {
    type: 'Encoding error (critical)',
    example: 'wrong character',
    description:
      'A character that looks like Tibetan is actually the wrong Unicode codepoint — a common issue when text is copied from certain older fonts or systems.',
    fix: 'Re-type the syllable from scratch using a Unicode Tibetan keyboard, or use a font conversion tool.',
  },
]
