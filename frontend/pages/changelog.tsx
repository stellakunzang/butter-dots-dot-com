import type {GetStaticProps, NextPage} from 'next'
import {Layout, PageTitle} from '../components'
import {parseChangelog, VersionEntry, ChangeCategory} from '../lib/changelog'

interface Props {
  entries: VersionEntry[]
}

const CATEGORY_STYLES: Record<ChangeCategory, {dot: string; label: string}> = {
  Added:      {dot: 'bg-emerald-400', label: 'text-emerald-700'},
  Changed:    {dot: 'bg-blue-400',    label: 'text-blue-700'},
  Deprecated: {dot: 'bg-amber-400',   label: 'text-amber-700'},
  Removed:    {dot: 'bg-red-400',     label: 'text-red-700'},
  Fixed:      {dot: 'bg-violet-400',  label: 'text-violet-700'},
  Security:   {dot: 'bg-orange-400',  label: 'text-orange-700'},
}

const Changelog: NextPage<Props> = ({entries}) => {
  const released = entries.filter(e => !e.isUnreleased)
  const unreleased = entries.find(e => e.isUnreleased)

  return (
    <Layout
      title="Changelog — Butter Dots"
      description="What's new in the Tibetan spellchecker"
      showBackLink
    >
      <div className="mb-12 max-w-3xl mx-auto border-b-2 border-gray-200 pb-8">
        <div className="mb-4">
          <span className="text-sm uppercase tracking-wider text-gray-500 font-medium">
            Release History
          </span>
        </div>
        <PageTitle>Changelog</PageTitle>
        <p className="text-xl text-gray-600 font-light leading-relaxed">
          A record of improvements, fixes, and new features — newest first.
        </p>
      </div>

      <div className="max-w-3xl mx-auto space-y-16">
        {unreleased && unreleased.categories.length > 0 && (
          <VersionBlock entry={unreleased} />
        )}

        {released.map(entry => (
          <VersionBlock key={entry.version} entry={entry} />
        ))}

        {released.length === 0 && !unreleased?.categories.length && (
          <p className="text-gray-500">No releases yet.</p>
        )}
      </div>
    </Layout>
  )
}

function VersionBlock({entry}: {entry: VersionEntry}) {
  return (
    <div>
      <div className="flex items-baseline gap-4 mb-6 pb-3 border-b border-gray-200">
        <h2 className="text-3xl font-serif text-gray-900">
          {entry.isUnreleased ? 'Unreleased' : entry.version}
        </h2>
        {entry.date && (
          <span className="text-sm text-gray-400 tabular-nums">{entry.date}</span>
        )}
      </div>

      {entry.categories.length === 0 ? (
        <p className="text-gray-500 italic">Nothing yet.</p>
      ) : (
        <div className="space-y-8">
          {entry.categories.map(block => {
            const style = CATEGORY_STYLES[block.type]
            return (
              <div key={block.type}>
                <div className="flex items-center gap-2 mb-3">
                  <span className={`inline-block w-2 h-2 rounded-full ${style.dot}`} />
                  <h3 className={`text-xs uppercase tracking-widest font-semibold ${style.label}`}>
                    {block.type}
                  </h3>
                </div>
                <ul className="space-y-2">
                  {block.items.map((item, i) => (
                    <li
                      key={i}
                      className="pl-5 relative text-gray-700 leading-relaxed
                        before:content-['—'] before:absolute before:left-0
                        before:text-gray-300 before:font-normal"
                    >
                      {item}
                    </li>
                  ))}
                </ul>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}

export const getStaticProps: GetStaticProps<Props> = async () => {
  const entries = parseChangelog()
  return {props: {entries}}
}

export default Changelog
