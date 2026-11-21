import { beforeEach, describe, expect, it } from 'vitest'
import { useLivroStore } from '../../src/modules/livro/store/livroStore'
import type { LivroDados } from '../../src/modules/livro/types/livro'

const dadosLivro: LivroDados = {
  nome: 'Dom Casmurro',
  autor: 'Machado de Assis',
  isbn: '9788535910663',
  editora: 'Companhia das Letras',
  genero: 'Ficção',
  data_lancamento: '1899-01-01',
  quantidade_total: 4,
}

describe('Armazenamento de livros', () => {
  beforeEach(() => {
    useLivroStore.setState({ livros: [] })
  })

  it('cadastra um livro com exemplares disponíveis', () => {
    useLivroStore.getState().adicionarLivro(dadosLivro)

    expect(useLivroStore.getState().livros).toMatchObject([
      {
        ...dadosLivro,
        quantidade_disponivel: 4,
        quantidade_emprestada: 0,
        arquivado: false,
      },
    ])
  })

  it('atualiza os dados de um livro já cadastrado', () => {
    useLivroStore.getState().adicionarLivro(dadosLivro)
    const [livro] = useLivroStore.getState().livros
    useLivroStore.getState().atualizarLivro(livro.codigo, {
      ...dadosLivro,
      quantidade_total: 8,
      nome: 'Dom Casmurro — edição nova',
    })

    expect(useLivroStore.getState().livros[0]).toMatchObject({
      nome: 'Dom Casmurro — edição nova',
      quantidade_total: 8,
      quantidade_disponivel: 8,
    })
  })

  it('arquiva um livro sem removê-lo do armazenamento', () => {
    useLivroStore.getState().adicionarLivro(dadosLivro)
    const [livro] = useLivroStore.getState().livros
    useLivroStore.getState().arquivarLivro(livro.codigo)

    expect(useLivroStore.getState().livros[0].arquivado).toBe(true)
  })
})
