import React from 'react'

interface SectionProps {
  children: React.ReactNode
  title?: string
  variant?: 'default' | 'highlight' | 'minimal'
  className?: string
}

export const Section: React.FC<SectionProps> = ({
  children,
  title,
  variant = 'default',
  className = '',
}) => {
  const variantClasses = {
    default: 'my-8 p-8 bg-white rounded-xl shadow-sm',
    highlight: 'my-8 p-8 bg-white border-l-4 border-primary-500 rounded-xl shadow-md',
    minimal: 'my-8 py-4',
  }
  
  return (
    <section className={`${variantClasses[variant]} ${className}`}>
      {title && (
        <h2 className="mt-0 mb-6 text-gray-800 text-3xl font-serif border-b-2 border-butter-600 pb-2">
          {title}
        </h2>
      )}
      <div className="text-gray-600 leading-relaxed">
        {children}
      </div>
    </section>
  )
}
