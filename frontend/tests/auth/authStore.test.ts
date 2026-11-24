import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { useAuthStore } from '../../src/modules/auth/store/authStore'

function resposta(body: unknown, status = 200): Response {
  return {
    ok: status >= 200 && status < 300,
    status,
    text: async () => JSON.stringify(body),
  } as Response
}

const usuario = {
  codigo: 'usr_1',
  matricula: '2026001',
  nome: 'Ana Souza',
  email: 'ana@bibliofy.com',
  telefone: null,
  papel: 'BIBLIOTECARIO' as const,
  ativo: true,
}

describe('Armazenamento de autenticação', () => {
  beforeEach(() => {
    window.sessionStorage.clear()
    useAuthStore.setState({
      accessToken: null,
      usuario: null,
      estado: 'unauthenticated',
      carregandoLogin: false,
      erro: null,
    })
  })

  afterEach(() => {
    vi.unstubAllGlobals()
    window.sessionStorage.clear()
  })

  it('entra pela API, valida o usuário e persiste o token', async () => {
    vi.stubGlobal('fetch', vi.fn(async (input: RequestInfo | URL) => {
      if (String(input).endsWith('/auth/login')) {
        return resposta({ access_token: 'token-1', token_type: 'bearer' })
      }
      return resposta(usuario)
    }))

    expect(await useAuthStore.getState().entrar('ana@bibliofy.com', 'senha')).toBe(true)
    expect(useAuthStore.getState()).toMatchObject({
      accessToken: 'token-1',
      usuario,
      estado: 'authenticated',
      carregandoLogin: false,
    })
    expect(window.sessionStorage.getItem('access_token')).toBe('token-1')
  })

  it('mantém o erro da API sem autenticar', async () => {
    vi.stubGlobal('fetch', vi.fn(async () => resposta({ detail: 'Credenciais inválidas' }, 401)))

    expect(await useAuthStore.getState().entrar('ana@bibliofy.com', 'errada')).toBe(false)
    expect(useAuthStore.getState().erro).toBe('Credenciais inválidas')
    expect(useAuthStore.getState().estado).toBe('unauthenticated')
  })

  it('limpa sessão e erro ao sair', () => {
    window.sessionStorage.setItem('access_token', 'token-1')
    useAuthStore.setState({ accessToken: 'token-1', usuario, erro: 'erro', estado: 'authenticated' })

    useAuthStore.getState().sair()
    useAuthStore.getState().limparErro()

    expect(useAuthStore.getState()).toMatchObject({
      accessToken: null,
      usuario: null,
      estado: 'unauthenticated',
      erro: null,
    })
    expect(window.sessionStorage.getItem('access_token')).toBeNull()
  })
})
