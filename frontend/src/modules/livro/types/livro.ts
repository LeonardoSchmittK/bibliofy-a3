export interface Livro {
  codigo: string
  isbn: string
  nome: string
  autor: string
  editora: string
  genero: string
  data_lancamento: string
  descricao?: string | null
  quantidade_total: number
  quantidade_disponivel: number
  quantidade_emprestada: number
  arquivado: boolean
}

export type LivroDados = Omit<
  Livro,
  'codigo' | 'quantidade_disponivel' | 'quantidade_emprestada' | 'arquivado'
>

export interface CategoriaResumo {
  genero: string
  quantidade: number
  percentual: number
}

export interface AcervoResumo {
  total_titulos: number
  total_exemplares: number
  disponiveis: number
  emprestados: number
  categorias: CategoriaResumo[]
}

export interface CatalogoLivros {
  livros: Livro[]
  resumo: AcervoResumo
}
