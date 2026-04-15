import { test, expect, Page } from '@playwright/test'

// ---------------------------------------------------------------------------
// Test fixtures
// ---------------------------------------------------------------------------

// Minimal PDF buffer — the frontend only checks the .pdf extension, not file
// contents, so this is sufficient to pass the file selection guard.
const FAKE_PDF = Buffer.from('%PDF-1.4 1 0 obj << >> endobj\n%%EOF')

// ---------------------------------------------------------------------------
// Mock API responses
// ---------------------------------------------------------------------------

const SYNC_RESPONSE = {
  job_id: 'sync-job-123',
  page_count: 5,
  error_count: 3,
  errors: [
    { word: 'བཀྲ', page: 1, error_type: 'invalid_prefix', severity: 'error' },
    { word: 'ཤིས', page: 2, error_type: 'invalid_suffix', severity: 'error' },
    { word: 'པོ', page: 3, error_type: 'invalid_vowel', severity: 'warning' },
  ],
  is_scanned: false,
  pdf_url: '/api/v1/spellcheck/result/sync-job-123/pdf',
  docx_url: '/api/v1/spellcheck/result/sync-job-123/docx',
}

const SYNC_NO_ERRORS_RESPONSE = {
  ...SYNC_RESPONSE,
  job_id: 'sync-clean-456',
  error_count: 0,
  errors: [],
}

const SYNC_SCANNED_RESPONSE = {
  ...SYNC_RESPONSE,
  job_id: 'sync-scanned-789',
  is_scanned: true,
}

// An async response is returned by the backend when the PDF has >15 pages.
// It lacks the `errors` field, which is how isSyncResponse() distinguishes it.
const ASYNC_RESPONSE = {
  job_id: 'async-job-456',
  page_count: 20,
  status: 'pending',
  message: 'Job queued for background processing',
}

const JOB_PENDING = {
  job_id: 'async-job-456',
  status: 'pending',
  progress: 0,
  page_count: 20,
}

const JOB_PROCESSING = {
  job_id: 'async-job-456',
  status: 'processing',
  progress: 50,
  page_count: 20,
}

const JOB_COMPLETED = {
  job_id: 'async-job-456',
  status: 'completed',
  progress: 100,
  page_count: 20,
  error_count: 7,
}

const JOB_COMPLETED_CLEAN = {
  ...JOB_COMPLETED,
  error_count: 0,
}

const JOB_FAILED = {
  job_id: 'async-job-456',
  status: 'failed',
  progress: 25,
  page_count: 20,
  error_message: 'OCR engine encountered an unsupported file format',
}

// ---------------------------------------------------------------------------
// Route-mocking helpers
// ---------------------------------------------------------------------------

async function mockUploadSync(page: Page, response = SYNC_RESPONSE) {
  await page.route('**/api/v1/spellcheck/upload', route =>
    route.fulfill({ json: response })
  )
}

async function mockUploadAsync(page: Page) {
  await page.route('**/api/v1/spellcheck/upload', route =>
    route.fulfill({ json: ASYNC_RESPONSE })
  )
}

async function mockUploadError(page: Page, status: number, detail: string) {
  await page.route('**/api/v1/spellcheck/upload', route =>
    route.fulfill({ status, json: { detail } })
  )
}

async function mockUploadNetworkError(page: Page) {
  await page.route('**/api/v1/spellcheck/upload', route => route.abort('failed'))
}

// Cycles through `responses` in order; repeats the last entry indefinitely.
async function mockJobStatus(page: Page, responses: object[]) {
  let callCount = 0
  await page.route('**/api/v1/spellcheck/job/**', route => {
    const resp = responses[Math.min(callCount, responses.length - 1)]
    callCount++
    route.fulfill({ json: resp })
  })
}

// ---------------------------------------------------------------------------
// Navigation / interaction helpers
// ---------------------------------------------------------------------------

