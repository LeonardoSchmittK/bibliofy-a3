
import { render, screen, cleanup, fireEvent, act, waitFor } from '@testing-library/react'
import { beforeEach, describe, it, expect, afterEach, vi } from 'vitest'
import { AppRoutes } from '../../src/routes/AppRoutes'
import { useEmprestimoStore } from '../../src/modules/emprestimo/store/emprestimoStore'
import { useLeitorStore } from '../../src/modules/leitor/store/leitorStore'
import { useLivroStore } from '../../src/modules/livro/store/livroStore'
import { useAuthStore } from '../../src/modules/auth/store/authStore'
import type { Livro } from '../../src/modules/livro/types/livro'
import type { UsuarioAutenticado } from '../../src/modules/auth/types/auth'
import type { Emprestimo } from '../../src/modules/emprestimo/types/emprestimo'

const leitoresIniciais = useLeitorStore.getState().leitores
const livrosIniciais = useLivroStore.getState().livros
const emprestimosIniciais: Emprestimo[] = [
  {
    id: 1,
    codigo: 'emp_32910482',
    leitorId: 'cus_001',
    leitorNome: 'Bruno Lima',
    livroId: 'liv_00000001',
    livroNome: 'Dom Quixote',
    livroIsbn: '9788491050296',
    dataEmprestimo: '2026-01-01',
    dataDevolucao: '2026-12-31',
    renovado: false,
    status: 'ATRASADO',
  },
  {
    id: 2,
    codigo: 'emp_04394934',
    leitorId: 'cus_002',
    leitorNome: 'Ana Costa',
    livroId: 'liv_00000002',
    livroNome: 'O Pequeno Príncipe',
    livroIsbn: '9788522031443',
    dataEmprestimo: '2026-01-02',
    dataDevolucao: '2026-12-31',
    renovado: false,
    status: 'EM_ANDAMENTO',
  },
  ...Array.from({ length: 7 }, (_, index) => ({
    id: index + 3,
    codigo: `emp_${index + 3}`,
    leitorId: `cus_${index + 3}`,
    leitorNome: `Leitor ${index + 3}`,
    livroId: index % 2 === 0 ? 'liv_00000001' : 'liv_00000002',
    livroNome: index % 2 === 0 ? 'Dom Quixote' : 'O Pequeno Príncipe',
    livroIsbn: index % 2 === 0 ? '9788491050296' : '9788522031443',
    dataEmprestimo: `2026-01-${String(index + 3).padStart(2, '0')}`,
    dataDevolucao: '2026-12-31',
    renovado: false,
    status: 'EM_ANDAMENTO' as const,
  })),
]
const livrosTeste: Livro[] = [
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
]

function autenticar(papel: UsuarioAutenticado['papel'] = 'BIBLIOTECARIO') {
  window.sessionStorage.setItem('access_token', 'test-token')
  useAuthStore.setState({
    accessToken: 'test-token',
    usuario: {
      codigo: 'usr_test',
      matricula: 'test',
      nome: papel === 'BIBLIOTECARIO' ? 'Ana Bibliotecária' : 'Leitor Teste',
      email: 'teste@bibliofy.com',
      telefone: null,
      papel,
      ativo: true,
    },
    estado: 'authenticated',
    erro: null,
  })
  useLivroStore.setState({ livros: livrosTeste, carregado: true, erro: null })
}

function respostaApi(body: unknown, status = 200): Response {
  return {
    ok: status >= 200 && status < 300,
    status,
    text: async () => body === undefined ? '' : JSON.stringify(body),
  } as Response
}

