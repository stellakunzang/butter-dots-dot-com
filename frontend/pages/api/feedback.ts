import type { NextApiRequest, NextApiResponse } from 'next'

const GITHUB_TOKEN = process.env.GITHUB_FEEDBACK_TOKEN
const GITHUB_REPO = process.env.GITHUB_FEEDBACK_REPO || 'stellakunzang/butter-dots-dot-com'
const FORMSPREE_ENDPOINT = process.env.FORMSPREE_ENDPOINT

const MAX_DESCRIPTION_CHARS = 5000
const RATE_WINDOW_MS = 10 * 60 * 1000
const RATE_MAX = 5

const hitsByIp = new Map<string, number[]>()

interface FeedbackBody {
  type: 'bug' | 'feature'
  description: string
  email?: string
  company?: string
}

export const config = {
  api: {
    bodyParser: {
      sizeLimit: '32kb',
    },
  },
}

function isValidBody(body: unknown): body is FeedbackBody {
  if (typeof body !== 'object' || body === null) return false
  const b = body as Record<string, unknown>
  if (b.type !== 'bug' && b.type !== 'feature') return false
  if (typeof b.description !== 'string' || b.description.trim().length === 0) return false
  if (b.description.length > MAX_DESCRIPTION_CHARS) return false
  if (b.email !== undefined && typeof b.email !== 'string') return false
  if (b.company !== undefined && typeof b.company !== 'string') return false
  return true
}

function clientIp(req: NextApiRequest): string {
  const forwarded = req.headers['x-forwarded-for']
  if (typeof forwarded === 'string' && forwarded.length > 0) {
    return forwarded.split(',')[0].trim()
  }
  return req.socket.remoteAddress ?? 'unknown'
}

function isRateLimited(ip: string): boolean {
  const now = Date.now()
  const recent = (hitsByIp.get(ip) ?? []).filter((at) => now - at < RATE_WINDOW_MS)
  if (recent.length >= RATE_MAX) {
    hitsByIp.set(ip, recent)
    return true
  }
  recent.push(now)
  hitsByIp.set(ip, recent)
  return false
}

export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse
) {
  if (req.method !== 'POST') {
    res.setHeader('Allow', 'POST')
    return res.status(405).json({ error: 'Method not allowed' })
  }

  if (!GITHUB_TOKEN) {
    console.error('GITHUB_FEEDBACK_TOKEN is not configured')
    return res.status(500).json({ error: 'Feedback service is not configured' })
  }

  if (!isValidBody(req.body)) {
    return res.status(400).json({
      error: 'Invalid request. Provide type ("bug" | "feature") and a non-empty description.',
    })
  }

  if (isRateLimited(clientIp(req))) {
    return res.status(429).json({ error: 'Too many feedback submissions. Try again later.' })
  }

  const { type, description, email, company } = req.body

  // Honeypot: real clients leave this empty. Pretend success so bots get no signal.
  if (typeof company === 'string' && company.trim().length > 0) {
    return res.status(201).json({ url: null })
  }

  const label = type === 'bug' ? 'bug' : 'enhancement'
  const title = `[${type === 'bug' ? 'Bug' : 'Feature Request'}] ${description.slice(0, 80)}`

  const issueBody = `${description}\n\n<sub>Submitted via the site feedback form</sub>`

  const [owner, repo] = GITHUB_REPO.split('/')

  const ghPromise = fetch(
    `https://api.github.com/repos/${owner}/${repo}/issues`,
    {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${GITHUB_TOKEN}`,
        Accept: 'application/vnd.github+json',
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ title, body: issueBody, labels: [label] }),
    }
  )

  const formspreePromise =
    FORMSPREE_ENDPOINT && email
      ? fetch(FORMSPREE_ENDPOINT, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            type: type === 'bug' ? 'Bug Report' : 'Feature Request',
            description,
            email,
          }),
        }).catch((err) => console.error('Formspree error:', err))
      : Promise.resolve()

  const ghResponse = await ghPromise
  await formspreePromise

  if (!ghResponse.ok) {
    const detail = await ghResponse.text()
    console.error('GitHub API error:', ghResponse.status, detail)
    return res.status(502).json({ error: 'Failed to create issue' })
  }

  const issue = await ghResponse.json()
  return res.status(201).json({ url: issue.html_url })
}
