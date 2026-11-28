import {
  useEffect,
  useState,
  type FormEvent,
  type PointerEvent as ReactPointerEvent,
  type ReactNode,
} from 'react'
import { Link, Redirect, Route, Switch, useLocation } from 'wouter'
import { getRandomQuote } from '../shared/utils/quotes'
import { useAuthStore } from '../modules/auth/store/authStore'
import type { UsuarioAutenticado } from '../modules/auth/types/auth'
import { useLivroStore } from '../modules/livro/store/livroStore'
import { CatalogoLivros } from '../modules/livro/pages/CatalogoLivros'
import { EmprestimosPage } from '../modules/emprestimo/pages/EmprestimosPage'
import { GerenciarEmprestimosPage } from '../modules/emprestimo/pages/GerenciarEmprestimosPage'
import { useEmprestimoStore } from '../modules/emprestimo/store/emprestimoStore'
import { apiRequest } from '../shared/api/client'

const quote = getRandomQuote()
const COUNT_UP_DURATION_MS = 650

function useCountUp(target: number): number {
  const prefersReducedMotion =
    window.matchMedia?.('(prefers-reduced-motion: reduce)').matches ?? false
  const [animation, setAnimation] = useState(() => ({
    target,
    value: prefersReducedMotion ? target : 0,
  }))

  useEffect(() => {
    if (prefersReducedMotion || target === 0) return
    let startedAt: number | null = null
    let frameId = 0
    function animate(timestamp: number) {
      if (startedAt === null) startedAt = timestamp
      const progress = Math.min((timestamp - startedAt) / COUNT_UP_DURATION_MS, 1)
      setAnimation({ target, value: Math.round(target * (1 - (1 - progress) ** 3)) })
      if (progress < 1) frameId = window.requestAnimationFrame(animate)
    }

    frameId = window.requestAnimationFrame(animate)
    return () => window.cancelAnimationFrame(frameId)
  }, [prefersReducedMotion, target])

  if (prefersReducedMotion) return target
  return animation.target === target ? animation.value : 0
}

function isExitDrawerTarget(target: EventTarget | null): boolean {
  return target instanceof Element
    && Boolean(target.closest('.session-exit-header, .dashboard-quote figcaption, .loan-quote figcaption'))
}

function TypewriterTitle({ text }: { text: string }) {
  const prefersReducedMotion =
    window.matchMedia?.('(prefers-reduced-motion: reduce)').matches ?? false
  const [displayedText, setDisplayedText] = useState(() =>
    prefersReducedMotion ? text : '',
  )
  const [isTyping, setIsTyping] = useState(!prefersReducedMotion)

  useEffect(() => {
    if (prefersReducedMotion) return

    let characterIndex = 0
    const interval = window.setInterval(() => {
      characterIndex += 1
      setDisplayedText(text.slice(0, characterIndex))

      if (characterIndex >= text.length) {
        window.clearInterval(interval)
        setIsTyping(false)
      }
    }, 55)

    return () => window.clearInterval(interval)
  }, [text, prefersReducedMotion])

  return (
    <h1 className="auth-title" aria-label={text}>
      <span aria-hidden="true">{displayedText}</span>
      {isTyping && <span className="auth-title-caret" aria-hidden="true" />}
    </h1>
  )
}

function PrivatePage({
  children,
  apenasBibliotecario = false,
}: {
  children: ReactNode
  apenasBibliotecario?: boolean
}) {
  const estado = useAuthStore((state) => state.estado)
  const usuario = useAuthStore((state) => state.usuario)
  const usuarioCodigo = usuario?.codigo
  const erro = useAuthStore((state) => state.erro)
  const inicializarSessao = useAuthStore((state) => state.inicializarSessao)
  const [exitDrawerOpen, setExitDrawerOpen] = useState(false)
  const sair = useAuthStore((state) => state.sair)
  const carregarLivros = useLivroStore((state) => state.carregarLivros)
  const livrosCarregados = useLivroStore((state) => state.carregado)
  const carregarEmprestimos = useEmprestimoStore((state) => state.carregarEmprestimos)
  const emprestimosCarregadosPara = useEmprestimoStore((state) => state.carregadoPara)

  useEffect(() => {
    void inicializarSessao()
  }, [inicializarSessao])

  useEffect(() => {
    if (estado === 'authenticated' && !livrosCarregados) void carregarLivros()
  }, [carregarLivros, estado, livrosCarregados])

  useEffect(() => {
    if (
      estado === 'authenticated' &&
      usuarioCodigo &&
      emprestimosCarregadosPara !== usuarioCodigo
    ) {
      void carregarEmprestimos()
    }
  }, [carregarEmprestimos, emprestimosCarregadosPara, estado, usuarioCodigo])

  if (estado === 'checking') {
    return <main className="simple-page" role="status">Verificando sessão...</main>
  }
  if (estado === 'error') {
    return (
      <main className="simple-page">
        <p role="alert">{erro || 'Não foi possível validar sua sessão.'}</p>
        <button type="button" onClick={() => void inicializarSessao()}>Tentar novamente</button>
      </main>
    )
  }
  if (estado !== 'authenticated') return <Redirect to="/login" />
  if (apenasBibliotecario && usuario?.papel !== 'BIBLIOTECARIO') return <Redirect to="/" />

  return (
    <div
      className="private-page-shell"
      onPointerOver={(event: ReactPointerEvent<HTMLDivElement>) => {
        if (isExitDrawerTarget(event.target)) setExitDrawerOpen(true)
      }}
      onPointerLeave={() => setExitDrawerOpen(false)}
    >
      <header
        className={`session-exit-header${exitDrawerOpen ? ' session-exit-header--open' : ''}`}
        aria-label="Ações da sessão"
      >
        <button type="button" className="session-exit-button" onClick={sair}>
          Sair
        </button>
      </header>
      {children}
    </div>
  )
}