beforeEach(() => {
  useEmprestimoStore.setState({
    emprestimos: emprestimosIniciais,
    impedimentos: [],
  })
  vi.stubGlobal('fetch', vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
    const url = String(input)
    if (url.endsWith('/emprestimos')) {
      return respostaApi(emprestimosIniciais.map((emprestimo) => ({
        id: emprestimo.id,
        codigo: emprestimo.codigo,
        pessoa_codigo: emprestimo.leitorId,
        pessoa_nome: emprestimo.leitorNome,
        livro_codigo: emprestimo.livroId,
        livro_nome: emprestimo.livroNome,
        livro_isbn: emprestimo.livroIsbn,
        data_emprestimo: emprestimo.dataEmprestimo,
        data_prevista: emprestimo.dataDevolucao,
        data_devolucao: emprestimo.dataDevolucaoRealizada ?? null,
        renovado: emprestimo.renovado,
        status_atual: emprestimo.status === 'EM_ANDAMENTO' ? 'EMPRESTADO' : emprestimo.status,
        bloqueio_inicio: emprestimo.bloqueioInicio ?? null,
        bloqueio_fim_exclusivo: emprestimo.bloqueioFimExclusivo ?? null,
      })))
    }
    if (url.endsWith('/auth/login')) return respostaApi({ access_token: 'test-token', token_type: 'bearer' })
    if (url.endsWith('/auth/me')) {
      return respostaApi({
        codigo: 'usr_test',
        matricula: 'test',
        nome: 'Ana Bibliotecária',
        email: 'teste@bibliofy.com',
        telefone: null,
        papel: 'BIBLIOTECARIO',
        ativo: true,
      })
    }
    if (url.endsWith('/emprestimos')) {
      if (init?.method === 'POST') {
        const dados = JSON.parse(String(init.body)) as { pessoa_codigo: string; livro_codigo: string }
        return respostaApi({
          id: 100,
          codigo: 'emp_novo',
          pessoa_codigo: dados.pessoa_codigo,
          pessoa_nome: dados.pessoa_codigo === 'cus_002' ? 'Ana Costa' : 'Leitor',
          livro_codigo: dados.livro_codigo,
          livro_nome: dados.livro_codigo === 'liv_00000002' ? 'O Pequeno Príncipe' : 'Dom Quixote',
          livro_isbn: dados.livro_codigo === 'liv_00000002' ? '9788522031443' : '9788491050296',
          data_emprestimo: '2026-01-01',
          data_prevista: '2026-12-31',
          data_devolucao: null,
          renovado: false,
          status_atual: 'EMPRESTADO',
          bloqueio_inicio: null,
          bloqueio_fim_exclusivo: null,
        })
      }
      return respostaApi(emprestimosIniciais.map((emprestimo) => ({
        id: emprestimo.id,
        codigo: emprestimo.codigo,
        pessoa_codigo: emprestimo.leitorId,
        pessoa_nome: emprestimo.leitorNome,
        livro_codigo: emprestimo.livroId,
        livro_nome: emprestimo.livroNome,
        livro_isbn: emprestimo.livroIsbn,
        data_emprestimo: emprestimo.dataEmprestimo,
        data_prevista: emprestimo.dataDevolucao,
        data_devolucao: emprestimo.dataDevolucaoRealizada ?? null,
        renovado: emprestimo.renovado,
        status_atual: emprestimo.status === 'EM_ANDAMENTO'
          ? 'EMPRESTADO'
          : emprestimo.status,
        bloqueio_inicio: emprestimo.bloqueioInicio ?? null,
        bloqueio_fim_exclusivo: emprestimo.bloqueioFimExclusivo ?? null,
      })))
    }
    if (url.includes('/emprestimos/') && url.endsWith('/devolucao') && init?.method === 'POST') {
      const atrasado = url.includes('/2/')
      return respostaApi({
        id: atrasado ? 2 : 1,
        codigo: atrasado ? 'emp_04394934' : 'emp_32910482',
        pessoa_codigo: atrasado ? 'cus_002' : 'cus_001',
        pessoa_nome: atrasado ? 'Ana Costa' : 'Bruno Lima',
        livro_codigo: atrasado ? 'liv_00000002' : 'liv_00000001',
        livro_nome: atrasado ? 'O Pequeno Príncipe' : 'Dom Quixote',
        livro_isbn: atrasado ? '9788522031443' : '9788491050296',
        data_emprestimo: atrasado ? '2026-01-02' : '2026-01-01',
        data_prevista: atrasado ? '2026-12-31' : '2026-12-31',
        data_devolucao: '2026-11-23',
        renovado: false,
        status_atual: atrasado ? 'DEVOLVIDO_COM_ATRASO' : 'DEVOLVIDO',
        bloqueio_inicio: atrasado ? '2026-11-23' : null,
        bloqueio_fim_exclusivo: atrasado ? '2026-12-03' : null,
      })
    }
    if (url.includes('/usuarios?papel=LEITOR')) {
      return respostaApi([
        { codigo: 'cus_001', nome: 'Bruno Lima', ativo: true },
        { codigo: 'cus_002', nome: 'Ana Costa', ativo: true },
      ])
    }
    if (url.includes('/livros/')) return respostaApi([])
    return respostaApi({ detail: 'Rota não encontrada' }, 404)
  }))
})

