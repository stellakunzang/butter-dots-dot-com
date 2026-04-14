import React from 'react'
import {render, screen} from '@testing-library/react'
import {ErrorDisplay} from '../ErrorDisplay'
import {SpellCheckError, SpellCheckResponse} from '@/lib/api'

describe('ErrorDisplay', () => {
  const mockErrors: SpellCheckError[] = [
    {
      word: 'གཀར',
      position: 0,
      error_type: 'invalid_prefix_combination',
      severity: 'error',
      message: 'Invalid prefix-root combination',
      component: 'prefix',
    },
    {
      word: 'དངས',
      position: 10,
      error_type: 'invalid_prefix',
      severity: 'error',
      message: 'This prefix cannot be used with this root',
    },
  ]

  const mockResponse: SpellCheckResponse = {
    text: 'གཀར་དངས་',
    error_count: 2,
    errors: mockErrors,
  }

  it('shows "no errors" message when errors array is empty', () => {
    const emptyResponse: SpellCheckResponse = {
      text: 'བོད་ཡིག',
      error_count: 0,
      errors: [],
    }
    render(<ErrorDisplay response={emptyResponse} />)

    expect(screen.getByText(/no spelling errors found/i)).toBeInTheDocument()
    expect(
      screen.getByText(/your tibetan text has correct spelling/i),
    ).toBeInTheDocument()
  })

  it('displays error count', () => {
    render(<ErrorDisplay response={mockResponse} />)

    expect(screen.getByText(/2 errors/i)).toBeInTheDocument()
  })

  it('displays singular error count', () => {
    const singleErrorResponse: SpellCheckResponse = {
      text: 'གཀར་',
      error_count: 1,
      errors: [mockErrors[0]],
    }
    render(<ErrorDisplay response={singleErrorResponse} />)

    expect(screen.getByText(/1 error/i)).toBeInTheDocument()
  })

  it('renders each error with details', () => {
    render(<ErrorDisplay response={mockResponse} />)

    // Check for words
    const words = screen.getAllByText('གཀར')
    expect(words.length).toBeGreaterThan(0)
    const words2 = screen.getAllByText('དངས')
    expect(words2.length).toBeGreaterThan(0)

    // Check for error types (formatted)
    expect(screen.getByText('Invalid Prefix Combination')).toBeInTheDocument()
    expect(screen.getByText('Invalid Prefix')).toBeInTheDocument()

    // Check for messages
    expect(
      screen.getByText(/this prefix cannot be used with this root/i),
    ).toBeInTheDocument()
  })

  it('displays position information', () => {
    render(<ErrorDisplay response={mockResponse} />)

    const positionLabels = screen.getAllByText(/position:/i)
    expect(positionLabels.length).toBeGreaterThan(0)
    expect(screen.getByText('0')).toBeInTheDocument()
    expect(screen.getByText('10')).toBeInTheDocument()
  })

  it('displays component information when available', () => {
    render(<ErrorDisplay response={mockResponse} />)

    expect(screen.getByText(/component:/i)).toBeInTheDocument()
    expect(screen.getByText('prefix')).toBeInTheDocument()
  })

  it('renders severity badges', () => {
    render(<ErrorDisplay response={mockResponse} />)

    const errorBadges = screen.getAllByText('ERROR')
    expect(errorBadges.length).toBeGreaterThan(0)
  })

  it('applies correct severity badge colors', () => {
    const {container} = render(<ErrorDisplay response={mockResponse} />)

    const errorBadge = container.querySelector('.bg-red-100')
    expect(errorBadge).toBeInTheDocument()
  })

  it('handles errors without optional fields', () => {
    const minimalError: SpellCheckError = {
      word: 'བོད',
      position: 5,
      error_type: 'test_error',
      severity: 'error',
    }

    const minimalResponse: SpellCheckResponse = {
      text: 'བོད་',
      error_count: 1,
      errors: [minimalError],
    }

    render(<ErrorDisplay response={minimalResponse} />)

    expect(screen.getByText('བོད')).toBeInTheDocument()
    expect(screen.getByText(/test error/i)).toBeInTheDocument()
  })

  it('formats error types correctly', () => {
    const error: SpellCheckError = {
      word: 'test',
      position: 0,
      error_type: 'invalid_superscript_combination',
      severity: 'error',
    }

    const response: SpellCheckResponse = {
      text: 'test',
      error_count: 1,
      errors: [error],
    }

    render(<ErrorDisplay response={response} />)

    expect(screen.getByText('ERROR')).toBeInTheDocument()
  })

  it('renders checkmark icon when no errors', () => {
    const emptyResponse: SpellCheckResponse = {
      text: 'བོད་ཡིག',
      error_count: 0,
      errors: [],
    }
    const {container} = render(<ErrorDisplay response={emptyResponse} />)

    const checkIcon = container.querySelector('svg')
    expect(checkIcon).toBeInTheDocument()
  })

  it('filters out info messages from error display', () => {
    const withInfoResponse: SpellCheckResponse = {
      text: 'བོད་ABC',
      error_count: 2,
      errors: [
        mockErrors[0],
        {
          word: '',
          position: -1,
          error_type: 'non_tibetan_skipped',
          severity: 'info',
          message: '3 non-Tibetan character(s) were skipped',
        },
      ],
    }

    render(<ErrorDisplay response={withInfoResponse} />)

    // Should show info message but not count it as spelling error
    expect(screen.getByText(/1 error/i)).toBeInTheDocument()
    expect(screen.getByText(/skipped/i)).toBeInTheDocument()
  })
})
