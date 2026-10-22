import React from 'react'
import {SpellErrorExample} from '../../content/learn/errors'

export function ErrorExample({type, example, description, fix}: SpellErrorExample) {
  return (
    <div className="p-5 bg-white rounded-lg border border-gray-200">
      <div className="flex items-start gap-4 flex-wrap">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-3 mb-2 flex-wrap">
            <h4 className="text-base font-semibold text-gray-900 m-0">{type}</h4>
            {example && (
              <span className="text-lg text-red-600 font-medium">{example}</span>
            )}
          </div>
          <p className="text-sm text-gray-600 mb-2">{description}</p>
          <p className="text-sm text-gray-500">
            <span className="font-medium text-gray-700">Fix: </span>
            {fix}
          </p>
        </div>
      </div>
    </div>
  )
}
