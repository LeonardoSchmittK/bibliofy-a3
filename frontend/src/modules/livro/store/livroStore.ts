import { create } from 'zustand'
import { ApiError, apiRequest } from '../../../shared/api/client'
import { useAuthStore } from '../../auth/store/authStore'
import type { Livro, LivroDados } from '../types/livro'

interface LivroApi {
  codigo: string
  isbn: string
  nome: string
  autor: string
  editora: string
  genero: string
  data_lancamento: string
  descricao: string | null
  quantidade_total: number
  quantidade_disponivel: number
  disponibilidade: 'DISPONIVEL' | 'EMPRESTADO' | 'INDISPONIVEL'
  arquivado: boolean
}

interface LivroState {
  livros: Livro[]
  carregando: boolean
  carregado: boolean
  erro: string | null
  limparErro: () => void
  carregarLivros: () => Promise<void>
  adicionarLivro: (dados: LivroDados) => Promise<boolean>
  atualizarLivro: (codigo: string, dados: LivroDados) => Promise<boolean>
  arquivarLivro: (codigo: string) => Promise<boolean>
  emprestarExemplar: (codigo: string) => boolean
  devolverExemplar: (codigo: string) => boolean
}

export function mapearLivroApi(livro: LivroApi): Livro {
  return {
    codigo: livro.codigo,
    isbn: livro.isbn,
    nome: livro.nome,
    autor: livro.autor,
    editora: livro.editora,
    genero: livro.genero,
    data_lancamento: livro.data_lancamento,
    descricao: livro.descricao,
    quantidade_total: livro.quantidade_total,
    quantidade_disponivel: livro.quantidade_disponivel,
    quantidade_emprestada: Math.max(
      livro.quantidade_total - livro.quantidade_disponivel,
      0,
    ),
    arquivado: livro.arquivado,
  }
}

function obterToken(): string {
  const token = useAuthStore.getState().accessToken
  if (!token) throw new ApiError('Sua sessão expirou. Entre novamente.', 401)
  return token
}

function mensagemErro(error: unknown): string {
  if (error instanceof ApiError) {
    if (error.status === 401) return 'Sua sessão expirou. Entre novamente.'
    if (error.message === 'ISBN_DUPLICADO') {
      return 'Já existe um livro cadastrado com esse ISBN.'
    }
    if (error.message === 'QUANTIDADE_INSUFICIENTE') {
      return 'A quantidade total não pode ser menor que os exemplares emprestados.'
    }
    if (error.message.toLocaleLowerCase('pt-BR').includes('isbn inválido')) {
      return 'ISBN inválido. Verifique o número e tente novamente.'
    }
    return error.message
  }
  if (error instanceof Error) return error.message
  return 'Não foi possível concluir a operação com os livros.'
}

function registrarErro(error: unknown, set: (partial: Partial<LivroState>) => void) {
  set({ erro: mensagemErro(error) })
  if (error instanceof ApiError && error.status === 401) {
    useAuthStore.getState().sair()
  }
}

export const useLivroStore = create<LivroState>((set) => ({
  livros: [],
  carregando: false,
  carregado: false,
  erro: null,
  limparErro: () => set({ erro: null }),
  carregarLivros: async () => {
    set({ carregando: true, erro: null })
    try {
      const resposta = await apiRequest<LivroApi[]>('/livros/', {
        token: obterToken(),
      })
      set({ livros: resposta.map(mapearLivroApi), carregado: true, erro: null })
    } catch (error) {
      registrarErro(error, set)
    } finally {
      set({ carregando: false })
    }
  },
  adicionarLivro: async (dados) => {
    set({ erro: null })
    try {
      const criado = await apiRequest<LivroApi>('/livros/', {
        method: 'POST',
        token: obterToken(),
        body: dados,
      })
      set((state) => ({
        livros: [...state.livros, mapearLivroApi(criado)],
        erro: null,
      }))
      return true
    } catch (error) {
      registrarErro(error, set)
      return false
    }
  },
  atualizarLivro: async (codigo, dados) => {
    set({ erro: null })
    try {
      const atualizado = await apiRequest<LivroApi>(
        `/livros/${encodeURIComponent(codigo)}`,
        {
          method: 'PATCH',
          token: obterToken(),
          body: dados,
        },
      )
      set((state) => ({
        livros: state.livros.map((livro) =>
          livro.codigo === codigo ? mapearLivroApi(atualizado) : livro,
        ),
        erro: null,
      }))
      return true
    } catch (error) {
      registrarErro(error, set)
      return false
    }
  },
  arquivarLivro: async (codigo) => {
    set({ erro: null })
    try {
      const arquivado = await apiRequest<LivroApi>(
        `/livros/${encodeURIComponent(codigo)}/arquivar`,
        {
          method: 'POST',
          token: obterToken(),
        },
      )
      set((state) => ({
        livros: state.livros.map((livro) =>
          livro.codigo === codigo ? mapearLivroApi(arquivado) : livro,
        ),
        erro: null,
      }))
      return true
    } catch (error) {
      registrarErro(error, set)
      return false
    }
  },
  emprestarExemplar: (codigo) => {
    let emprestado = false
    set((state) => ({
      livros: state.livros.map((livro) => {
        if (
          livro.codigo !== codigo ||
          livro.arquivado ||
          livro.quantidade_disponivel <= 0
        ) {
          return livro
        }
        emprestado = true
        return {
          ...livro,
          quantidade_disponivel: livro.quantidade_disponivel - 1,
          quantidade_emprestada: livro.quantidade_emprestada + 1,
        }
      }),
    }))
    return emprestado
  },
  devolverExemplar: (codigo) => {
    let devolvido = false
    set((state) => ({
      livros: state.livros.map((livro) => {
        if (livro.codigo !== codigo) return livro

        devolvido = true
        return {
          ...livro,
          quantidade_disponivel: Math.min(
            livro.quantidade_disponivel + 1,
            livro.quantidade_total,
          ),
          quantidade_emprestada: Math.max(livro.quantidade_emprestada - 1, 0),
        }
      }),
    }))
    return devolvido
  },
}))
