export interface LearnGuide {
  href: string
  title: string
  summary: string
}

export const LEARN_GUIDES: LearnGuide[] = [
  {
    href: '/learn/typing-tibetan',
    title: 'How to Type Tibetan',
    summary:
      'What Wylie is, how to turn it on on a Mac, Windows computer, or phone, and which font to use so Tibetan looks right.',
  },
  {
    href: '/learn/spelling-rules',
    title: 'Spelling Rules',
    summary:
      'How a Tibetan syllable is built, and which particle spellings are correct after which letters.',
  },
  {
    href: '/learn/sentence-structure',
    title: 'Reading a Tibetan Sentence',
    summary:
      'How to find where words begin and end, and what the particles are doing in a sentence.',
  },
]
