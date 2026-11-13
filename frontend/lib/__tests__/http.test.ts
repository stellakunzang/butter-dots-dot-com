import {APIError, request} from '@/lib/http'
import {reportApiFailure} from '@/lib/monitoring'

jest.mock('@/lib/monitoring', () => ({reportApiFailure: jest.fn()}))

const reported = reportApiFailure as jest.MockedFunction<typeof reportApiFailure>

function respond(status: number, body: unknown) {
  global.fetch = jest.fn().mockResolvedValue({
    ok: status < 400,
    status,
    json: async () => body,
  }) as unknown as typeof fetch
}

describe('request', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    jest.useRealTimers()
  })

  it('returns the JSON body and reports nothing on success', async () => {
    respond(200, {ok: true})
    await expect(request('/api/v1/health')).resolves.toEqual({ok: true})
    expect(reported).not.toHaveBeenCalled()
  })

  it('abandons a request that outlives its timeout and reports it', async () => {
    jest.useFakeTimers()
    global.fetch = jest.fn(
      (_url: RequestInfo | URL, init?: RequestInit) =>
        new Promise((_resolve, reject) => {
          init?.signal?.addEventListener('abort', () =>
            reject(new DOMException('aborted', 'AbortError'))
          )
        })
    ) as unknown as typeof fetch

    const pending = request('/api/v1/spellcheck/upload', undefined, undefined, 1_000)
    jest.advanceTimersByTime(1_000)

    await expect(pending).rejects.toMatchObject({status: 0, message: expect.stringMatching(/did not respond in time/)})
    expect(reported).toHaveBeenCalledWith('/api/v1/spellcheck/upload', 'timeout', expect.any(APIError))
  })

  it('reports a network failure', async () => {
    global.fetch = jest.fn().mockRejectedValue(new TypeError('Failed to fetch')) as unknown as typeof fetch
    await expect(request('/api/v1/spellcheck/text')).rejects.toMatchObject({status: 0})
    expect(reported).toHaveBeenCalledWith('/api/v1/spellcheck/text', 'network', expect.any(APIError))
  })

  it('reports a 5xx with its status', async () => {
    respond(502, null)
    await expect(request('/api/v1/spellcheck/upload')).rejects.toMatchObject({status: 502})
    expect(reported).toHaveBeenCalledWith('/api/v1/spellcheck/upload', 'server', expect.any(APIError), 502)
  })

  it('does not report a 4xx, which is the user’s input, not an outage', async () => {
    respond(400, {detail: 'Text cannot be empty'})
    await expect(request('/api/v1/spellcheck/text')).rejects.toMatchObject({status: 400, message: 'Text cannot be empty'})
    expect(reported).not.toHaveBeenCalled()
  })
})
