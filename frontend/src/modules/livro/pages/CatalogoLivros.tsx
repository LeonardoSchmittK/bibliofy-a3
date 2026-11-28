import { useEffect, useMemo, useState, type FormEvent } from 'react'
import { Link, useLocation } from 'wouter'
import { useAuthStore } from '../../auth/store/authStore'
import { useLivroStore } from '../store/livroStore'
import type { Livro, LivroDados } from '../types/livro'

const camposVazios: LivroDados = {
  isbn: '',
  nome: '',
  autor: '',
  editora: '',
  genero: 'Ficção',
  data_lancamento: '',
  quantidade_total: 1,
}

function resumoData(data: string) {
  if (!data) return '—'
  return new Date(`${data}T00:00:00`).toLocaleDateString('pt-BR', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  })
}

function LivroForm({
  livro,
  onCancel,
  onSave,
  salvando,
}: {
  livro?: Livro
  onCancel?: () => void
  onSave: (dados: LivroDados) => void | Promise<void>
  salvando: boolean
}) {
  const [dados, setDados] = useState<LivroDados>(
    livro
      ? {
          isbn: livro.isbn,
          nome: livro.nome,
          autor: livro.autor,
          editora: livro.editora,
          genero: livro.genero,
          data_lancamento: livro.data_lancamento,
          quantidade_total: livro.quantidade_total,
        }
      : camposVazios,
  )

  function atualizarCampo(campo: keyof LivroDados, valor: string) {
    setDados((atuais) => ({
      ...atuais,
      [campo]: campo === 'quantidade_total' ? Number(valor) : valor,
    }))
  }

  async function enviar(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    await onSave({ ...dados, nome: dados.nome.trim(), isbn: dados.isbn.trim() })
  }

  return (
    <form className="book-form" onSubmit={enviar}>
      <div className="book-form-grid">
        <label>
          Título do livro
          <input
            required
            maxLength={200}
            value={dados.nome}
            onChange={(event) => atualizarCampo('nome', event.target.value)}
            placeholder="Digite o título"
          />
        </label>
        <label>
          Editora
          <input
            required
            maxLength={150}
            value={dados.editora}
            onChange={(event) => atualizarCampo('editora', event.target.value)}
            placeholder="Nome da editora"
          />
        </label>
        <label>
          Autor
          <input
            required
            maxLength={150}
            value={dados.autor}
            onChange={(event) => atualizarCampo('autor', event.target.value)}
            placeholder="Nome do autor"
          />
        </label>
        <label>
          Data de publicação
          <input
            required
            type="date"
            value={dados.data_lancamento}
            onChange={(event) => atualizarCampo('data_lancamento', event.target.value)}
          />
        </label>
        <label>
          Categoria
          <select
            value={dados.genero}
            onChange={(event) => atualizarCampo('genero', event.target.value)}
          >
            <option>Ficção</option>
            <option>Não ficção</option>
            <option>Infantil</option>
            <option>Acadêmico</option>
            <option>Literatura</option>
          </select>
        </label>
        <label>
          Quantidade total
          <input
            required
            min={1}
            type="number"
            value={dados.quantidade_total}
            onChange={(event) => atualizarCampo('quantidade_total', event.target.value)}
          />
        </label>
        <label className="book-form-isbn">
          ISBN
          <input
            required
            maxLength={20}
            value={dados.isbn}
            onChange={(event) => atualizarCampo('isbn', event.target.value)}
            placeholder="ISBN-10 ou ISBN-13"
          />
        </label>
      </div>
      <div className="book-form-actions">
        {onCancel && (
          <button type="button" className="book-button book-button--secondary" onClick={onCancel}>
            Cancelar
          </button>
        )}
        <button type="submit" className="book-button" disabled={salvando}>
          {salvando ? 'Salvando...' : livro ? 'Salvar alterações' : 'Cadastrar livro'}
        </button>
      </div>
    </form>
  )
}