function BibliotecarioOnly({ children }: { children: ReactNode }) {
  const usuario = useAuthStore((state) => state.usuario)
  if (usuario?.papel !== 'BIBLIOTECARIO') {
    return (
      <main className="simple-page">
        <p role="alert">Apenas bibliotecários podem registrar empréstimos.</p>
        <Link href="/emprestimos">Ver meus empréstimos →</Link>
      </main>
    )
  }
  return <>{children}</>
}

function AuthPage({ mode }: { mode: 'login' | 'cadastro' }) {
  const erro = useAuthStore((state) => state.erro)
  const carregandoLogin = useAuthStore((state) => state.carregandoLogin)
  const entrar = useAuthStore((state) => state.entrar)
  const limparErro = useAuthStore((state) => state.limparErro)
  const estado = useAuthStore((state) => state.estado)
  const [, navigate] = useLocation()
  const isLogin = mode === 'login'
  const [erroCadastro, setErroCadastro] = useState<string | null>(null)
  const [carregandoCadastro, setCarregandoCadastro] = useState(false)
  const [cadastroConcluido, setCadastroConcluido] = useState(false)

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const values = new FormData(event.currentTarget)
    const email = String(values.get('email') ?? '').trim()
    const password = String(values.get('senha') ?? '')
    limparErro()
    if (await entrar(email, password)) navigate('/')
  }

  async function handleCadastro(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const values = new FormData(event.currentTarget)
    const nome = String(values.get('nome') ?? '').trim()
    const matricula = String(values.get('matricula') ?? '').trim()
    const email = String(values.get('email') ?? '').trim()
    const telefone = String(values.get('telefone') ?? '').trim()
    const senha = String(values.get('senha') ?? '')

    setErroCadastro(null)
    setCarregandoCadastro(true)
    try {
      await apiRequest<UsuarioAutenticado>('/auth/registro', {
        method: 'POST',
        body: { nome, matricula, email, telefone: telefone || null, senha },
      })
      setCadastroConcluido(true)
    } catch (error) {
      setErroCadastro(
        error instanceof Error ? error.message : 'Não foi possível criar sua conta.',
      )
    } finally {
      setCarregandoCadastro(false)
    }
  }

  if (estado === 'authenticated') return <Redirect to="/" />
  if (estado === 'checking') {
    return <main className="simple-page" role="status">Verificando sessão...</main>
  }

  return (
    <main className={`auth-page auth-page--${isLogin ? 'login' : 'signup'}`}>
      <figure className="auth-quote">
        <blockquote>“{quote.text}”</blockquote>
        <figcaption>{quote.author}</figcaption>
      </figure>
      <section className="auth-card">
        <TypewriterTitle text={isLogin ? 'Que bom ter você de volta.' : 'Criar sua conta'} />
        <p className="auth-intro">
          {isLogin
            ? 'Acesse sua conta para continuar.'
            : 'Preencha seus dados para acessar a biblioteca.'}
        </p>
        <nav className="auth-tabs" aria-label="Autenticação">
          <Link href="/login" aria-current={isLogin ? 'page' : undefined} className={isLogin ? 'active' : undefined}>Entrar</Link>
          <Link href="/cadastro" aria-current={!isLogin ? 'page' : undefined} className={!isLogin ? 'active' : undefined}>Criar conta</Link>
        </nav>
        {isLogin ? (
          <form className="auth-form" onSubmit={handleSubmit}>
            <label htmlFor="email">Email</label>
            <input
              id="email"
              name="email"
              type="email"
              placeholder="voce@exemplo.com"
              autoComplete="email"
              required
              onChange={limparErro}
            />
            <label htmlFor="senha">Senha</label>
            <input
              id="senha"
              name="senha"
              type="password"
              placeholder="Sua senha"
              autoComplete="current-password"
              required
              onChange={limparErro}
            />
            {erro && <p className="auth-message" role="alert">{erro}</p>}
            <button type="submit" disabled={carregandoLogin}>
              {carregandoLogin ? 'Entrando...' : 'Entrar na biblioteca'} <span aria-hidden="true">→</span>
            </button>
          </form>
        ) : cadastroConcluido ? (
          <p className="auth-message auth-message--success" role="status">
            Conta criada. <Link href="/login">Entre com seu e-mail e senha.</Link>
          </p>
        ) : (
          <form className="auth-form" onSubmit={handleCadastro}>
            <label htmlFor="cadastro-nome">Nome</label>
            <input
              id="cadastro-nome"
              name="nome"
              type="text"
              autoComplete="name"
              required
            />
            <label htmlFor="cadastro-matricula">Matrícula</label>
            <input
              id="cadastro-matricula"
              name="matricula"
              type="text"
              autoComplete="off"
              required
            />
            <label htmlFor="cadastro-email">Email</label>
            <input
              id="cadastro-email"
              name="email"
              type="email"
              autoComplete="email"
              required
            />
            <label htmlFor="cadastro-telefone">Telefone <span>(opcional)</span></label>
            <input
              id="cadastro-telefone"
              name="telefone"
              type="tel"
              autoComplete="tel"
            />
            <label htmlFor="cadastro-senha">Senha</label>
            <input
              id="cadastro-senha"
              name="senha"
              type="password"
              autoComplete="new-password"
              required
            />
            {erroCadastro && <p className="auth-message" role="alert">{erroCadastro}</p>}
            <button type="submit" disabled={carregandoCadastro}>
              {carregandoCadastro ? 'Criando conta...' : 'Criar conta'} <span aria-hidden="true">→</span>
            </button>
          </form>
        )}
        {isLogin && <p className="auth-footnote">Ao continuar, você concorda com os termos de uso da Bibliofy.</p>}
      </section>
    </main>
  )
}

