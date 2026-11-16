
import { Link, Route, Switch } from 'wouter'

function HomePage() {
  return (
    <main>
      <h1>Bibliofy</h1>
      <p>Sistema de gerenciamento de biblioteca.</p>

      <nav>
        <ul>
          <li><Link href="/login">Login</Link></li>
          <li><Link href="/cadastro">Cadastro</Link></li>
          <li><Link href="/bibliotecario">Área do bibliotecário</Link></li>
          <li><Link href="/leitor">Área do leitor</Link></li>
          <li><Link href="/livros">Repositório de livros</Link></li>
          <li><Link href="/livros/cadastrar">Cadastrar livros</Link></li>
          <li><Link href="/emprestimos">Empréstimos</Link></li>
          <li><Link href="/emprestimos/novo">Novo empréstimo</Link></li>
        </ul>
      </nav>
    </main>
  )
}

function LoginPage() {
  return <main><h1>Login</h1><Link href="/">Voltar ao início</Link></main>
}

function CadastroPage() {
  return <main><h1>Cadastro</h1><Link href="/">Voltar ao início</Link></main>
}

function BibliotecarioPage() {
  return <main><h1>Área do bibliotecário</h1><Link href="/">Voltar ao início</Link></main>
}

function LeitorPage() {
  return <main><h1>Área do leitor</h1><Link href="/">Voltar ao início</Link></main>
}

function LivrosPage() {
  return <main><h1>Repositório de livros</h1><Link href="/livros/cadastrar">Cadastrar livro</Link></main>
}

function CadastroLivroPage() {
  return <main><h1>Cadastro de livros</h1><Link href="/livros">Voltar aos livros</Link></main>
}

function EmprestimosPage() {
  return <main><h1>Consulta de empréstimos</h1><Link href="/emprestimos/novo">Registrar empréstimo</Link></main>
}

function NovoEmprestimoPage() {
  return <main><h1>Novo empréstimo</h1><Link href="/emprestimos">Voltar aos empréstimos</Link></main>
}

function NotFoundPage() {
  return <main><h1>Página não encontrada</h1><Link href="/">Voltar ao início</Link></main>
}

export function AppRoutes() {
  return (
    <Switch>
      <Route path="/" component={HomePage} />
      <Route path="/login" component={LoginPage} />
      <Route path="/cadastro" component={CadastroPage} />
      <Route path="/bibliotecario" component={BibliotecarioPage} />
      <Route path="/leitor" component={LeitorPage} />
      <Route path="/livros" component={LivrosPage} />
      <Route path="/livros/cadastrar" component={CadastroLivroPage} />
      <Route path="/emprestimos" component={EmprestimosPage} />
      <Route path="/emprestimos/novo" component={NovoEmprestimoPage} />
      <Route component={NotFoundPage} />
    </Switch>
  )
}