async function goToPDFTab(page: Page) {
  await page.goto('/spellcheck')
  await page.getByRole('button', { name: 'Upload PDF' }).click()
  await expect(page.getByText('Drop a PDF here or')).toBeVisible()
}

async function uploadFile(page: Page, filename = 'test.pdf') {
  const fileInput = page.locator('input[type="file"][accept=".pdf"]')
  await fileInput.setInputFiles({
    name: filename,
    mimeType: 'application/pdf',
    buffer: FAKE_PDF,
  })
}

// Drives the flow up to the job-status polling phase (email submitted).
async function goToJobStatus(page: Page) {
  await mockUploadAsync(page)
  await mockJobStatus(page, [JOB_PENDING, JOB_PROCESSING, JOB_COMPLETED])
  await goToPDFTab(page)
  await uploadFile(page)
  await page.getByRole('button', { name: 'Check spelling' }).click()
  await expect(page.getByText('Large document detected')).toBeVisible()
  await page.getByLabel('Email address').fill('test@example.com')
  await page.getByRole('button', { name: 'Queue for processing' }).click()
}

// ===========================================================================
// Test suites
// ===========================================================================

test.describe('Tab navigation', () => {
  test('text tab is active by default', async ({ page }) => {
    await page.goto('/spellcheck')
    await expect(page.getByText('Input Text')).toBeVisible()
    await expect(page.locator('input[type="file"]')).not.toBeVisible()
  })

  test('clicking "Upload PDF" tab shows the dropzone', async ({ page }) => {
    await page.goto('/spellcheck')
    await page.getByRole('button', { name: 'Upload PDF' }).click()
    await expect(page.getByText('Drop a PDF here or')).toBeVisible()
    await expect(page.getByText('Input Text')).not.toBeVisible()
  })

  test('switching back to "Check text" tab hides the dropzone', async ({ page }) => {
    await page.goto('/spellcheck')
    await page.getByRole('button', { name: 'Upload PDF' }).click()
    await page.getByRole('button', { name: 'Check text' }).click()
    await expect(page.getByText('Input Text')).toBeVisible()
    await expect(page.getByText('Drop a PDF here or')).not.toBeVisible()
  })
})

test.describe('File selection', () => {
  test('selecting a PDF shows the filename and a "Check spelling" button', async ({ page }) => {
    await goToPDFTab(page)
    await uploadFile(page, 'tibetan-sutra.pdf')

    await expect(page.getByText('tibetan-sutra.pdf')).toBeVisible()
    await expect(page.getByRole('button', { name: 'Check spelling' })).toBeVisible()
  })

  test('file size is shown after selecting', async ({ page }) => {
    await goToPDFTab(page)
    await uploadFile(page)
    await expect(page.getByText(/MB — click to change/)).toBeVisible()
  })

  test('non-PDF files are silently rejected', async ({ page }) => {
    await goToPDFTab(page)
    const fileInput = page.locator('input[type="file"]')
    await fileInput.setInputFiles({
      name: 'notes.docx',
      mimeType: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
      buffer: Buffer.from('fake docx'),
    })

    // No filename shown, no "Check spelling" button, dropzone prompt still visible
    await expect(page.getByRole('button', { name: 'Check spelling' })).not.toBeVisible()
    await expect(page.getByText('notes.docx')).not.toBeVisible()
    await expect(page.getByText('Drop a PDF here or')).toBeVisible()
  })
})

