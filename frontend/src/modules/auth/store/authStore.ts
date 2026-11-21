import { create } from 'zustand'
import { ApiError, apiRequest } from '../../../shared/api/client'
import type { EstadoAutenticacao, UsuarioAutenticado } from '../types/auth'

interface RespostaToken {
  access_token: string
  token_type: string
}

interface AuthState {
  accessToken: string | null
  usuario: UsuarioAutenticado | null
  estado: EstadoAutenticacao
  carregandoLogin: boolean
  erro: string | null
  inicializarSessao: () => Promise<void>
  entrar: (email: string, senha: string) => Promise<boolean>
  sair: () => void
  limparErro: () => void
}

const CHAVE_TOKEN = 'access_token'
let inicializacaoPendente: Promise<void> | null = null

function obterTokenSalvo(): string | null {
  return typeof window === 'undefined' ? null : window.sessionStorage.getItem(CHAVE_TOKEN)
}

function limparTokenSalvo() {
  if (typeof window !== 'undefined') window.sessionStorage.removeItem(CHAVE_TOKEN)
}

function mensagemErro(error: unknown): string {
  if (error instanceof ApiError) {
    return error.message
  }
  if (error instanceof Error) return error.message
  return 'Não foi possível conectar ao servidor.'
}

export const useAuthStore = create<AuthState>((set, get) => ({
  accessToken: obterTokenSalvo(),
  usuario: null,
  estado: obterTokenSalvo() ? 'checking' : 'unauthenticated',
  carregandoLogin: false,
  erro: null,
  inicializarSessao: () => {
    if (inicializacaoPendente) return inicializacaoPendente

    const token = obterTokenSalvo()
    if (!token) {
      set({
        accessToken: null,
        usuario: null,
        estado: 'unauthenticated',
        erro: null,
      })
      return Promise.resolve()
    }

    const atual = get()
    if (
      atual.estado === 'authenticated' &&
      atual.accessToken === token &&
      atual.usuario
    ) {
      return Promise.resolve()
    }

    set({ accessToken: token, estado: 'checking', erro: null })
    inicializacaoPendente = (async () => {
      try {
        const usuario = await apiRequest<UsuarioAutenticado>('/auth/me', { token })
        set({ accessToken: token, usuario, estado: 'authenticated', erro: null })
      } catch (error) {
        if (error instanceof ApiError && error.status === 401) {
          limparTokenSalvo()
          set({
            accessToken: null,
            usuario: null,
            estado: 'unauthenticated',
            erro: null,
          })
        } else {
          set({
            accessToken: token,
            usuario: null,
            estado: 'error',
            erro: mensagemErro(error),
          })
        }
      } finally {
        inicializacaoPendente = null
      }
    })()
    return inicializacaoPendente
  },
  entrar: async (email, senha) => {
    set({ carregandoLogin: true, erro: null })
    try {
      const resposta = await apiRequest<RespostaToken>('/auth/login', {
        method: 'POST',
        body: new URLSearchParams({ username: email, password: senha }),
      })
      const usuario = await apiRequest<UsuarioAutenticado>('/auth/me', {
        token: resposta.access_token,
      })
      window.sessionStorage.setItem(CHAVE_TOKEN, resposta.access_token)
      set({
        accessToken: resposta.access_token,
        usuario,
        estado: 'authenticated',
        carregandoLogin: false,
        erro: null,
      })
      return true
    } catch (error) {
      set({ carregandoLogin: false, erro: mensagemErro(error) })
      return false
    }
  },
  sair: () => {
    limparTokenSalvo()
    set({
      accessToken: null,
      usuario: null,
      estado: 'unauthenticated',
      carregandoLogin: false,
      erro: null,
    })
  },
  limparErro: () => set({ erro: null }),
}))
