import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type { Livro, LivroDados } from '../types/livro'

interface LivroState {
  livros: Livro[]
  adicionarLivro: (dados: LivroDados) => void
  atualizarLivro: (codigo: string, dados: LivroDados) => void
  arquivarLivro: (codigo: string) => void
  emprestarExemplar: (codigo: string) => boolean
  devolverExemplar: (codigo: string) => boolean
}

const livrosExemplo: Livro[] = [
  {
    codigo: 'liv_00000001',
    isbn: '9788491050296',
    nome: 'Dom Quixote',
    autor: 'Miguel de Cervantes',
    editora: 'Penguin Companhia',
    genero: 'Ficção',
    data_lancamento: '1605-01-16',
    quantidade_total: 180,
    quantidade_disponivel: 166,
    quantidade_emprestada: 14,
    arquivado: false,
  },
  {
    codigo: 'liv_00000002',
    isbn: '9788522031443',
    nome: 'O Pequeno Príncipe',
    autor: 'Antoine de Saint-Exupéry',
    editora: 'Agir',
    genero: 'Infantil',
    data_lancamento: '1943-04-06',
    quantidade_total: 100,
    quantidade_disponivel: 89,
    quantidade_emprestada: 11,
    arquivado: false,
  },
  {
    codigo: 'liv_00000003',
    isbn: '9788501029467',
    nome: 'A Hora da Estrela',
    autor: 'Clarice Lispector',
    editora: 'Rocco',
    genero: 'Ficção',
    data_lancamento: '1977-10-26',
    quantidade_total: 70,
    quantidade_disponivel: 60,
    quantidade_emprestada: 10,
    arquivado: false,
  },
  {
    codigo: 'liv_00000004',
    isbn: '9786555320352',
    nome: 'O Alquimista',
    autor: 'Paulo Coelho',
    editora: 'Paralela',
    genero: 'Ficção',
    data_lancamento: '1988-01-01',
    quantidade_total: 40,
    quantidade_disponivel: 40,
    quantidade_emprestada: 0,
    arquivado: false,
  },
  {
    codigo: 'liv_00000005',
    isbn: '9788535910663',
    nome: 'Memórias Póstumas',
    autor: 'Machado de Assis',
    editora: 'Companhia das Letras',
    genero: 'Clássico',
    data_lancamento: '1881-01-01',
    quantidade_total: 35,
    quantidade_disponivel: 35,
    quantidade_emprestada: 0,
    arquivado: false,
  },
  {
    codigo: 'liv_00000006',
    isbn: '9788532522529',
    nome: 'O Código da Vinci',
    autor: 'Dan Brown',
    editora: 'Sextante',
    genero: 'Suspense',
    data_lancamento: '2003-03-18',
    quantidade_total: 32,
    quantidade_disponivel: 32,
    quantidade_emprestada: 0,
    arquivado: false,
  },
]

function criarLivro(dados: LivroDados, codigo: string): Livro {
  return {
    ...dados,
    codigo,
    quantidade_disponivel: Math.max(dados.quantidade_total, 0),
    quantidade_emprestada: 0,
    arquivado: false,
  }
}

export const useLivroStore = create<LivroState>()(
  persist(
    (set) => ({
      livros: livrosExemplo,
      adicionarLivro: (dados) =>
        set((state) => ({
          livros: [...state.livros, criarLivro(dados, `liv_${Date.now().toString(36)}`)],
        })),
      atualizarLivro: (codigo, dados) =>
        set((state) => ({
          livros: state.livros.map((livro) =>
            livro.codigo === codigo
              ? {
                  ...livro,
                  ...dados,
                  quantidade_disponivel: Math.max(
                    dados.quantidade_total - livro.quantidade_emprestada,
                    0,
                  ),
                }
              : livro,
          ),
        })),
      arquivarLivro: (codigo) =>
        set((state) => ({
          livros: state.livros.map((livro) =>
            livro.codigo === codigo ? { ...livro, arquivado: true } : livro,
          ),
        })),
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
    }),
    {
      name: 'bibliofy-livros',
      merge: (persistedState, currentState) => {
        const savedState = persistedState as Partial<LivroState> | undefined
        const savedBooks = Array.isArray(savedState?.livros) ? savedState.livros : []
        const savedCodes = new Set(savedBooks.map((livro) => livro.codigo))
        return {
          ...currentState,
          ...savedState,
          livros: [
            ...savedBooks,
            ...currentState.livros.filter((livro) => !savedCodes.has(livro.codigo)),
          ],
        }
      },
    },
  ),
)
