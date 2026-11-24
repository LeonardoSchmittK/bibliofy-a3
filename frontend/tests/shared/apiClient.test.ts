import { afterEach, describe, expect, it, vi } from 'vitest'
import { ApiError, apiRequest } from '../../src/shared/api/client'

function resposta(body: unknown, status = 200, text?: string): Response {
  return {
    ok: status >= 200 && status < 300,
    status,
    text: async () => text ?? (body === undefined ? '' : JSON.stringify(body)),
  } as Response
}

describe('Cliente HTTP da API', () => {
  afterEach(() => vi.unstubAllGlobals())

  it('envia JSON e retorna o payload', async () => {
    const fetchMock = vi.fn(async () => resposta({ codigo: 'liv_1' }))
    vi.stubGlobal('fetch', fetchMock)

    await expect(apiRequest('/livros', {
      method: 'POST',
      token: 'token',
      body: { nome: 'Livro' },
    })).resolves.toEqual({ codigo: 'liv_1' })

    expect(fetchMock).toHaveBeenCalledWith(
      expect.stringContaining('/livros'),
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify({ nome: 'Livro' }),
      }),
    )
  })

  it('converte erros 422 em ApiError com a mensagem da API', async () => {
    vi.stubGlobal('fetch', vi.fn(async () => resposta(
      { detail: [{ msg: 'ISBN inválido' }, { msg: 'Nome obrigatório' }] },
      422,
    )))

    await expect(apiRequest('/livros')).rejects.toMatchObject({
      status: 422,
      message: 'ISBN inválido Nome obrigatório',
    } satisfies Partial<ApiError>)
  })

  it('trata resposta vazia, texto inválido e status 204', async () => {
    vi.stubGlobal('fetch', vi.fn(async () => resposta(undefined, 200, '')))
    await expect(apiRequest('/vazio')).rejects.toBeInstanceOf(ApiError)

    vi.stubGlobal('fetch', vi.fn(async () => resposta(undefined, 200, 'não-json')))
    await expect(apiRequest('/texto')).rejects.toMatchObject({ message: 'A API retornou uma resposta inválida.' })

    vi.stubGlobal('fetch', vi.fn(async () => resposta(undefined, 204)))
    await expect(apiRequest('/sem-conteudo')).resolves.toBeUndefined()
  })
})
