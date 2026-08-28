import type { NextApiRequest, NextApiResponse } from 'next'

const FORMSPREE_ENDPOINT = process.env.FORMSPREE_ENDPOINT

interface WaitlistBody {
  email: string
  name?: string
  note?: string
}

function isValidBody(body: unknown): body is WaitlistBody {
  if (typeof body !== 'object' || body === null) return false
  const b = body as Record<string, unknown>
  if (typeof b.email !== 'string' || !b.email.trim().includes('@')) return false
  if (b.name !== undefined && typeof b.name !== 'string') return false
  if (b.note !== undefined && typeof b.note !== 'string') return false
  return true
}

export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse
) {
  if (req.method !== 'POST') {
    res.setHeader('Allow', 'POST')
    return res.status(405).json({ error: 'Method not allowed' })
  }

  if (!FORMSPREE_ENDPOINT) {
    console.error('FORMSPREE_ENDPOINT is not configured')
    return res.status(500).json({ error: 'Waitlist is not configured' })
  }

  if (!isValidBody(req.body)) {
    return res.status(400).json({
      error: 'Please provide a valid email address.',
    })
  }

  const email = req.body.email.trim()
  const name = req.body.name?.trim() || undefined
  const note = req.body.note?.trim() || undefined

  try {
    const response = await fetch(FORMSPREE_ENDPOINT, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        type: 'OCR Waitlist',
        source: 'ocr-waitlist',
        email,
        ...(name && { name }),
        ...(note && { note }),
      }),
    })

    if (!response.ok) {
      const detail = await response.text()
      console.error('Formspree error:', response.status, detail)
      return res.status(502).json({ error: 'Failed to join waitlist' })
    }

    return res.status(201).json({ ok: true })
  } catch (err) {
    console.error('Formspree request failed:', err)
    return res.status(502).json({ error: 'Failed to join waitlist' })
  }
}
