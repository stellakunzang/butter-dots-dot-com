import React from 'react'
import {ParticleRow} from '../../content/learn/particles'

export function ParticleTable({rows}: {rows: ParticleRow[]}) {
  return (
    <div className="overflow-x-auto rounded-lg border border-gray-200 mb-2">
      <table className="w-full text-sm border-collapse">
        <thead className="bg-gray-50">
          <tr>
            <th className="px-4 py-3 text-left text-xs uppercase tracking-wider text-gray-500 font-medium border-b border-gray-200 w-24">
              Particle
            </th>
            <th className="px-4 py-3 text-left text-xs uppercase tracking-wider text-gray-500 font-medium border-b border-gray-200">
              Used after suffix
            </th>
            <th className="px-4 py-3 text-left text-xs uppercase tracking-wider text-gray-500 font-medium border-b border-gray-200">
              Example
            </th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row, i) => (
            <tr
              key={row.particle}
              className={[
                i < rows.length - 1 ? 'border-b border-gray-100' : '',
                row.lenient || row.rare ? 'bg-gray-50' : 'bg-white',
              ].join(' ')}
            >
              <td className="px-4 py-3">
                <span className="text-2xl text-gray-900">{row.particle}</span>
                {row.lenient && (
                  <span className="ml-2 text-xs text-gray-400 align-middle">
                    lenient
                  </span>
                )}
                {row.rare && (
                  <span className="ml-2 text-xs text-gray-400 align-middle">
                    rare
                  </span>
                )}
              </td>
              <td className="px-4 py-3 text-gray-600 font-mono tracking-wide">
                {row.suffixes}
              </td>
              <td className="px-4 py-3">
                {row.example && (
                  <>
                    <span className="text-xl text-gray-900 mr-2">
                      {row.example}
                    </span>
                    <span className="text-gray-400 italic">
                      {row.exampleGloss}
                    </span>
                  </>
                )}
                {!row.example && (
                  <span className="text-gray-400 italic">
                    {row.exampleGloss}
                  </span>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
