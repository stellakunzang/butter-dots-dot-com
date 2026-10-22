export interface ParticleRow {
  particle: string
  suffixes: string
  example: string
  exampleGloss: string
  lenient?: boolean
  rare?: boolean
}

export const RELATIONAL_PARTICLES: ParticleRow[] = [
  {
    particle: 'ཀྱི',
    suffixes: 'ད  བ  ས',
    example: 'བོད་ཀྱི་',
    exampleGloss: 'of Tibet',
  },
  {
    particle: 'གི',
    suffixes: 'ག  ང',
    example: 'ཆོས་གི་',
    exampleGloss: 'of the dharma',
  },
  {
    particle: 'གྱི',
    suffixes: 'ན  མ  ར  ལ',
    example: 'སེམས་ཅན་གྱི་',
    exampleGloss: 'of beings',
  },
  {
    particle: 'འི',
    suffixes: 'འ  or no suffix',
    example: 'ལྷའི་',
    exampleGloss: 'of the deity',
  },
  {
    particle: 'ཡི',
    suffixes: 'any (lenient variant)',
    example: 'ལྷ་ཡི་',
    exampleGloss: 'used in poetry for metrical reasons',
    lenient: true,
  },
]

export const AGENTIVE_PARTICLES: ParticleRow[] = [
  {
    particle: 'ཀྱིས',
    suffixes: 'ད  བ  ས',
    example: 'བོད་ཀྱིས་',
    exampleGloss: 'by Tibet',
  },
  {
    particle: 'གིས',
    suffixes: 'ག  ང',
    example: 'ཆོས་གིས་',
    exampleGloss: 'by the dharma',
  },
  {
    particle: 'གྱིས',
    suffixes: 'ན  མ  ར  ལ',
    example: 'སེམས་ཅན་གྱིས་',
    exampleGloss: 'by beings',
  },
  {
    particle: 'ས',
    suffixes: 'འ  or no suffix',
    example: 'ལྷས་',
    exampleGloss: 'by the deity',
  },
  {
    particle: 'ཡིས',
    suffixes: 'any (lenient variant)',
    example: '',
    exampleGloss: 'used in poetry for metrical reasons',
    lenient: true,
  },
]

export const LOCATIVE_PARTICLES: ParticleRow[] = [
  {
    particle: 'ན',
    suffixes: 'any suffix or no suffix',
    example: 'བོད་ན་',
    exampleGloss: 'in Tibet',
  },
  {
    particle: 'ལ',
    suffixes: 'any suffix or no suffix',
    example: 'བོད་ལ་',
    exampleGloss: 'to Tibet',
  },
  {
    particle: 'སུ',
    suffixes: 'ས',
    example: 'ཆོས་སུ་',
    exampleGloss: 'into the dharma',
  },
  {
    particle: 'ཏུ',
    suffixes: 'ག  བ  (or post-suffix ད)',
    example: 'ཕྱོགས་ཏུ་',
    exampleGloss: 'in the direction',
  },
  {
    particle: 'དུ',
    suffixes: 'ང  ད  ན  མ  ར  ལ',
    example: 'བར་དུ་',
    exampleGloss: 'until',
  },
  {
    particle: 'རུ',
    suffixes: 'འ  or no suffix',
    example: 'བཀའ་རུ་',
    exampleGloss: 'into the command; according to the decree',
    rare: true,
  },
  {
    particle: 'ར',
    suffixes: 'འ',
    example: 'ཆེར་',
    exampleGloss: 'greatly',
  },
]

export const INDEFINITE_PARTICLES: ParticleRow[] = [
  {
    particle: 'ཅིག',
    suffixes: 'ག  ད  བ',
    example: 'ཆོས་ཅིག་',
    exampleGloss: 'a dharma',
  },
  {
    particle: 'ཤིག',
    suffixes: 'ས',
    example: 'ཕྱོགས་ཤིག་',
    exampleGloss: 'a direction',
  },
  {
    particle: 'ཞིག',
    suffixes: 'ང  ན  མ  ར  ལ  འ  or no suffix',
    example: 'ལྷ་ཞིག་',
    exampleGloss: 'a deity',
  },
]
