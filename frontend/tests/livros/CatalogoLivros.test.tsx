import { cleanup, fireEvent, render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { AppRoutes } from '../../src/routes/AppRoutes'
import { useLivroStore } from '../../src/modules/livro/store/livroStore'
import { useAuthStore } from '../../src/modules/auth/store/authStore'
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

function respostaApi(body: unknown, status = 200): Response {
  return {
    ok: status >= 200 && status < 300,
    status,
    text: async () => JSON.stringify(body),
  } as Response
}

function dadosApi(livro: Livro, arquivado = livro.arquivado) {
  return {
    codigo: livro.codigo,
    isbn: livro.isbn,
    nome: livro.nome,
    autor: livro.autor,
    editora: livro.editora,
    genero: livro.genero,
    data_lancamento: livro.data_lancamento,
    descricao: null,
    quantidade_total: livro.quantidade_total,
    quantidade_disponivel: livro.quantidade_disponivel,
    disponibilidade: livro.quantidade_disponivel > 0 ? 'DISPONIVEL' : 'EMPRESTADO',
    arquivado,
  }
}

function autenticar(papel: 'LEITOR' | 'BIBLIOTECARIO') {
  window.sessionStorage.setItem('access_token', 'local-test')
  useAuthStore.setState({
    accessToken: 'local-test',
    estado: 'authenticated',
    usuario: {
      codigo: 'usr_test',
      matricula: 'test',
      nome: 'Usuário de teste',
      email: 'teste@bibliofy.com',
      telefone: null,
      papel,
      ativo: true,
    },
  })
}

beforeEach(() => {
  autenticar('LEITOR')
  window.history.replaceState({}, '', '/livros')
  useLivroStore.setState({ livros: livrosTeste, carregado: true, erro: null })
  vi.stubGlobal('fetch', vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
    const url = String(input)
    if (url.endsWith('/arquivar')) {
      return respostaApi(dadosApi(livrosTeste[0], true))
    }
    if (init?.method === 'PATCH') {
      const livro = livrosTeste[0]
      return respostaApi(dadosApi(livro))
    }
    return respostaApi([])
  }))
})

afterEach(() => {
  cleanup()
  useLivroStore.setState({ livros: [], carregado: false, carregando: false, erro: null })
  window.localStorage.clear()
  window.sessionStorage.clear()
  useAuthStore.setState({
    accessToken: null,
    usuario: null,
    estado: 'unauthenticated',
    erro: null,
    carregandoLogin: false,
  })
  vi.unstubAllGlobals()
  window.history.replaceState({}, '', '/')
})

describe('Catálogo de livros', () => {
  it('filtra por disponibilidade e mantém a visão de leitor somente para consulta', async () => {
    const user = userEvent.setup()
    render(<AppRoutes />)

    expect(screen.getByRole('heading', { name: 'Catálogo de Livros' })).toBeInTheDocument()
    expect(screen.queryByRole('link', { name: /cadastrar livro/i })).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /editar livro disponível/i })).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /arquivar livro disponível/i })).not.toBeInTheDocument()

    await user.click(screen.getByRole('button', { name: /indisponíveis/i }))

    expect(screen.getByRole('heading', { name: 'Livro indisponível' })).toBeInTheDocument()
    expect(screen.queryByRole('heading', { name: 'Livro disponível' })).not.toBeInTheDocument()
  })

  it('não abre o modal de cadastro por URL para leitor', () => {
    window.history.replaceState({}, '', '/livros?modal=cadastro')
    render(<AppRoutes />)

    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Catálogo de Livros' })).toBeInTheDocument()
  })

  it('abre o formulário de edição em um modal para bibliotecário', async () => {
    autenticar('BIBLIOTECARIO')
    const user = userEvent.setup()
    render(<AppRoutes />)

    await user.click(screen.getByRole('button', { name: 'Editar Livro disponível' }))

    expect(screen.getByRole('dialog', { name: 'Editar livro' })).toBeInTheDocument()
    expect(screen.getByRole('textbox', { name: 'Título do livro' })).toHaveValue('Livro disponível')
  })

  it('usa diálogo nativo e fecha ao clicar no backdrop', async () => {
    autenticar('BIBLIOTECARIO')
    const user = userEvent.setup()
    render(<AppRoutes />)

    await user.click(screen.getByRole('button', { name: 'Editar Livro disponível' }))
    const dialog = screen.getByRole('dialog', { name: 'Editar livro' })

    expect(dialog.tagName).toBe('DIALOG')
    fireEvent.click(dialog)
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
  })

  it('abre o cadastro em um modal dentro do catálogo', async () => {
    autenticar('BIBLIOTECARIO')
    const user = userEvent.setup()
    render(<AppRoutes />)

    await user.click(screen.getByRole('button', { name: /cadastrar livro/i }))

    expect(screen.getByRole('dialog', { name: 'Cadastrar novo exemplar' })).toBeInTheDocument()
    expect(screen.getByRole('textbox', { name: 'Título do livro' })).toBeInTheDocument()
  })

  it('mantém erros de validação do cadastro somente dentro do modal', async () => {
    autenticar('BIBLIOTECARIO')
    useLivroStore.setState({ livros: [], carregado: true, erro: null })
    vi.stubGlobal('fetch', vi.fn(async () =>
      respostaApi({ detail: [{ msg: 'Value error, ISBN inválido: 2E' }] }, 422),
    ))
    render(<AppRoutes />)

    fireEvent.click(screen.getByRole('button', { name: /cadastrar livro/i }))
    fireEvent.change(screen.getByLabelText('Título do livro'), { target: { value: 'Livro teste' } })
    fireEvent.change(screen.getByLabelText('Editora'), { target: { value: 'Editora teste' } })
    fireEvent.change(screen.getByLabelText('Autor'), { target: { value: 'Autora teste' } })
    fireEvent.change(screen.getByLabelText('Data de publicação'), { target: { value: '2020-01-01' } })
    fireEvent.change(screen.getByLabelText('ISBN'), { target: { value: '2E' } })
    fireEvent.click(within(screen.getByRole('dialog')).getByRole('button', { name: 'Cadastrar livro' }))

    const dialog = await screen.findByRole('dialog', { name: 'Cadastrar novo exemplar' })
    const error = await screen.findByRole('alert')
    expect(error).toHaveTextContent('ISBN inválido. Verifique o número e tente novamente.')
    expect(error).not.toHaveTextContent('Value error')
    expect(dialog).toContainElement(error)
    expect(screen.getAllByRole('alert')).toHaveLength(1)
  })

  it('confirma o arquivamento em um modal', async () => {
    autenticar('BIBLIOTECARIO')
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

  it('não concede edição com base em papel local antigo', () => {
    window.localStorage.setItem('bibliofy_role', 'BIBLIOTECARIO')
    window.localStorage.setItem('bibliofy_user', 'Ana Bibliotecária')
    render(<AppRoutes />)

    expect(screen.queryByRole('button', { name: 'Editar Livro disponível' })).not.toBeInTheDocument()
  })
})
