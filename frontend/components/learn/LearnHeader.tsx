import React from 'react'
import {PageTitle} from '../Typography'

export function LearnHeader({
  title,
  lede,
  children,
}: {
  title: string
  lede: React.ReactNode
  children?: React.ReactNode
}) {
  return (
    <div className="mb-12 max-w-4xl mx-auto border-b-2 border-gray-200 pb-8">
      <div className="mb-4">
        <span className="text-sm uppercase tracking-wider text-gray-500 font-medium">
          Learn
        </span>
      </div>
      <PageTitle>{title}</PageTitle>
      <p className="text-xl text-gray-600 font-light leading-relaxed">{lede}</p>
      {children}
    </div>
  )
}
