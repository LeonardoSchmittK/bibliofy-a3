const configuredApiUrl = import.meta.env.VITE_API_URL
let normalizedApiUrl = configuredApiUrl ?? ''
while (normalizedApiUrl.endsWith('/')) {
  normalizedApiUrl = normalizedApiUrl.slice(0, -1)
}
const API_BASE_URL = normalizedApiUrl || 'http://localhost:8000'

export class ApiError extends Error {
  readonly status: number

  constructor(
    message: string,
    status: number,
  ) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}

function extrairMensagemErro(payload: unknown): string | null {
  if (!payload || typeof payload !== 'object' || !('detail' in payload)) return null

  const { detail } = payload
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail)) {
    const mensagens = detail.flatMap((item) => {
      if (item && typeof item === 'object' && 'msg' in item && typeof item.msg === 'string') {
        return [item.msg]
      }
      return []
    })
    return mensagens.length > 0 ? mensagens.join(' ') : null
  }

  return null
}

export async function apiRequest<T>(
  path: string,
  options: {
    method?: string
    token?: string
    body?: unknown
    headers?: HeadersInit
  } = {},
): Promise<T> {
  const headers = new Headers(options.headers)
  headers.set('Accept', 'application/json')
  if (options.token) headers.set('Authorization', `Bearer ${options.token}`)

  let body: BodyInit | undefined
  if (options.body instanceof URLSearchParams) {
    body = options.body
  } else if (options.body !== undefined) {
    headers.set('Content-Type', 'application/json')
    body = JSON.stringify(options.body)
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: options.method ?? 'GET',
    headers,
    body,
  })

  if (response.status === 204) return undefined as T

  const responseText = await response.text()
  let payload: unknown
  if (responseText) {
    try {
      payload = JSON.parse(responseText)
    } catch {
      if (response.ok) {
        throw new ApiError('A API retornou uma resposta inválida.', response.status)
      }
    }
  } else if (response.ok) {
    throw new ApiError('A API retornou uma resposta vazia.', response.status)
  }

  if (!response.ok) {
    const message = extrairMensagemErro(payload)
      ?? `A solicitação falhou (${response.status}).`
    throw new ApiError(message, response.status)
  }

  return payload as T
}