test.describe('Sync processing (≤15 pages)', () => {
  test('shows a spinner with "Processing…" while the request is in flight', async ({ page }) => {
    await page.route('**/api/v1/spellcheck/upload', async route => {
      await new Promise(resolve => setTimeout(resolve, 400))
      await route.fulfill({ json: SYNC_RESPONSE })
    })
    await goToPDFTab(page)
    await uploadFile(page)
    await page.getByRole('button', { name: 'Check spelling' }).click()

    await expect(page.getByText('Processing…')).toBeVisible()
  })

  test('shows error count and download links on completion', async ({ page }) => {
    await mockUploadSync(page)
    await goToPDFTab(page)
    await uploadFile(page)
    await page.getByRole('button', { name: 'Check spelling' }).click()

    await expect(page.getByText(/3 spelling errors? found across 5 pages?/)).toBeVisible()
    await expect(page.getByRole('link', { name: 'Annotated PDF' })).toBeVisible()
    await expect(page.getByRole('link', { name: 'Editable Word doc' })).toBeVisible()
  })

  test('download links have correct href and download attribute', async ({ page }) => {
    await mockUploadSync(page)
    await goToPDFTab(page)
    await uploadFile(page)
    await page.getByRole('button', { name: 'Check spelling' }).click()

    const pdfLink = page.getByRole('link', { name: 'Annotated PDF' })
    await expect(pdfLink).toHaveAttribute('href', /result\/sync-job-123\/pdf/)
    await expect(pdfLink).toHaveAttribute('download')

    const docxLink = page.getByRole('link', { name: 'Editable Word doc' })
    await expect(docxLink).toHaveAttribute('href', /result\/sync-job-123\/docx/)
    await expect(docxLink).toHaveAttribute('download')
  })

  test('shows green "No spelling errors found" when the PDF is clean', async ({ page }) => {
    await mockUploadSync(page, SYNC_NO_ERRORS_RESPONSE)
    await goToPDFTab(page)
    await uploadFile(page)
    await page.getByRole('button', { name: 'Check spelling' }).click()

    await expect(page.getByText('No spelling errors found.')).toBeVisible()
    // Download links should not appear when there are no errors
    await expect(page.getByRole('link', { name: 'Annotated PDF' })).not.toBeVisible()
    await expect(page.getByRole('link', { name: 'Editable Word doc' })).not.toBeVisible()
  })

  test('shows scanned-document disclaimer for OCR-processed PDFs', async ({ page }) => {
    await mockUploadSync(page, SYNC_SCANNED_RESPONSE)
    await goToPDFTab(page)
    await uploadFile(page)
    await page.getByRole('button', { name: 'Check spelling' }).click()

    await expect(
      page.getByText('Scanned document — results may vary based on image quality.')
    ).toBeVisible()
  })

  test('"Upload another PDF" resets back to the idle dropzone', async ({ page }) => {
    await mockUploadSync(page)
    await goToPDFTab(page)
    await uploadFile(page)
    await page.getByRole('button', { name: 'Check spelling' }).click()
    await expect(page.getByText(/spelling errors? found/)).toBeVisible()

    await page.getByRole('button', { name: 'Upload another PDF' }).click()

    await expect(page.getByText('Drop a PDF here or')).toBeVisible()
    await expect(page.getByText(/spelling errors? found/)).not.toBeVisible()
  })
})

