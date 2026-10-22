import type {NextPage} from 'next'
import Link from 'next/link'
import {Layout} from '../../components'
import {LearnHeader} from '../../components/learn/LearnHeader'
import {LEARN_GUIDES} from '../../content/learn/guides'

const Learn: NextPage = () => {
  return (
    <Layout
      title="Learn - Butter Dots"
      description="Guides to typing Tibetan, spelling rules, and reading a sentence"
    >
      <LearnHeader
        title="Learn"
        lede="Short guides for working with Tibetan on a computer, and for reading what you type."
      />

      <div className="max-w-4xl mx-auto grid grid-cols-1 gap-5">
        {LEARN_GUIDES.map(guide => (
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
