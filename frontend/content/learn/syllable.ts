export interface SyllableCell {
  role: string
  position: string
  glyph: string
  root?: boolean
  muted?: boolean
}

/** བསྒྲུབ, "to accomplish", split into syllable positions. */
export const SYLLABLE_EXAMPLE: SyllableCell[] = [
  {role: 'Prefix', position: 'before root', glyph: 'བ'},
  {role: 'Superscript', position: 'above root', glyph: 'ས'},
  {role: 'Root', position: 'root letter', glyph: 'ག', root: true},
  {role: 'Subscript', position: 'below root', glyph: 'ྲ', muted: true},
  {role: 'Vowel', position: 'above or below stack', glyph: 'ུ'},
  {role: 'Suffix', position: 'after root', glyph: 'བ'},
  {role: 'Post-suffix', position: 'final', glyph: '—', muted: true},
]

export const SYLLABLE_COMPOSED = {
  glyph: 'བསྒྲུབ',
  gloss: 'to accomplish',
}