test.describe('Email capture (>15 pages)', () => {
  test('shows the email capture form for large PDFs', async ({ page }) => {
    await mockUploadAsync(page)
    await goToPDFTab(page)
    await uploadFile(page)
    await page.getByRole('button', { name: 'Check spelling' }).click()

    await expect(page.getByText('Large document detected')).toBeVisible()
    await expect(page.getByText(/Your PDF has 20 pages/)).toBeVisible()
    await expect(page.getByLabel('Email address')).toBeVisible()
    await expect(page.getByRole('button', { name: 'Queue for processing' })).toBeVisible()
  })

  test('shows validation error for an address without @', async ({ page }) => {
    await mockUploadAsync(page)
    await goToPDFTab(page)
    await uploadFile(page)
    await page.getByRole('button', { name: 'Check spelling' }).click()
    await expect(page.getByText('Large document detected')).toBeVisible()

    await page.getByLabel('Email address').fill('notanemail')
    await page.getByRole('button', { name: 'Queue for processing' }).click()

    await expect(page.getByText('Please enter a valid email address.')).toBeVisible()
  })

  test('validation error clears when the user edits the email field', async ({ page }) => {
    await mockUploadAsync(page)
    await goToPDFTab(page)
    await uploadFile(page)
    await page.getByRole('button', { name: 'Check spelling' }).click()
    await page.getByRole('button', { name: 'Queue for processing' }).click()
    await expect(page.getByText('Please enter a valid email address.')).toBeVisible()

    await page.getByLabel('Email address').fill('a')

    await expect(page.getByText('Please enter a valid email address.')).not.toBeVisible()
  })

  test('"Cancel" returns to the idle upload dropzone', async ({ page }) => {
    await mockUploadAsync(page)
    await goToPDFTab(page)
    await uploadFile(page)
    await page.getByRole('button', { name: 'Check spelling' }).click()
    await expect(page.getByText('Large document detected')).toBeVisible()

    await page.getByRole('button', { name: 'Cancel' }).click()

    await expect(page.getByText('Drop a PDF here or')).toBeVisible()
    await expect(page.getByText('Large document detected')).not.toBeVisible()
  })
})

test.describe('Async job status polling', () => {
  test('shows progress bar and email confirmation after email submission', async ({ page }) => {
    await goToJobStatus(page)

    await expect(page.getByText(/Results will be sent to/)).toBeVisible()
    await expect(page.getByText('test@example.com')).toBeVisible()
    await expect(page.getByText('Queued')).toBeVisible()
  })

  test('shows "Queued" label when job is pending', async ({ page }) => {
    await mockUploadAsync(page)
    await mockJobStatus(page, [JOB_PENDING])
    await goToPDFTab(page)
    await uploadFile(page)
    await page.getByRole('button', { name: 'Check spelling' }).click()
    await page.getByLabel('Email address').fill('test@example.com')
    await page.getByRole('button', { name: 'Queue for processing' }).click()

    await expect(page.getByText('Queued')).toBeVisible()
  })

  test('shows processing percentage when job is running', async ({ page }) => {
    await mockUploadAsync(page)
    await mockJobStatus(page, [JOB_PROCESSING])
    await goToPDFTab(page)
    await uploadFile(page)
    await page.getByRole('button', { name: 'Check spelling' }).click()
    await page.getByLabel('Email address').fill('test@example.com')
    await page.getByRole('button', { name: 'Queue for processing' }).click()

    await expect(page.getByText('Processing… 50%')).toBeVisible()
    await expect(page.getByText('50%')).toBeVisible()
  })

  test('transitions to "Processing complete" with download links when job completes', async ({ page }) => {
    await mockUploadAsync(page)
    await mockJobStatus(page, [JOB_COMPLETED])
    await goToPDFTab(page)
    await uploadFile(page)
    await page.getByRole('button', { name: 'Check spelling' }).click()
    await page.getByLabel('Email address').fill('test@example.com')
    await page.getByRole('button', { name: 'Queue for processing' }).click()

    await expect(page.getByText('Processing complete')).toBeVisible({ timeout: 10_000 })
    await expect(page.getByText(/7 spelling errors? found/)).toBeVisible()
    await expect(page.getByRole('link', { name: 'Annotated PDF' })).toBeVisible()
    await expect(page.getByRole('link', { name: 'Editable Word doc' })).toBeVisible()
  })

  test('"Upload another PDF" resets after async completion', async ({ page }) => {
    await mockUploadAsync(page)
    await mockJobStatus(page, [JOB_COMPLETED])
    await goToPDFTab(page)
    await uploadFile(page)
    await page.getByRole('button', { name: 'Check spelling' }).click()
    await page.getByLabel('Email address').fill('test@example.com')
    await page.getByRole('button', { name: 'Queue for processing' }).click()
    await expect(page.getByText('Processing complete')).toBeVisible({ timeout: 10_000 })

    await page.getByRole('button', { name: 'Upload another PDF' }).click()

    await expect(page.getByText('Drop a PDF here or')).toBeVisible()
    await expect(page.getByText('Processing complete')).not.toBeVisible()
  })

  test('shows "No spelling errors found" and hides download links when async job is clean', async ({ page }) => {
    await mockUploadAsync(page)
    await mockJobStatus(page, [JOB_COMPLETED_CLEAN])
    await goToPDFTab(page)
    await uploadFile(page)
    await page.getByRole('button', { name: 'Check spelling' }).click()
    await page.getByLabel('Email address').fill('test@example.com')
    await page.getByRole('button', { name: 'Queue for processing' }).click()

    await expect(page.getByText('Processing complete')).toBeVisible({ timeout: 10_000 })
    await expect(page.getByText('No spelling errors found.')).toBeVisible()
    await expect(page.getByRole('link', { name: 'Annotated PDF' })).not.toBeVisible()
    await expect(page.getByRole('link', { name: 'Editable Word doc' })).not.toBeVisible()
  })

  test('shows "Processing failed" with the error message when the job fails', async ({ page }) => {
    await mockUploadAsync(page)
    await mockJobStatus(page, [JOB_FAILED])
    await goToPDFTab(page)
    await uploadFile(page)
    await page.getByRole('button', { name: 'Check spelling' }).click()
    await page.getByLabel('Email address').fill('test@example.com')
    await page.getByRole('button', { name: 'Queue for processing' }).click()

    await expect(page.getByText('Processing failed')).toBeVisible({ timeout: 10_000 })
    await expect(
      page.getByText('OCR engine encountered an unsupported file format')
    ).toBeVisible()
  })

  test('shows a polling error if the status endpoint is unreachable', async ({ page }) => {
    await mockUploadAsync(page)
    await page.route('**/api/v1/spellcheck/job/**', route => route.abort('failed'))
    await goToPDFTab(page)
    await uploadFile(page)
    await page.getByRole('button', { name: 'Check spelling' }).click()
    await page.getByLabel('Email address').fill('test@example.com')
    await page.getByRole('button', { name: 'Queue for processing' }).click()

    await expect(page.getByText('Polling error:')).toBeVisible({ timeout: 10_000 })
  })
})

