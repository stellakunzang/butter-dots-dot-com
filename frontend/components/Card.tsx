import React from 'react'

interface CardProps {
  children: React.ReactNode
  title?: string
  variant?: 'default' | 'bordered' | 'elevated'
  className?: string
}

export const Card: React.FC<CardProps> = ({
  children,
  title,
  variant = 'default',
  className = '',
}) => {
  const variantClasses = {
    default: 'p-6 rounded-lg my-4 bg-gray-50',
    bordered: 'p-6 rounded-lg my-4 bg-white border border-gray-200',
    elevated: 'p-6 rounded-lg my-4 bg-white shadow-md',
  }
  
  return (
    <div className={`${variantClasses[variant]} ${className}`}>
      {title && (
        <h4 className="mt-0 mb-4 text-gray-800 text-lg font-semibold">
          {title}
        </h4>
      )}
      <div className="text-gray-600 leading-relaxed">
        {children}
      </div>
    </div>
  )
}