function DashboardPage() {
  const usuario = useAuthStore((state) => state.usuario)
  const isBibliotecario = usuario?.papel === 'BIBLIOTECARIO'
  const name = usuario?.nome || 'Bibliotecário'
  const firstName = name.trim().split(/\s+/)[0]
  const [showLoanSummary, setShowLoanSummary] = useState(false)
  const [showBookSummary, setShowBookSummary] = useState(false)
  const emprestimosArmazenados = useEmprestimoStore((state) => state.emprestimos)
  const emprestimosCarregadosPara = useEmprestimoStore((state) => state.carregadoPara)
  const livros = useLivroStore((state) => state.livros)
  const carregarLivros = useLivroStore((state) => state.carregarLivros)
  const livrosErro = useLivroStore((state) => state.erro)
  const emprestimos = emprestimosCarregadosPara === usuario?.codigo ? emprestimosArmazenados : []
  const livrosAtivos = livros.filter((livro) => !livro.arquivado)
  const exemplaresDisponiveis = livrosAtivos.reduce(
    (total, livro) => total + livro.quantidade_disponivel,
    0,
  )
  const exemplaresEmprestados = livrosAtivos.reduce(
    (total, livro) => total + livro.quantidade_emprestada,
    0,
  )
  const emprestimosAbertos = emprestimos.filter(
    (emprestimo) => !emprestimo.status.startsWith('DEVOLVIDO'),
  ).length
  const emprestimosAtrasados = emprestimos.filter(
    (emprestimo) => emprestimo.status === 'ATRASADO',
  ).length
  const exemplaresDisponiveisAnimados = useCountUp(exemplaresDisponiveis)
  const exemplaresEmprestadosAnimados = useCountUp(exemplaresEmprestados)
  const emprestimosAbertosAnimados = useCountUp(emprestimosAbertos)
  const emprestimosAtrasadosAnimados = useCountUp(emprestimosAtrasados)

  return (
    <main className="dashboard-page">
      <figure className="dashboard-quote"><blockquote>“{quote.text}”</blockquote><figcaption>{quote.author}</figcaption></figure>
      <section className="dashboard-content">
        <div className="welcome-row">
          <div>
            <h1>Olá, {firstName}.</h1>
            <p
              className="dashboard-subtitle"
              onMouseEnter={() => isBibliotecario && setShowLoanSummary(true)}
              onMouseLeave={() => setShowLoanSummary(false)}
            >
              <span>
                {isBibliotecario && showLoanSummary
                  ? `Você tem ${emprestimosAbertos} empréstimos abertos e ${emprestimosAtrasados} atrasados.`
                  : showBookSummary
                    ? isBibliotecario
                      ? `${exemplaresDisponiveis} exemplares disponíveis e ${exemplaresEmprestados} emprestados.`
                      : `${exemplaresDisponiveis} exemplares disponíveis no acervo.`
                    : isBibliotecario
                      ? 'Gerencie aqui seus empréstimos e livros.'
                      : 'Consulte o estoque da biblioteca.'}
              </span>
            </p>
          </div>
          <div className="stats" aria-label="Resumo da biblioteca">
            <div
              className="stat-pair stat-pair--books"
              role="group"
              aria-label={`${exemplaresDisponiveis} exemplares disponíveis e ${exemplaresEmprestados} emprestados`}
              onMouseEnter={() => setShowBookSummary(true)}
              onMouseLeave={() => setShowBookSummary(false)}
            >
              <span className="stat-number stat-number--green">{exemplaresDisponiveisAnimados}</span>
              <span className="stat-number stat-number--red">{exemplaresEmprestadosAnimados}</span>
            </div>
            {isBibliotecario && (
              <div
                className="stat-pair stat-pair--loans"
                role="group"
                aria-label={`${emprestimosAbertos} empréstimos abertos e ${emprestimosAtrasados} atrasados`}
                onMouseEnter={() => setShowLoanSummary(true)}
                onMouseLeave={() => setShowLoanSummary(false)}
              >
                <span className="stat-number stat-number--green">{emprestimosAbertosAnimados}</span>
                <span className="stat-number stat-number--red">{emprestimosAtrasadosAnimados}</span>
              </div>
            )}
          </div>
        </div>
        <div className="management-row">
          <div className="management-links">
            <Link href="/emprestimos">
              {isBibliotecario ? 'Gerenciar empréstimos' : 'Meus empréstimos'} <span>↗</span>
            </Link>
            <Link href="/livros">{isBibliotecario ? 'Gerenciar estoque' : 'Ver estoque'} <span>↗</span></Link>
          </div>
        </div>
        {livrosErro && (
          <div className="dashboard-load-error" role="alert">
            <p>Não foi possível carregar o resumo do acervo: {livrosErro}</p>
            <button type="button" onClick={() => void carregarLivros()}>Tentar novamente</button>
          </div>
        )}
        {isBibliotecario && (
          <div className="quick-actions">
            <Link href="/emprestimos/novo" className="action-card"><span className="action-plus">+</span><span>Registrar empréstimo</span></Link>
            <Link href="/livros?modal=cadastro" className="action-card"><span className="action-plus">+</span><span>Adicionar livro no<br /> catálogo</span></Link>
          </div>
        )}
      </section>
    </main>
  )
}

