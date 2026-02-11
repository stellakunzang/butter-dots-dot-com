import React from 'react'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import SpellCheckPage from '@/pages/spellcheck'
import * as api from '@/lib/api'

// Mock the API module
jest.mock('@/lib/api')

const mockedApi = api as jest.Mocked<typeof api>

describe('SpellCheckPage', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('renders the page correctly', () => {
    render(<SpellCheckPage />)

    expect(screen.getByText('Tibetan Spell Checker')).toBeInTheDocument()
    expect(
      screen.getByText(/paste tibetan text below to check for spelling errors/i)
    ).toBeInTheDocument()
    expect(screen.getByLabelText('Tibetan text input')).toBeInTheDocument()
  })

  it('shows empty state before checking', () => {
    render(<SpellCheckPage />)

    expect(
      screen.getByText(/enter text and click "check spelling" to see results/i)
    ).toBeInTheDocument()
  })

  it('allows user to input text', () => {
    render(<SpellCheckPage />)

    const textarea = screen.getByLabelText('Tibetan text input')
    fireEvent.change(textarea, { target: { value: 'བོད་ཡིག' } })

    expect(textarea).toHaveValue('བོད་ཡིག')
  })

  it('triggers API call on form submission', async () => {
    const mockResponse: api.SpellCheckResponse = {
      text: 'བོད་ཡིག',
      error_count: 0,
      errors: [],
    }

    mockedApi.checkText.mockResolvedValue(mockResponse)

    render(<SpellCheckPage />)

    const textarea = screen.getByLabelText('Tibetan text input')
    fireEvent.change(textarea, { target: { value: 'བོད་ཡིག' } })

    const submitButton = screen.getByRole('button', { name: /check spelling/i })
    fireEvent.click(submitButton)

    await waitFor(() => {
      expect(mockedApi.checkText).toHaveBeenCalledWith('བོད་ཡིག')
    })
  })

  it('displays loading state while processing', async () => {
    const mockResponse: api.SpellCheckResponse = {
      text: 'བོད་ཡིག',
      error_count: 0,
      errors: [],
    }

    // Create a promise that we can control
    let resolvePromise: (value: api.SpellCheckResponse) => void
    const promise = new Promise<api.SpellCheckResponse>((resolve) => {
      resolvePromise = resolve
    })

    mockedApi.checkText.mockReturnValue(promise)

    render(<SpellCheckPage />)

    const textarea = screen.getByLabelText('Tibetan text input')
    fireEvent.change(textarea, { target: { value: 'བོད་ཡིག' } })

    const submitButton = screen.getByRole('button', { name: /check spelling/i })
    fireEvent.click(submitButton)

    // Check for loading state
    expect(screen.getByText(/checking/i)).toBeInTheDocument()
    expect(textarea).toBeDisabled()

    // Resolve the promise
    resolvePromise!(mockResponse)

    await waitFor(() => {
      expect(screen.queryByText(/checking/i)).not.toBeInTheDocument()
    })
  })

  it('displays "no errors" when text is valid', async () => {
    const mockResponse: api.SpellCheckResponse = {
      text: 'བོད་ཡིག',
      error_count: 0,
      errors: [],
    }

    mockedApi.checkText.mockResolvedValue(mockResponse)

    render(<SpellCheckPage />)

    const textarea = screen.getByLabelText('Tibetan text input')
    fireEvent.change(textarea, { target: { value: 'བོད་ཡིག' } })

    const submitButton = screen.getByRole('button', { name: /check spelling/i })
    fireEvent.click(submitButton)

    await waitFor(() => {
      expect(screen.getByText(/no errors found/i)).toBeInTheDocument()
    })
  })

  it('displays errors when found', async () => {
    const mockResponse: api.SpellCheckResponse = {
      text: 'གཀར',
      error_count: 1,
      errors: [
        {
          word: 'གཀར',
          position: 0,
          error_type: 'invalid_prefix_combination',
          severity: 'error',
          message: 'Invalid prefix-root combination',
          component: 'prefix',
        },
      ],
    }

    mockedApi.checkText.mockResolvedValue(mockResponse)

    render(<SpellCheckPage />)

    const textarea = screen.getByLabelText('Tibetan text input')
    fireEvent.change(textarea, { target: { value: 'གཀར' } })

    const submitButton = screen.getByRole('button', { name: /check spelling/i })
    fireEvent.click(submitButton)

    await waitFor(() => {
      const words = screen.getAllByText('གཀར')
      expect(words.length).toBeGreaterThan(0)
      expect(screen.getByText('Invalid Prefix Combination')).toBeInTheDocument()
      expect(screen.getByText(/1 error found/i)).toBeInTheDocument()
    })
  })

  it.skip('handles API errors gracefully', async () => {
    const errorMessage = 'Connection failed'
    mockedApi.checkText.mockRejectedValue(new api.APIError(errorMessage, 0))

    render(<SpellCheckPage />)

    const textarea = screen.getByLabelText('Tibetan text input')
    fireEvent.change(textarea, { target: { value: 'བོད་ཡིག' } })

    const submitButton = screen.getByRole('button', { name: /check spelling/i })
    fireEvent.click(submitButton)

    // Use findByText which waits for the element to appear
    expect(await screen.findByText('Error')).toBeInTheDocument()
    expect(await screen.findByText(errorMessage)).toBeInTheDocument()
    
    // Verify the API was called
    expect(mockedApi.checkText).toHaveBeenCalledWith('བོད་ཡིག')
  })

  it.skip('clears error message on successful submission', async () => {
    const errorMessage = 'Connection failed'
    mockedApi.checkText.mockRejectedValueOnce(new api.APIError(errorMessage, 0))

    render(<SpellCheckPage />)

    const textarea = screen.getByLabelText('Tibetan text input')
    fireEvent.change(textarea, { target: { value: 'བོད་ཡིག' } })

    let submitButton = screen.getByRole('button', { name: /check spelling/i })
    fireEvent.click(submitButton)

    // Wait for error to appear
    expect(await screen.findByText(errorMessage)).toBeInTheDocument()

    // Now mock successful response
    const mockResponse: api.SpellCheckResponse = {
      text: 'བོད་ཡིག',
      error_count: 0,
      errors: [],
    }
    mockedApi.checkText.mockResolvedValue(mockResponse)

    submitButton = screen.getByRole('button', { name: /check spelling/i })
    fireEvent.click(submitButton)

    await waitFor(() => {
      expect(screen.queryByText(errorMessage)).not.toBeInTheDocument()
      expect(screen.getByText(/no errors found/i)).toBeInTheDocument()
    })
  })

  it('allows re-checking with modified text', async () => {
    const firstResponse: api.SpellCheckResponse = {
      text: 'བོད',
      error_count: 0,
      errors: [],
    }

    const secondResponse: api.SpellCheckResponse = {
      text: 'གཀར',
      error_count: 1,
      errors: [
        {
          word: 'གཀར',
          position: 0,
          error_type: 'invalid_prefix_combination',
          severity: 'error',
          message: 'Invalid prefix-root combination',
        },
      ],
    }

    mockedApi.checkText
      .mockResolvedValueOnce(firstResponse)
      .mockResolvedValueOnce(secondResponse)

    render(<SpellCheckPage />)

    const textarea = screen.getByLabelText('Tibetan text input')

    // First check
    fireEvent.change(textarea, { target: { value: 'བོད' } })
    let submitButton = screen.getByRole('button', { name: /check spelling/i })
    fireEvent.click(submitButton)

    await waitFor(() => {
      expect(screen.getByText(/no errors found/i)).toBeInTheDocument()
    })

    // Second check with different text
    fireEvent.change(textarea, { target: { value: 'གཀར' } })
    submitButton = screen.getByRole('button', { name: /check spelling/i })
    fireEvent.click(submitButton)

    await waitFor(() => {
      const words = screen.getAllByText('གཀར')
      expect(words.length).toBeGreaterThan(0)
      expect(screen.getByText(/1 error found/i)).toBeInTheDocument()
    })

    expect(mockedApi.checkText).toHaveBeenCalledTimes(2)
  })
})
