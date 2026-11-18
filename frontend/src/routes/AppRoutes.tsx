import { useState, type FormEvent, type ReactNode } from 'react'
import { Link, Redirect, Route, Switch, useLocation } from 'wouter'

const quotes = [
  { text: 'Um leitor vive mil vidas antes de morrer. O homem que nunca lê vive apenas uma.', author: 'J.R.R. Martin' },
  { text: 'Quem lê muito e anda muito, vê muito e sabe muito.', author: 'Miguel de Cervantes' },
  { text: 'Um livro é um sonho que você segura nas mãos.', author: 'Neil Gaiman' },
]
const quote = quotes[0]
const demoUser = { name: 'Ana Bibliotecária', email: 'demo@bibliofy.com', password: 'bibliofy123' }

function PrivatePage({ children }: { children: ReactNode }) {
  return window.localStorage.getItem('access_token') ? children : <Redirect to="/cadastro" />
}

function AuthPage({ mode }: { mode: 'login' | 'cadastro' }) {
  const [message, setMessage] = useState('')
  const [, navigate] = useLocation()
  const isLogin = mode === 'login'

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const values = new FormData(event.currentTarget)
    const email = String(values.get('email') ?? '').trim()
    const password = String(values.get('senha') ?? '')
    if (isLogin && (email !== demoUser.email || password !== demoUser.password)) {
      setMessage('Email ou senha incorretos. Use as credenciais de demonstração abaixo.')
      return
    }
    const name = isLogin
      ? demoUser.name
      : String(values.get('nome') ?? '').trim()

    window.localStorage.setItem('bibliofy_user', name)
    window.localStorage.setItem('access_token', `local-${Date.now()}`)
    navigate('/')
  }

  return (
    <main className={`auth-page auth-page--${isLogin ? 'login' : 'signup'}`}>
      <figure className="auth-quote">
        <blockquote>“{quote.text}”</blockquote>
        <figcaption>{quote.author}</figcaption>
      </figure>
      <section className="auth-card">
        <h1>{isLogin ? 'Que bom ter você de volta.' : 'Criar sua conta'}</h1>
        <p className="auth-intro">{isLogin ? 'Acesse sua conta para continuar.' : 'Preencha seus dados para começar.'}</p>
        <nav className="auth-tabs" aria-label="Autenticação">
          <Link href="/login" aria-current={isLogin ? 'page' : undefined} className={isLogin ? 'active' : undefined}>Entrar</Link>
          <Link href="/cadastro" aria-current={!isLogin ? 'page' : undefined} className={!isLogin ? 'active' : undefined}>Criar conta</Link>
        </nav>
        <form className="auth-form" onSubmit={handleSubmit}>
          {!isLogin && <>
            <label htmlFor="nome">Seu nome</label>
            <input id="nome" name="nome" type="text" placeholder="Como podemos chamar você?" autoComplete="name" required />
            <label htmlFor="matricula">Matrícula</label>
            <input id="matricula" name="matricula" type="text" placeholder="Digite sua matrícula" required />
          </>}
          <label htmlFor="email">Email</label>
          <input id="email" name="email" type="email" placeholder="voce@exemplo.com" autoComplete="email" required />
          {!isLogin && <>
            <label htmlFor="telefone">Telefone <span>(opcional)</span></label>
            <input id="telefone" name="telefone" type="tel" placeholder="(00) 00000-0000" autoComplete="tel" />
          </>}
          <label htmlFor="senha">Senha</label>
          <input id="senha" name="senha" type="password" placeholder="Mínimo de 8 caracteres" autoComplete={isLogin ? 'current-password' : 'new-password'} required />
          {message && <p className="auth-message" role="status">{message}</p>}
          <button type="submit">{isLogin ? 'Entrar na biblioteca' : 'Criar minha conta'} <span aria-hidden="true">→</span></button>
        </form>
        <p className="auth-footnote">Ao continuar, você concorda com os termos de uso da Bibliofy.</p>
      </section>
    </main>
  )
}

function DashboardPage() {
  const name = window.localStorage.getItem('bibliofy_user') || 'Bibliotecário'
  const firstName = name.trim().split(/\s+/)[0]
  return (
    <main className="dashboard-page">
      <figure className="dashboard-quote"><blockquote>“{quote.text}”</blockquote><figcaption>{quote.author}</figcaption></figure>
      <section className="dashboard-content">
        <div className="welcome-row">
          <div><h1>Olá, {firstName}.</h1><p className="dashboard-subtitle">Gerencie aqui seus empréstimos e livros.</p></div>
          <div className="stats" aria-label="Resumo da biblioteca">
            <div className="stat-pair" role="group" aria-label="234 empréstimos e 150 em atraso"><span className="stat-number stat-number--green">234</span><span className="stat-number stat-number--red">150</span></div>
            <div className="stat-pair" role="group" aria-label="100 livros e 50 disponíveis"><span className="stat-number stat-number--green">100</span><span className="stat-number stat-number--red">50</span></div>
          </div>
        </div>
        <div className="management-row">
          <div className="management-links"><Link href="/emprestimos">Gerenciar empréstimos <span>↗</span></Link><Link href="/livros">Gerenciar estoque <span>↗</span></Link></div>
        </div>
        <div className="quick-actions">
          <Link href="/emprestimos/novo" className="action-card"><span className="action-plus">+</span><span>Registrar empréstimo</span></Link>
          <Link href="/livros/cadastrar" className="action-card"><span className="action-plus">+</span><span>Adicionar livro no<br /> catálogo</span></Link>
        </div>
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
      <Route path="/livros/cadastrar"><PrivatePage><SimplePage title="Adicionar livro ao catálogo" href="/livros" link="Voltar ao estoque" /></PrivatePage></Route>
      <Route path="/livros"><PrivatePage><SimplePage title="Estoque de livros" href="/" link="Voltar ao painel" /></PrivatePage></Route>
      <Route path="/emprestimos/novo"><PrivatePage><SimplePage title="Registrar empréstimo" href="/emprestimos" link="Ver empréstimos" /></PrivatePage></Route>
      <Route path="/emprestimos"><PrivatePage><SimplePage title="Empréstimos" href="/" link="Voltar ao painel" /></PrivatePage></Route>
      <Route><SimplePage title="Página não encontrada" href="/" link="Voltar ao painel" /></Route>
    </Switch>
  )
}
