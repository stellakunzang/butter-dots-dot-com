import type {NextPage} from 'next'
import Link from 'next/link'
import {Layout, PageTitle} from '../../components'

const GUIDES: {href: string; title: string; summary: string}[] = [
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

const Learn: NextPage = () => {
  return (
    <Layout
      title="Learn - Butter Dots"
      description="Guides to typing Tibetan, spelling rules, and reading a sentence"
    >
      <div className="mb-12 max-w-4xl mx-auto border-b-2 border-gray-200 pb-8">
        <div className="mb-4">
          <span className="text-sm uppercase tracking-wider text-gray-500 font-medium">
            Learn
          </span>
        </div>
        <PageTitle>Learn</PageTitle>
        <p className="text-xl text-gray-600 font-light leading-relaxed">
          Short guides for working with Tibetan on a computer, and for reading
          what you type.
        </p>
      </div>

      <div className="max-w-4xl mx-auto grid grid-cols-1 gap-5">
        {GUIDES.map(guide => (
          <Link
            key={guide.href}
            href={guide.href}
            className="block p-6 md:p-8 bg-white rounded-xl border border-gray-200 shadow-sm hover:border-gray-300 hover:shadow-md transition-all"
          >
            <h2 className="text-2xl font-serif text-gray-900 mt-0 mb-2">
              {guide.title}
            </h2>
            <p className="text-gray-600 leading-relaxed m-0">{guide.summary}</p>
          </Link>
        ))}
      </div>
    </Layout>
  )
}

export default Learn
