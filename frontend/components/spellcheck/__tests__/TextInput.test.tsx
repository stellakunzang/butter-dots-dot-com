import React from 'react'
import { render, screen, fireEvent } from '@testing-library/react'
import { TextInput } from '../TextInput'

describe('TextInput', () => {
  const mockOnChange = jest.fn()
  const mockOnSubmit = jest.fn()

  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('renders textarea and submit button', () => {
    render(
      <TextInput
        value=""
        onChange={mockOnChange}
        onSubmit={mockOnSubmit}
        loading={false}
      />
    )

    expect(screen.getByLabelText('Tibetan text input')).toBeInTheDocument()
    expect(
      screen.getByRole('button', { name: /check spelling/i })
    ).toBeInTheDocument()
  })

  it('displays placeholder text', () => {
    const placeholder = 'Enter text here'
    render(
      <TextInput
        value=""
        onChange={mockOnChange}
        onSubmit={mockOnSubmit}
        loading={false}
        placeholder={placeholder}
      />
    )

    expect(screen.getByPlaceholderText(placeholder)).toBeInTheDocument()
  })

  it('calls onChange when text changes', () => {
    render(
      <TextInput
        value=""
        onChange={mockOnChange}
        onSubmit={mockOnSubmit}
        loading={false}
      />
    )

    const textarea = screen.getByLabelText('Tibetan text input')
    fireEvent.change(textarea, { target: { value: 'བོད་ཡིག' } })

    expect(mockOnChange).toHaveBeenCalledWith('བོད་ཡིག')
  })

  it('calls onSubmit when form is submitted', () => {
    render(
      <TextInput
        value="བོད་ཡིག"
        onChange={mockOnChange}
        onSubmit={mockOnSubmit}
        loading={false}
      />
    )

    const form = screen.getByRole('button', { name: /check spelling/i }).closest('form')
    if (form) {
      fireEvent.submit(form)
    }

    expect(mockOnSubmit).toHaveBeenCalled()
  })

  it('disables input when loading', () => {
    render(
      <TextInput
        value="བོད་ཡིག"
        onChange={mockOnChange}
        onSubmit={mockOnSubmit}
        loading={true}
      />
    )

    const textarea = screen.getByLabelText('Tibetan text input')
    expect(textarea).toBeDisabled()
  })

  it('disables submit button when loading', () => {
    render(
      <TextInput
        value="བོད་ཡིག"
        onChange={mockOnChange}
        onSubmit={mockOnSubmit}
        loading={true}
      />
    )

    const submitButton = screen.getByRole('button', { name: /checking/i })
    expect(submitButton).toBeDisabled()
  })

  it('disables submit button when text is empty', () => {
    render(
      <TextInput
        value=""
        onChange={mockOnChange}
        onSubmit={mockOnSubmit}
        loading={false}
      />
    )

    const submitButton = screen.getByRole('button', { name: /check spelling/i })
    expect(submitButton).toBeDisabled()
  })

  it('disables submit button when text is only whitespace', () => {
    render(
      <TextInput
        value="   "
        onChange={mockOnChange}
        onSubmit={mockOnSubmit}
        loading={false}
      />
    )

    const submitButton = screen.getByRole('button', { name: /check spelling/i })
    expect(submitButton).toBeDisabled()
  })

  it('shows character count', () => {
    const text = 'བོད་ཡིག'
    render(
      <TextInput
        value={text}
        onChange={mockOnChange}
        onSubmit={mockOnSubmit}
        loading={false}
      />
    )

    expect(screen.getByText(`${text.length} characters`)).toBeInTheDocument()
  })

  it('shows clear button when text is present', () => {
    render(
      <TextInput
        value="བོད་ཡིག"
        onChange={mockOnChange}
        onSubmit={mockOnSubmit}
        loading={false}
      />
    )

    expect(screen.getByRole('button', { name: /clear/i })).toBeInTheDocument()
  })

  it('does not show clear button when text is empty', () => {
    render(
      <TextInput
        value=""
        onChange={mockOnChange}
        onSubmit={mockOnSubmit}
        loading={false}
      />
    )

    expect(screen.queryByRole('button', { name: /clear/i })).not.toBeInTheDocument()
  })

  it('calls onChange with empty string when clear button is clicked and no onClear provided', () => {
    render(
      <TextInput
        value="བོད་ཡིག"
        onChange={mockOnChange}
        onSubmit={mockOnSubmit}
        loading={false}
      />
    )

    const clearButton = screen.getByRole('button', { name: /clear/i })
    fireEvent.click(clearButton)

    expect(mockOnChange).toHaveBeenCalledWith('')
  })

  it('calls onClear when provided and clear button is clicked', () => {
    const mockOnClear = jest.fn()
    render(
      <TextInput
        value="བོད་ཡིག"
        onChange={mockOnChange}
        onSubmit={mockOnSubmit}
        onClear={mockOnClear}
        loading={false}
      />
    )

    const clearButton = screen.getByRole('button', { name: /clear/i })
    fireEvent.click(clearButton)

    expect(mockOnClear).toHaveBeenCalled()
    expect(mockOnChange).not.toHaveBeenCalled()
  })

  it('shows loading text when loading', () => {
    render(
      <TextInput
        value="བོད་ཡིག"
        onChange={mockOnChange}
        onSubmit={mockOnSubmit}
        loading={true}
      />
    )

    expect(screen.getByText(/checking/i)).toBeInTheDocument()
  })
})