export function CatalogoLivros() {
  const livros = useLivroStore((state) => state.livros)
  const adicionarLivro = useLivroStore((state) => state.adicionarLivro)
  const atualizarLivro = useLivroStore((state) => state.atualizarLivro)
  const arquivarLivro = useLivroStore((state) => state.arquivarLivro)
  const carregarLivros = useLivroStore((state) => state.carregarLivros)
  const carregando = useLivroStore((state) => state.carregando)
  const erro = useLivroStore((state) => state.erro)
  const limparErro = useLivroStore((state) => state.limparErro)
  const usuario = useAuthStore((state) => state.usuario)
  const podeEditar = usuario?.papel === 'BIBLIOTECARIO'
  const [busca, setBusca] = useState('')
  const [generoAtivo, setGeneroAtivo] = useState('Todos')
  const [disponibilidade, setDisponibilidade] = useState('Todas')
  const [livroEditando, setLivroEditando] = useState<Livro>()
  const [livroArquivando, setLivroArquivando] = useState<Livro>()
  const [cadastroAberto, setCadastroAberto] = useState(
    () => podeEditar && new URLSearchParams(window.location.search).get('modal') === 'cadastro',
  )
  const [salvando, setSalvando] = useState(false)
  const [, navigate] = useLocation()
  const ativos = useMemo(() => livros.filter((livro) => !livro.arquivado), [livros])
  const filtrados = useMemo(() => {
    const termo = busca.trim().toLocaleLowerCase('pt-BR')
    return ativos.filter((livro) => {
      const combinaBusca = !termo
        || [livro.nome, livro.autor, livro.isbn].some((campo) =>
          campo.toLocaleLowerCase('pt-BR').includes(termo),
        )
      const combinaGenero = generoAtivo === 'Todos' || livro.genero === generoAtivo
      const combinaDisponibilidade = disponibilidade === 'Todas'
        || (disponibilidade === 'Disponíveis' && livro.quantidade_disponivel > 0)
        || (disponibilidade === 'Indisponíveis' && livro.quantidade_disponivel === 0)
      return combinaBusca && combinaGenero && combinaDisponibilidade
    })
  }, [ativos, busca, disponibilidade, generoAtivo])
  const generos = useMemo(
    () => ['Todos', ...new Set(ativos.map((livro) => livro.genero))],
    [ativos],
  )
  const modalAberto = podeEditar && Boolean(livroEditando || livroArquivando || cadastroAberto)

  function fecharModal() {
    setLivroEditando(undefined)
    setLivroArquivando(undefined)
    setCadastroAberto(false)
    limparErro()
    if (new URLSearchParams(window.location.search).has('modal')) navigate('/livros')
  }

  useEffect(() => {
    if (!modalAberto) return
    function fecharComEscape(event: KeyboardEvent) {
      if (event.key === 'Escape') {
        setLivroEditando(undefined)
        setLivroArquivando(undefined)
        setCadastroAberto(false)
        if (new URLSearchParams(window.location.search).has('modal')) navigate('/livros')
      }
    }
    window.addEventListener('keydown', fecharComEscape)
    return () => window.removeEventListener('keydown', fecharComEscape)
  }, [modalAberto, navigate])

  const totalExemplares = ativos.reduce((total, livro) => total + livro.quantidade_total, 0)
  const totalDisponiveis = ativos.reduce((total, livro) => total + livro.quantidade_disponivel, 0)
  const totalEmprestados = ativos.reduce((total, livro) => total + livro.quantidade_emprestada, 0)

  async function salvarEdicao(dados: LivroDados) {
    if (!livroEditando) return
    setSalvando(true)
    const salvo = await atualizarLivro(livroEditando.codigo, dados)
    setSalvando(false)
    if (salvo) fecharModal()
  }

  async function salvarCadastro(dados: LivroDados) {
    setSalvando(true)
    const salvo = await adicionarLivro(dados)
    setSalvando(false)
    if (salvo) fecharModal()
  }

  function arquivar(livro: Livro) {
    setLivroArquivando(livro)
  }

  return (
    <main className="book-page">
      <header className="book-page-header">
        <div>
          <Link className="book-back-link" href="/">← Voltar ao painel</Link>
          <h1>Catálogo de Livros</h1>
          <p className="book-page-subtitle">Encontre e consulte os livros da biblioteca.</p>
        </div>
        {podeEditar && (
          <button
            type="button"
            className="book-button book-add-button"
            onClick={() => setCadastroAberto(true)}
          >
            <span aria-hidden="true">+</span> Cadastrar livro
          </button>
        )}
      </header>

      <div className="book-toolbar">
        <label className="book-search">
          <span aria-hidden="true">⌕</span>
          <input
            type="search"
            value={busca}
            onChange={(event) => setBusca(event.target.value)}
            placeholder="Pesquisar livro..."
            aria-label="Pesquisar por título, autor ou ISBN"
          />
        </label>
        <div className="book-categories" aria-label="Filtrar por categoria">
          {generos.map((genero) => (
            <button
              key={genero}
              type="button"
              className={`book-category ${generoAtivo === genero ? 'active' : ''}`}
              onClick={() => setGeneroAtivo(genero)}
              aria-pressed={generoAtivo === genero}
            >
              {genero}
            </button>
          ))}
        </div>
      </div>

      <div className="book-catalog-layout">
        <section className="book-list" aria-label="Livros do catálogo">
          {erro && !modalAberto && <p className="book-api-error" role="alert">{erro}</p>}
          {carregando && livros.length === 0 ? (
            <div className="book-empty" role="status">Carregando livros...</div>
          ) : erro && livros.length === 0 && !modalAberto ? (
            <div className="book-empty">
              <p className="book-api-error" role="alert">{erro}</p>
              <button type="button" className="book-button" onClick={() => void carregarLivros()}>
                Tentar novamente
              </button>
            </div>
          ) : filtrados.length === 0 ? (
            <div className="book-empty">
              <span aria-hidden="true">⌕</span>
              <h2>{livros.length ? 'Nenhum livro encontrado' : 'Nenhum livro cadastrado'}</h2>
              <p>
                {livros.length
                  ? 'Tente mudar a busca ou escolher outra categoria.'
                  : 'Os livros cadastrados aparecerão aqui.'}
              </p>
            </div>
          ) : (
            filtrados.map((livro) => (
              <article className="book-card" key={livro.codigo}>
                <div className="book-card-heading">
                  <div>
                    <h2>{livro.nome}</h2>
                    <p className="book-card-author">por {livro.autor}</p>
                  </div>
                  <div className="book-card-tools">
                    <span className={`book-status ${livro.quantidade_disponivel ? '' : 'unavailable'}`}>
                      {livro.quantidade_disponivel ? 'Disponível' : 'Indisponível'}
                    </span>
                    {podeEditar && (
                      <div className="book-card-actions">
                        <button
                          type="button"
                          aria-label={`Editar ${livro.nome}`}
                          title="Editar livro"
                          onClick={() => setLivroEditando(livro)}
                        >
                          <svg viewBox="0 0 16 16" aria-hidden="true">
                            <path d="m11.4 2.1 2.5 2.5M2.5 13.5l2.2-.5 8.5-8.5a1.4 1.4 0 0 0-2-2l-8.5 8.5-.2 2.5Z" />
                          </svg>
                        </button>
                        <button
                          type="button"
                          aria-label={`Arquivar ${livro.nome}`}
                          title="Arquivar livro"
                          onClick={() => arquivar(livro)}
                        >
                          ×
                        </button>
                      </div>
                    )}
                  </div>
                </div>
                <div className="book-card-details">
                  <div><span>ID</span><strong>{livro.codigo}</strong></div>
                  <div><span>EDITORA</span><strong>{livro.editora}</strong></div>
                  <div><span>PUBLICAÇÃO</span><strong>{resumoData(livro.data_lancamento)}</strong></div>
                  <div><span>ISBN</span><strong>{livro.isbn}</strong></div>
                  <div><span>EXEMPLARES</span><strong>{livro.quantidade_total}</strong></div>
                </div>
                <div className="book-card-stock">
                  <span>{livro.quantidade_disponivel} disponíveis</span>
                  <span>{livro.quantidade_emprestada} emprestados</span>
                  <div className="book-stock-track">
                    <span
                      style={{
                        width: `${livro.quantidade_total
                          ? (livro.quantidade_disponivel / livro.quantidade_total) * 100
                          : 0}%`,
                      }}
                    />
                  </div>
                </div>
              </article>
            ))
          )}
        </section>

        <aside className="book-sidebar">
          <section className="book-summary-card">
            <p className="book-sidebar-title">Resumo do acervo</p>
            <div className="book-summary-line"><span>Títulos</span><strong>{ativos.length}</strong></div>
            <div className="book-summary-line"><span>Exemplares</span><strong>{totalExemplares}</strong></div>
            <div className="book-summary-line"><span>Disponíveis</span><strong>{totalDisponiveis}</strong></div>
            <div className="book-summary-line"><span>Emprestados</span><strong>{totalEmprestados}</strong></div>
            <strong className="book-summary-total">{totalExemplares} exemplares</strong>
          </section>
          <section className="book-summary-card book-availability-filter" aria-label="Filtrar por disponibilidade">
            <p className="book-sidebar-title">Disponibilidade</p>
            {['Todas', 'Disponíveis', 'Indisponíveis'].map((filtro) => (
              <button
                key={filtro}
                type="button"
                className={`book-availability-option ${disponibilidade === filtro ? 'active' : ''}`}
                onClick={() => setDisponibilidade(filtro)}
                aria-pressed={disponibilidade === filtro}
              >
                <span>{filtro}</span>
                <span>
                  {filtro === 'Todas'
                    ? ativos.length
                    : ativos.filter((livro) =>
                        filtro === 'Disponíveis'
                          ? livro.quantidade_disponivel > 0
                          : livro.quantidade_disponivel === 0,
                      ).length}
                </span>
              </button>
            ))}
          </section>
          <section className="book-summary-card book-category-summary">
            <p className="book-sidebar-title">Categorias</p>
            {ativos.length === 0 ? (
              <p className="book-no-category">Sem categorias cadastradas.</p>
            ) : (
              generos.slice(1).map((genero) => {
                const quantidade = ativos.filter((livro) => livro.genero === genero).length
                const percentual = quantidade / ativos.length * 100
                return (
                  <button
                    className="book-category-stat"
                    key={genero}
                    type="button"
                    onClick={() => setGeneroAtivo(genero)}
                  >
                    <span>{genero}</span>
                    <strong>{percentual.toFixed(0)}%</strong>
                    <span className="book-category-track">
                      <span style={{ width: `${percentual}%` }} />
                    </span>
                  </button>
                )
              })
            )}
          </section>
        </aside>
      </div>

      {podeEditar && modalAberto && (
        <dialog
          open
          className="book-modal-backdrop"
          aria-labelledby="book-modal-title"
          onClick={(event) => {
            if (event.target === event.currentTarget) fecharModal()
          }}
        >
          <section className="book-modal">
            <button
              className="book-modal-close"
              type="button"
              aria-label={
                livroArquivando
                  ? 'Fechar confirmação de arquivamento'
                  : livroEditando
                    ? 'Fechar edição'
                    : 'Fechar cadastro'
              }
              onClick={fecharModal}
            >
              ×
            </button>
            <h2 id="book-modal-title">
              {livroArquivando ? 'Arquivar livro' : livroEditando ? 'Editar livro' : 'Cadastrar novo exemplar'}
            </h2>
            {erro && <p className="book-api-error" role="alert">{erro}</p>}
            {livroArquivando ? (
              <div className="book-archive-confirmation">
                <p>
                  Deseja arquivar <strong>{livroArquivando.nome}</strong>? O livro deixará de aparecer
                  no catálogo.
                </p>
                <div className="book-form-actions">
                  <button type="button" className="book-button book-button--secondary" onClick={fecharModal}>
                    Cancelar
                  </button>
                  <button
                    type="button"
                    className="book-button book-button--archive"
                    disabled={salvando}
                    onClick={async () => {
                      setSalvando(true)
                      const arquivado = await arquivarLivro(livroArquivando.codigo)
                      setSalvando(false)
                      if (arquivado) fecharModal()
                    }}
                  >
                    {salvando ? 'Arquivando...' : 'Arquivar livro'}
                  </button>
                </div>
              </div>
            ) : (
              <LivroForm
                key={livroEditando?.codigo ?? 'cadastro'}
                livro={livroEditando}
                onCancel={fecharModal}
                onSave={livroEditando ? salvarEdicao : salvarCadastro}
                salvando={salvando}
              />
            )}
          </section>
        </dialog>
      )}
    </main>
  )
}
