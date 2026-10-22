import React from 'react'

export function WylieExample({
  wylie,
  tibetan,
}: {
  wylie: string
  tibetan: string
}) {
  return (
    <div className="flex items-center gap-3 my-3 flex-wrap">
      <code className="bg-gray-100 px-2 py-1 rounded font-mono text-sm text-pink-600 border border-gray-200">
        {wylie}
      </code>
      <span className="text-gray-400 font-bold text-xl">{'\u2192'}</span>
      <span
        className="text-3xl text-gray-900 leading-relaxed"
        style={{fontFamily: 'Jomolhari, serif'}}
      >
        {tibetan}
      </span>
    </div>
  )
}