afterEach(() => {
  cleanup()
  useEmprestimoStore.setState({ emprestimos: emprestimosIniciais, impedimentos: [] })
  useLeitorStore.setState({ leitores: leitoresIniciais })
  useLivroStore.setState({ livros: livrosIniciais, carregado: false, carregando: false, erro: null })
  window.localStorage.clear()
  window.sessionStorage.clear()
  useAuthStore.setState({
    accessToken: null,
    usuario: null,
    estado: 'unauthenticated',
    carregandoLogin: false,
    erro: null,
  })
  vi.unstubAllGlobals()
  window.history.replaceState({}, '', '/')
})

describe('Rotas do Bibliofy', () => {
  it('deve navegar para Login', async () => {
    window.history.replaceState({}, '', '/login')
    render(<AppRoutes />)

    expect(screen.getByLabelText(/email/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/senha/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /entrar na biblioteca/i })).toBeInTheDocument()
    expect(screen.queryByRole('link', { name: /voltar ao início/i })).not.toBeInTheDocument()
  })

  it('exibe o formulário de cadastro público', async () => {
    window.history.replaceState({}, '', '/cadastro')
    render(<AppRoutes />)

    expect(screen.getByLabelText(/nome/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/matrícula/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/email/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/senha/i)).toBeInTheDocument()
  })

  it('cria a conta pela API e orienta o usuário a entrar', async () => {
    window.history.replaceState({}, '', '/cadastro')
    const fetchMock = vi.fn(async (input: RequestInfo | URL) => {
      if (String(input).endsWith('/auth/registro')) {
        return respostaApi({
          codigo: 'cus_00000001',
          matricula: '2026001',
          nome: 'Ana Souza',
          email: 'ana@escola.edu',
          telefone: null,
          papel: 'LEITOR',
          ativo: true,
        }, 201)
      }
      return respostaApi({ detail: 'Rota não encontrada' }, 404)
    })
    vi.stubGlobal('fetch', fetchMock)
    render(<AppRoutes />)

    fireEvent.change(screen.getByLabelText(/nome/i), { target: { value: 'Ana Souza' } })
    fireEvent.change(screen.getByLabelText(/matrícula/i), { target: { value: '2026001' } })
    fireEvent.change(screen.getByLabelText(/email/i), { target: { value: 'ana@escola.edu' } })
    fireEvent.change(screen.getByLabelText(/senha/i), { target: { value: 'senha-segura' } })
    fireEvent.click(screen.getByRole('button', { name: /criar conta/i }))

    expect(await screen.findByRole('status')).toHaveTextContent(/conta criada/i)
    expect(screen.getByRole('link', { name: /entre com seu e-mail e senha/i })).toHaveAttribute(
      'href',
      '/login',
    )
    expect(fetchMock).toHaveBeenCalledWith(
      expect.stringContaining('/auth/registro'),
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify({
          nome: 'Ana Souza',
          matricula: '2026001',
          email: 'ana@escola.edu',
          telefone: null,
          senha: 'senha-segura',
        }),
      }),
    )
  })

  it('mostra o erro da API quando o cadastro falha', async () => {
    window.history.replaceState({}, '', '/cadastro')
    vi.stubGlobal('fetch', vi.fn(async () => respostaApi(
      { detail: 'E-mail ou matrícula já cadastrados' },
      409,
    )))
    render(<AppRoutes />)

    fireEvent.change(screen.getByLabelText(/nome/i), { target: { value: 'Ana Souza' } })
    fireEvent.change(screen.getByLabelText(/matrícula/i), { target: { value: '2026001' } })
    fireEvent.change(screen.getByLabelText(/email/i), { target: { value: 'ana@escola.edu' } })
    fireEvent.change(screen.getByLabelText(/senha/i), { target: { value: 'senha-segura' } })
    fireEvent.click(screen.getByRole('button', { name: /criar conta/i }))

    expect(await screen.findByRole('alert')).toHaveTextContent(
      'E-mail ou matrícula já cadastrados',
    )
  })

  it('autentica com a API e abre o painel', async () => {
    window.history.replaceState({}, '', '/login')
    render(<AppRoutes />)

    fireEvent.change(screen.getByLabelText(/email/i), {
      target: { value: 'ana@bibliofy.com' },
    })
    fireEvent.change(screen.getByLabelText(/senha/i), {
      target: { value: 'senha-segura' },
    })
    fireEvent.click(screen.getByRole('button', { name: /entrar na biblioteca/i }))

    await waitFor(() => {
      expect(screen.getByRole('heading', { name: /olá, ana/i })).toBeInTheDocument()
    })
    expect(fetch).toHaveBeenCalledWith(
      expect.stringContaining('/auth/login'),
      expect.objectContaining({
        method: 'POST',
        body: expect.any(URLSearchParams),
      }),
    )
    expect(window.sessionStorage.getItem('access_token')).toBe('test-token')
  })

  it('redireciona para login quando a pessoa não está autenticada', () => {
    window.history.replaceState({}, '', '/')
    render(<AppRoutes />)

    expect(screen.getByLabelText(/email/i)).toBeInTheDocument()
  })

  it('redireciona rotas privadas para login sem sessão', () => {
    window.history.replaceState({}, '', '/livros')
    render(<AppRoutes />)

    expect(screen.getByLabelText(/email/i)).toBeInTheDocument()
  })

  it('permite acesso às rotas privadas com token de sessão', () => {
    autenticar()
    window.history.replaceState({}, '', '/livros')
    render(<AppRoutes />)

    expect(screen.getByRole('heading', { name: /catálogo de livros/i })).toBeInTheDocument()
  })

  it('anima as estatísticas da tela inicial de zero até os valores reais', () => {
    const frames: FrameRequestCallback[] = []
    vi.stubGlobal('requestAnimationFrame', (callback: FrameRequestCallback) => {
      frames.push(callback)
      return frames.length
    })
    vi.stubGlobal('cancelAnimationFrame', vi.fn())
    autenticar()
    window.history.replaceState({}, '', '/')
    render(<AppRoutes />)

    const estatisticasLivros = screen.getByRole('group', {
      name: '255 exemplares disponíveis e 25 emprestados',
    })
    const lerValores = () =>
      Array.from(estatisticasLivros.querySelectorAll('.stat-number'), (item) => item.textContent)

    expect(lerValores()).toEqual(['0', '0'])

    act(() => {
      frames.splice(0).forEach((frame) => frame(0))
      frames.splice(0).forEach((frame) => frame(700))
    })

    expect(lerValores()).toEqual(['255', '25'])
  })

  it('mostra ao leitor o estoque, sem ações ou estatísticas de empréstimo', () => {
    autenticar('LEITOR')
    window.history.replaceState({}, '', '/')
    render(<AppRoutes />)

    expect(screen.getByRole('link', { name: /ver estoque/i })).toHaveAttribute('href', '/livros')
    expect(screen.queryByRole('link', { name: /gerenciar empréstimos/i })).not.toBeInTheDocument()
    expect(screen.queryByRole('link', { name: /registrar empréstimo/i })).not.toBeInTheDocument()
    expect(screen.queryByRole('link', { name: /adicionar livro/i })).not.toBeInTheDocument()
    expect(screen.queryByRole('group', { name: /empréstimos abertos/i })).not.toBeInTheDocument()
    expect(screen.getByRole('group', { name: /exemplares disponíveis e .* emprestados/i }))
      .toBeInTheDocument()
  })

  it('bloqueia leitor que tenta registrar empréstimo', () => {
    autenticar('LEITOR')
    window.history.replaceState({}, '', '/emprestimos/novo')
    render(<AppRoutes />)

    expect(screen.getByRole('alert')).toHaveTextContent(/apenas bibliotecários/i)
  })

  it('abre o drawer de sair ao passar pelo autor da citação', () => {
    autenticar()
    window.history.replaceState({}, '', '/emprestimos/novo')
    render(<AppRoutes />)

    const header = screen.getByRole('banner', { name: 'Ações da sessão' })
    const linhaDoAutor = document.querySelector('.loan-quote figcaption')
    if (!linhaDoAutor) throw new Error('A linha do autor da citação não foi renderizada.')

    fireEvent.pointerOver(linhaDoAutor)

    expect(header).toHaveClass('session-exit-header--open')
  })

  it('encerra a sessão pelo botão de sair do cabeçalho oculto', () => {
    autenticar()
    window.history.replaceState({}, '', '/livros')
    render(<AppRoutes />)

    fireEvent.click(screen.getByRole('button', { name: 'Sair' }))

    expect(screen.getByLabelText(/email/i)).toBeInTheDocument()
    expect(window.sessionStorage.getItem('access_token')).toBeNull()
  })

  it('permite acesso à área do bibliotecário com token de sessão', () => {
    autenticar()
    window.history.replaceState({}, '', '/bibliotecario')
    render(<AppRoutes />)

    expect(screen.getByRole('heading', { name: /área do bibliotecário/i })).toBeInTheDocument()
  })

  it('exibe a gestão de empréstimos com filtros por status, id e intervalo', () => {
    autenticar()
    window.history.replaceState({}, '', '/emprestimos')
    render(<AppRoutes />)

    expect(screen.getByRole('heading', { name: /gerir empréstimos/i })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /voltar para a tela inicial/i })).toHaveAttribute('href', '/')
    expect(screen.getByLabelText(/status/i)).toBeInTheDocument()
    expect(screen.getByRole('searchbox', { name: /buscar empréstimo/i })).toBeInTheDocument()
    expect(screen.getByLabelText(/data inicial/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/data final/i)).toBeInTheDocument()
  })

  it('seleciona exemplar e leitor, confirma e abre a gestão', async () => {
    autenticar()
    window.history.replaceState({}, '', '/emprestimos/novo')
    render(<AppRoutes />)

    expect(screen.getByRole('heading', { name: /qual livro emprestar e para quem/i })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /voltar para a tela inicial/i })).toHaveAttribute('href', '/')
    expect(screen.queryByText(/selecionar um exemplar|selecionar um leitor/i)).not.toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: /escolha o exemplar/i }))
    expect(screen.getByRole('dialog', { name: /escolha o exemplar/i })).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: /O Pequeno Príncipe/ }))
    fireEvent.click(screen.getByRole('button', { name: /escolha o leitor/i }))
    expect(screen.getByRole('dialog', { name: /escolha o leitor/i })).toBeInTheDocument()
  })

  it('explica a regra de impedimento no modal de penalidades', () => {
    autenticar()
    window.history.replaceState({}, '', '/emprestimos/novo')
    render(<AppRoutes />)

    fireEvent.click(screen.getByRole('button', { name: /consultar penalidades/i }))

    const dialog = screen.getByRole('dialog', { name: /penalidades/i })
    expect(dialog).toHaveTextContent(/cada livro devolvido após o prazo gera 10 dias/i)
    expect(dialog).toHaveTextContent(/dois livros.*20 dias; três.*30 dias/i)
    expect(dialog).toHaveTextContent(/não permite novos empréstimos durante sua vigência/i)
  })

  it('volta do registro de empréstimo para a tela inicial', () => {
    autenticar()
    window.history.replaceState({}, '', '/emprestimos/novo')
    render(<AppRoutes />)

    fireEvent.click(screen.getByRole('link', { name: /voltar para a tela inicial/i }))

    expect(screen.getByRole('heading', { name: /olá, ana/i })).toBeInTheDocument()
  })

  it('volta da gestão de empréstimos para a tela inicial', () => {
    autenticar()
    window.history.replaceState({}, '', '/emprestimos')
    render(<AppRoutes />)

    fireEvent.click(screen.getByRole('link', { name: /voltar para a tela inicial/i }))

    expect(screen.getByRole('heading', { name: /olá, ana/i })).toBeInTheDocument()
  })

  it('filtra empréstimos por id do livro e respeita o intervalo de início', () => {
    autenticar()
    window.history.replaceState({}, '', '/emprestimos')
    render(<AppRoutes />)

    const busca = screen.getByRole('searchbox', { name: /buscar empréstimo/i })
    fireEvent.change(busca, { target: { value: 'liv_00000002' } })
    expect(screen.getByRole('row', { name: /Ana Costa.*O Pequeno Príncipe/i })).toBeInTheDocument()
    expect(screen.queryByRole('row', { name: /Bruno Lima/ })).not.toBeInTheDocument()

    const emprestimoAna = emprestimosIniciais.find(
      (emprestimo) => emprestimo.codigo === 'emp_04394934',
    )
    expect(emprestimoAna).toBeDefined()
    fireEvent.change(screen.getByLabelText(/data inicial/i), {
      target: { value: emprestimoAna?.dataEmprestimo },
    })
    fireEvent.change(screen.getByLabelText(/data final/i), {
      target: { value: emprestimoAna?.dataEmprestimo },
    })
    fireEvent.change(busca, { target: { value: 'emp_04394934' } })
    expect(screen.getByRole('row', { name: /Ana Costa.*O Pequeno Príncipe/i })).toBeInTheDocument()
    expect(screen.queryByRole('row', { name: /Henrique Silva/ })).not.toBeInTheDocument()
  })
})
