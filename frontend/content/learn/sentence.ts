export const EXAMPLE_SENTENCE =
  'མ་ནམ་མཁའ་དང་མཉམ་པའི་སེམས་ཅན་ཐམས་ཅད་བདེ་བ་དང་བདེ་བའི་རྒྱུ་དང་ལྡན་པར་གྱུར་ཅིག།'

export const EXAMPLE_SYLLABLES = EXAMPLE_SENTENCE.replace(/[།\s]/g, '')
  .split('་')
  .filter(Boolean)

export const EXAMPLE_WORDS: {tibetan: string; gloss: string}[] = [
  {tibetan: 'མ', gloss: 'mother'},
  {tibetan: 'ནམ་མཁའ', gloss: 'space'},
  {tibetan: 'དང', gloss: 'and'},
  {tibetan: 'མཉམ་པའི', gloss: 'equal'},
  {tibetan: 'སེམས་ཅན', gloss: 'sentient beings'},
  {tibetan: 'ཐམས་ཅད', gloss: 'all'},
  {tibetan: 'བདེ་བ', gloss: 'happiness'},
  {tibetan: 'དང', gloss: 'and'},
  {tibetan: 'བདེ་བའི', gloss: 'of happiness'},
  {tibetan: 'རྒྱུ', gloss: 'cause'},
  {tibetan: 'དང', gloss: 'and'},
  {tibetan: 'ལྡན་པར', gloss: 'endowed with'},
  {tibetan: 'གྱུར་ཅིག', gloss: 'may they become'},
]
