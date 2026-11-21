import { cleanup, render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, beforeEach, describe, expect, it } from 'vitest'
import { AppRoutes } from '../../src/routes/AppRoutes'
import { useLivroStore } from '../../src/modules/livro/store/livroStore'
import type { Livro } from '../../src/modules/livro/types/livro'

const livrosTeste: Livro[] = [
  {
    codigo: 'liv_1',
    isbn: '9780000000001',
    nome: 'Livro disponível',
    autor: 'Autora A',
    editora: 'Editora A',
    genero: 'Ficção',
    data_lancamento: '2020-01-01',
    quantidade_total: 2,
    quantidade_disponivel: 2,
    quantidade_emprestada: 0,
    arquivado: false,
  },
  {
    codigo: 'liv_2',
    isbn: '9780000000002',
    nome: 'Livro indisponível',
    autor: 'Autor B',
    editora: 'Editora B',
    genero: 'Infantil',
    data_lancamento: '2021-01-01',
    quantidade_total: 1,
    quantidade_disponivel: 0,
    quantidade_emprestada: 1,
    arquivado: false,
  },
]

beforeEach(() => {
  window.localStorage.setItem('access_token', 'local-test')
  window.localStorage.setItem('bibliofy_role', 'LEITOR')
  window.history.replaceState({}, '', '/livros')
  useLivroStore.setState({ livros: livrosTeste })
})

afterEach(() => {
  cleanup()
  useLivroStore.setState({ livros: [] })
  window.localStorage.clear()
  window.history.replaceState({}, '', '/')
})

describe('Catálogo de livros', () => {
  it('filtra por disponibilidade e mantém a visão de leitor somente para consulta', async () => {
    const user = userEvent.setup()
    render(<AppRoutes />)

    expect(screen.getByRole('heading', { name: 'Catálogo de Livros' })).toBeInTheDocument()
    expect(screen.queryByRole('link', { name: /cadastrar livro/i })).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /editar livro disponível/i })).not.toBeInTheDocument()

    await user.click(screen.getByRole('button', { name: /indisponíveis/i }))

    expect(screen.getByRole('heading', { name: 'Livro indisponível' })).toBeInTheDocument()
    expect(screen.queryByRole('heading', { name: 'Livro disponível' })).not.toBeInTheDocument()
  })

  it('abre o formulário de edição em um modal para bibliotecário', async () => {
    window.localStorage.setItem('bibliofy_role', 'BIBLIOTECARIO')
    const user = userEvent.setup()
    render(<AppRoutes />)

    await user.click(screen.getByRole('button', { name: 'Editar Livro disponível' }))

    expect(screen.getByRole('dialog', { name: 'Editar livro' })).toBeInTheDocument()
    expect(screen.getByRole('textbox', { name: 'Título do livro' })).toHaveValue('Livro disponível')
  })

  it('abre o cadastro em um modal dentro do catálogo', async () => {
    window.localStorage.setItem('bibliofy_role', 'BIBLIOTECARIO')
    const user = userEvent.setup()
    render(<AppRoutes />)

    await user.click(screen.getByRole('button', { name: /cadastrar livro/i }))

    expect(screen.getByRole('dialog', { name: 'Cadastrar novo exemplar' })).toBeInTheDocument()
    expect(screen.getByRole('textbox', { name: 'Título do livro' })).toBeInTheDocument()
  })

  it('confirma o arquivamento em um modal', async () => {
    window.localStorage.setItem('bibliofy_role', 'BIBLIOTECARIO')
    const user = userEvent.setup()
    render(<AppRoutes />)

    await user.click(screen.getByRole('button', { name: 'Arquivar Livro disponível' }))
    expect(screen.getByRole('dialog', { name: 'Arquivar livro' })).toBeInTheDocument()
    expect(screen.getByText((_, element) =>
      element?.tagName === 'P'
      && element.textContent?.replace(/\s+/g, ' ').trim()
        === 'Deseja arquivar Livro disponível? O livro deixará de aparecer no catálogo.',
    )).toBeInTheDocument()

    await user.click(screen.getByRole('button', { name: 'Cancelar' }))
    expect(screen.getByRole('heading', { name: 'Livro disponível' })).toBeInTheDocument()

    await user.click(screen.getByRole('button', { name: 'Arquivar Livro disponível' }))
    await user.click(screen.getByRole('button', { name: 'Arquivar livro' }))

    expect(screen.queryByRole('heading', { name: 'Livro disponível' })).not.toBeInTheDocument()
  })

  it('mantém a edição disponível para uma sessão antiga de bibliotecário', () => {
    window.localStorage.removeItem('bibliofy_role')
    window.localStorage.setItem('bibliofy_user', 'Ana Bibliotecária')
    render(<AppRoutes />)

    expect(screen.getByRole('button', { name: 'Editar Livro disponível' })).toBeInTheDocument()
  })
})
