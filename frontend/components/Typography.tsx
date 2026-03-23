import React from 'react'

interface Props {
  children: React.ReactNode
  className?: string
}

interface SectionHeadingProps extends Props {
  as?: 'h2' | 'h3' | 'h4'
}

export function PageTitle({children, className = ''}: Props) {
  return (
    <h1
      className={`text-5xl md:text-6xl font-serif text-gray-900 mb-4 tracking-tight ${className}`.trim()}
    >
      {children}
    </h1>
  )
}

export function SectionHeading({children, className = '', as: Tag = 'h2'}: SectionHeadingProps) {
  return (
    <Tag
      className={`text-2xl font-serif text-gray-900 mt-8 mb-4 ${className}`.trim()}
    >
      {children}
    </Tag>
  )
}
