import React from 'react'
import {
  SYLLABLE_COMPOSED,
  SYLLABLE_EXAMPLE,
} from '../../content/learn/syllable'

export function SyllableAnatomy() {
  return (
    <div className="my-8 p-6 bg-gray-50 rounded-xl border border-gray-200 overflow-x-auto">
      <table className="w-full text-center border-collapse">
        <thead>
          <tr>
            {SYLLABLE_EXAMPLE.map(cell => (
              <th
                key={cell.role}
                className={[
                  'px-4 py-2 text-xs uppercase tracking-wider text-gray-400 font-medium border-b border-gray-200',
                  cell.root ? 'bg-yellow-50' : '',
                ].join(' ')}
              >
                {cell.role}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          <tr>
            {SYLLABLE_EXAMPLE.map(cell => (
              <td
                key={cell.role}
                className={[
                  'px-4 py-3 text-sm',
                  cell.root
                    ? 'text-gray-900 font-semibold bg-yellow-50'
                    : 'text-gray-500',
                ].join(' ')}
              >
                {cell.position}
              </td>
            ))}
          </tr>
          <tr className="border-t border-gray-100">
            {SYLLABLE_EXAMPLE.map(cell => (
              <td
                key={cell.role}
                className={[
                  'px-4 py-3',
                  cell.root
                    ? 'text-3xl font-semibold text-gray-900 bg-yellow-50'
                    : cell.muted
                      ? 'text-gray-400 text-sm'
                      : 'text-2xl text-gray-700',
                ].join(' ')}
              >
                {cell.glyph}
              </td>
            ))}
          </tr>
          <tr className="border-t border-gray-100">
            <td colSpan={SYLLABLE_EXAMPLE.length} className="px-4 py-3 text-center">
              <span className="text-2xl text-gray-900 mr-4">
                {SYLLABLE_COMPOSED.glyph}
              </span>
              <span className="text-gray-500 text-sm">{SYLLABLE_COMPOSED.gloss}</span>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  )
}
