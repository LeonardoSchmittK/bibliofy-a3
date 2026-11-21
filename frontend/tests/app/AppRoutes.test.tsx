
import { render, screen, cleanup, fireEvent } from '@testing-library/react'
import { describe, it, expect, afterEach } from 'vitest'
import { AppRoutes } from '../../src/routes/AppRoutes'
import { useEmprestimoStore } from '../../src/modules/emprestimo/store/emprestimoStore'
import { useLeitorStore } from '../../src/modules/leitor/store/leitorStore'
import { useLivroStore } from '../../src/modules/livro/store/livroStore'

const emprestimosIniciais = useEmprestimoStore.getState().emprestimos
const leitoresIniciais = useLeitorStore.getState().leitores
const livrosIniciais = useLivroStore.getState().livros

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
  useLivroStore.setState({ livros: livrosIniciais })
  window.localStorage.clear()
  window.history.replaceState({}, '', '/')
})

describe('Rotas do Bibliofy', () => {
  it('deve navegar para Login', async () => {
    window.history.replaceState({}, '', '/login')
    render(<AppRoutes />)

    expect(screen.getByLabelText(/qual seu email/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/qual sua senha/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /acessar/i })).toBeInTheDocument()
    expect(screen.queryByRole('link', { name: /voltar ao início/i })).not.toBeInTheDocument()
  })

  it('deve navegar para Cadastro', async () => {
    window.history.replaceState({}, '', '/cadastro')
    render(<AppRoutes />)

    expect(screen.getByLabelText(/qual seu nome/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/qual sua matrícula/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /cadastrar/i })).toBeInTheDocument()
  })

  it('redireciona para login quando a pessoa não está autenticada', () => {
    window.history.replaceState({}, '', '/')
    render(<AppRoutes />)

    expect(screen.getByLabelText(/qual seu email/i)).toBeInTheDocument()
  })

  it('redireciona rotas privadas para login sem sessão', () => {
    window.history.replaceState({}, '', '/livros')
    render(<AppRoutes />)

    expect(screen.getByLabelText(/qual seu email/i)).toBeInTheDocument()
  })

  it('permite acesso às rotas privadas com token de sessão', () => {
    window.localStorage.setItem('access_token', 'test-token')
    window.history.replaceState({}, '', '/livros')
    render(<AppRoutes />)

    expect(screen.getByRole('heading', { name: /repositório de livros/i })).toBeInTheDocument()
  })

  it('permite acesso à área do bibliotecário com token de sessão', () => {
    window.localStorage.setItem('access_token', 'test-token')
    window.history.replaceState({}, '', '/bibliotecario')
    render(<AppRoutes />)

    expect(screen.getByRole('heading', { name: /área do bibliotecário/i })).toBeInTheDocument()
  })

  it('exibe a gestão de empréstimos com filtros por status, id e intervalo', () => {
    window.localStorage.setItem('access_token', 'test-token')
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
    window.localStorage.setItem('access_token', 'test-token')
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
    window.localStorage.setItem('access_token', 'test-token')
    window.history.replaceState({}, '', '/emprestimos/novo')
    render(<AppRoutes />)

    fireEvent.click(screen.getByRole('button', { name: /consultar penalidades/i }))

    const dialog = screen.getByRole('dialog', { name: /penalidades/i })
    expect(dialog).toHaveTextContent(/cada livro devolvido após o prazo gera 10 dias/i)
    expect(dialog).toHaveTextContent(/dois livros.*20 dias; três.*30 dias/i)
    expect(dialog).toHaveTextContent(/não permite novos empréstimos durante sua vigência/i)
  })

  it('registra a devolução atrasada, cria o impedimento e atualiza o estoque', () => {
    window.localStorage.setItem('access_token', 'test-token')
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
    window.localStorage.setItem('access_token', 'test-token')
    window.history.replaceState({}, '', '/emprestimos/novo')
    render(<AppRoutes />)

    fireEvent.click(screen.getByRole('link', { name: /voltar para a tela inicial/i }))

    expect(screen.getByRole('heading', { name: /olá, bibliotecário/i })).toBeInTheDocument()
  })

  it('volta da gestão de empréstimos para a tela inicial', () => {
    window.localStorage.setItem('access_token', 'test-token')
    window.history.replaceState({}, '', '/emprestimos')
    render(<AppRoutes />)

    fireEvent.click(screen.getByRole('link', { name: /voltar para a tela inicial/i }))

    expect(screen.getByRole('heading', { name: /olá, bibliotecário/i })).toBeInTheDocument()
  })

  it('filtra empréstimos por id do livro e respeita o intervalo de início', () => {
    window.localStorage.setItem('access_token', 'test-token')
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