test.describe('Error handling', () => {
  test('shows the server error message on a 500 response', async ({ page }) => {
    await mockUploadError(page, 500, 'Internal server error')
    await goToPDFTab(page)
    await uploadFile(page)
    await page.getByRole('button', { name: 'Check spelling' }).click()

    await expect(page.getByText('Internal server error')).toBeVisible()
  })

  test('shows the error message on a 413 (file too large) response', async ({ page }) => {
    await mockUploadError(page, 413, 'File too large. Maximum size is 50 MB.')
    await goToPDFTab(page)
    await uploadFile(page)
    await page.getByRole('button', { name: 'Check spelling' }).click()

    await expect(page.getByText('File too large. Maximum size is 50 MB.')).toBeVisible()
  })

  test('shows a connection error when the backend is unreachable', async ({ page }) => {
    await mockUploadNetworkError(page)
    await goToPDFTab(page)
    await uploadFile(page)
    await page.getByRole('button', { name: 'Check spelling' }).click()

    await expect(page.getByText(/Unable to connect|Upload failed/)).toBeVisible()
  })

  test('"Try again" resets to the upload dropzone after an error', async ({ page }) => {
    await mockUploadError(page, 500, 'Internal server error')
    await goToPDFTab(page)
    await uploadFile(page)
    await page.getByRole('button', { name: 'Check spelling' }).click()
    await expect(page.getByText('Internal server error')).toBeVisible()

    await page.getByRole('button', { name: 'Try again' }).click()

    await expect(page.getByText('Drop a PDF here or')).toBeVisible()
    await expect(page.getByText('Internal server error')).not.toBeVisible()
  })
})
