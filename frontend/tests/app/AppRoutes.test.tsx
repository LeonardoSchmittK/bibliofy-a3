
import { render, screen, cleanup, fireEvent, act, waitFor } from '@testing-library/react'
import { beforeEach, describe, it, expect, afterEach, vi } from 'vitest'
import { AppRoutes } from '../../src/routes/AppRoutes'
import { useEmprestimoStore } from '../../src/modules/emprestimo/store/emprestimoStore'
import { useLeitorStore } from '../../src/modules/leitor/store/leitorStore'
import { useLivroStore } from '../../src/modules/livro/store/livroStore'
import { useAuthStore } from '../../src/modules/auth/store/authStore'
import type { Livro } from '../../src/modules/livro/types/livro'
import type { UsuarioAutenticado } from '../../src/modules/auth/types/auth'

const emprestimosIniciais = useEmprestimoStore.getState().emprestimos
const leitoresIniciais = useLeitorStore.getState().leitores
const livrosIniciais = useLivroStore.getState().livros
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
  vi.stubGlobal('fetch', vi.fn(async (input: RequestInfo | URL) => {
    const url = String(input)
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
    if (url.includes('/livros/')) return respostaApi([])
    return respostaApi({ detail: 'Rota não encontrada' }, 404)
  }))
})

function dataISO(data: Date): string {
  return [
    data.getFullYear(),
    String(data.getMonth() + 1).padStart(2, '0'),
    String(data.getDate()).padStart(2, '0'),
  ].join('-')
}

function adicionarDias(data: string, dias: number): string {
  const [ano, mes, dia] = data.split('-').map(Number)
  return dataISO(new Date(ano, mes - 1, dia + dias, 12))
}

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

  it.each(['/emprestimos', '/emprestimos/novo'])(
    'redireciona leitor que tenta acessar %s',
    (path) => {
      autenticar('LEITOR')
      window.history.replaceState({}, '', path)
      render(<AppRoutes />)

      expect(screen.getByRole('heading', { name: 'Olá, Leitor.' })).toBeInTheDocument()
      expect(screen.queryByRole('heading', { name: /empréstimo/i })).not.toBeInTheDocument()
    },
  )

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

  it('seleciona exemplar e leitor, confirma e abre a gestão', () => {
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
    fireEvent.click(screen.getByRole('button', { name: /Ana Costa/ }))

    expect(screen.getByRole('dialog', { name: /confirmar empréstimo/i })).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: /confirmar/i }))
    expect(screen.getByRole('heading', { name: /gerir empréstimos/i })).toBeInTheDocument()
    expect(screen.getByRole('status')).toHaveTextContent(/9 empréstimos encontrados/i)
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

  it('registra a devolução atrasada, cria o impedimento e atualiza o estoque', () => {
    autenticar()
    window.history.replaceState({}, '', '/emprestimos')
    render(<AppRoutes />)

    fireEvent.click(screen.getByRole('button', { name: /emp_32910482/i }))

    expect(
      screen.getByRole('row', { name: /Bruno Lima.*Dom Quixote.*Devolvido com atraso/i }),
    ).toBeInTheDocument()
    expect(useEmprestimoStore.getState().impedimentos).toHaveLength(1)
    expect(useLivroStore.getState().livros.find((livro) => livro.codigo === 'liv_00000001'))
      .toMatchObject({ quantidade_disponivel: 167, quantidade_emprestada: 13 })

    cleanup()
    window.history.replaceState({}, '', '/emprestimos/novo')
    render(<AppRoutes />)
    fireEvent.click(screen.getByRole('button', { name: /escolha o leitor/i }))
    expect(
      screen.getByRole('button', { name: /Bruno Lima.*Impedido até/i }),
    ).toBeDisabled()
  })

  it('acumula dez dias por cada devolução atrasada e bloqueia novos empréstimos', () => {
    const emprestimoBase = emprestimosIniciais.find((emprestimo) => emprestimo.id === 2)
    if (!emprestimoBase) throw new Error('Empréstimo exemplo não encontrado.')

    const emprestimosAtrasados = [
      emprestimoBase,
      ...[9, 10].map((id) => ({
        ...emprestimoBase,
        id,
        codigo: `emp_${id}`,
        livroId: 'liv_00000002',
        livroNome: 'O Pequeno Príncipe',
      })),
    ]
    useEmprestimoStore.setState({
      emprestimos: emprestimosAtrasados,
      impedimentos: [],
    })

    const registrarDevolucao = useEmprestimoStore.getState().registrarDevolucao
    expect(registrarDevolucao(2)).toBe(true)
    expect(registrarDevolucao(9)).toBe(true)
    expect(registrarDevolucao(10)).toBe(true)

    const impedimentos = useEmprestimoStore.getState().impedimentos
    const hoje = dataISO(new Date())
    expect(impedimentos).toHaveLength(3)
    expect(impedimentos.map((impedimento) => impedimento.inicio)).toEqual([
      hoje,
      adicionarDias(hoje, 10),
      adicionarDias(hoje, 20),
    ])
    expect(impedimentos[2].fimExclusivo).toBe(adicionarDias(hoje, 30))
    expect(
      useEmprestimoStore.getState().registrarEmprestimo({
        livroId: 'liv_00000001',
        livroNome: 'Dom Quixote',
        leitorId: emprestimoBase.leitorId,
        leitorNome: emprestimoBase.leitorNome,
      }),
    ).toBe(false)
  })

  it('não cria impedimento para uma devolução dentro do prazo', () => {
    const emprestimoBase = emprestimosIniciais.find((emprestimo) => emprestimo.id === 1)
    if (!emprestimoBase) throw new Error('Empréstimo exemplo não encontrado.')

    useEmprestimoStore.setState({
      emprestimos: [{
        ...emprestimoBase,
        dataDevolucao: adicionarDias(dataISO(new Date()), 1),
        status: 'EM_ANDAMENTO',
      }],
      impedimentos: [],
    })

    expect(useEmprestimoStore.getState().registrarDevolucao(emprestimoBase.id)).toBe(true)
    expect(useEmprestimoStore.getState().impedimentos).toHaveLength(0)
    expect(useEmprestimoStore.getState().emprestimos[0].status).toBe('DEVOLVIDO')
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
