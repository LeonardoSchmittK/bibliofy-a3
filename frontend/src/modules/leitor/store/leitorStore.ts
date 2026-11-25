import { create } from 'zustand'
import { ApiError, apiRequest } from '../../../shared/api/client'
import { useAuthStore } from '../../auth/store/authStore'
import type { Leitor } from '../types/leitor'

interface LeitorApi {
  codigo: string
  nome: string
  ativo: boolean
}

interface LeitorState {
  leitores: Leitor[]
  carregando: boolean
  carregado: boolean
  carregadoPara: string | null
  erro: string | null
  carregarLeitores: () => Promise<void>
}

function obterToken(): string {
  const token = useAuthStore.getState().accessToken
  if (!token) throw new ApiError('Sua sessão expirou. Entre novamente.', 401)
  return token
}

export const useLeitorStore = create<LeitorState>((set) => ({
  leitores: [],
  carregando: false,
  carregado: false,
  carregadoPara: null,
  erro: null,
  carregarLeitores: async () => {
    set({ carregando: true, erro: null })
    try {
      const resposta = await apiRequest<LeitorApi[]>('/usuarios?papel=LEITOR', {
        token: obterToken(),
      })
      set({
        leitores: resposta
          .filter((leitor) => leitor.ativo)
          .map(({ codigo, nome }) => ({ codigo, nome })),
        carregado: true,
        carregadoPara: useAuthStore.getState().usuario?.codigo ?? null,
        erro: null,
      })
    } catch (error) {
      const mensagem =
        error instanceof Error ? error.message : 'Não foi possível carregar os leitores.'
      set({ erro: mensagem })
      if (error instanceof ApiError && error.status === 401) {
        useAuthStore.getState().sair()
      }
    } finally {
      set({ carregando: false })
    }
  },
}))