function SimplePage({ title, href, link }: { title: string; href: string; link: string }) {
  return <main className="simple-page"><p className="eyebrow">BIBLIOFY</p><h1>{title}</h1><Link href={href}>{link} →</Link></main>
}

export function AppRoutes() {
  return (
    <Switch>
      <Route path="/"><PrivatePage><DashboardPage /></PrivatePage></Route>
      <Route path="/login"><AuthPage mode="login" /></Route>
      <Route path="/cadastro"><AuthPage mode="cadastro" /></Route>
      <Route path="/bibliotecario"><PrivatePage><SimplePage title="Área do bibliotecário" href="/" link="Voltar ao painel" /></PrivatePage></Route>
      <Route path="/leitor"><PrivatePage><SimplePage title="Área do leitor" href="/" link="Voltar ao painel" /></PrivatePage></Route>
      <Route path="/livros/cadastrar"><PrivatePage apenasBibliotecario><Redirect to="/livros?modal=cadastro" /></PrivatePage></Route>
      <Route path="/livros"><PrivatePage><CatalogoLivros /></PrivatePage></Route>
      <Route path="/emprestimos/novo">
        <PrivatePage>
          <BibliotecarioOnly><EmprestimosPage /></BibliotecarioOnly>
        </PrivatePage>
      </Route>
      <Route path="/emprestimos"><PrivatePage><GerenciarEmprestimosPage /></PrivatePage></Route>
      <Route><SimplePage title="Página não encontrada" href="/" link="Voltar ao painel" /></Route>
    </Switch>
  )
}
