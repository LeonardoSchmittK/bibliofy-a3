import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type { Livro, LivroDados } from '../types/livro'

interface LivroState {
  livros: Livro[]
  adicionarLivro: (dados: LivroDados) => void
  atualizarLivro: (codigo: string, dados: LivroDados) => void
  arquivarLivro: (codigo: string) => void
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
    }),
    { name: 'bibliofy-livros' },
  ),
)
