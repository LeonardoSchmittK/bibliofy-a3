import { useEffect, useMemo, useState } from 'react'
import { Link, useLocation } from 'wouter'
import { getRandomQuote } from '../../../shared/utils/quotes'
import { useAuthStore } from '../../auth/store/authStore'
import {
  obterFimImpedimentoAtivo,
  obterImpedimentoAtivo,
  useEmprestimoStore,
} from '../store/emprestimoStore'
import { useLeitorStore } from '../../leitor/store/leitorStore'
import { useLivroStore } from '../../livro/store/livroStore'
import type { Leitor } from '../../leitor/types/leitor'
import type { Livro } from '../../livro/types/livro'

const quote = getRandomQuote()
type LoanPicker = 'book' | 'reader' | null

function normalizarBusca(value: string): string {
  return value
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLocaleLowerCase('pt-BR')
    .trim()
}

function formatarData(data: Date): string {
  return new Intl.DateTimeFormat('pt-BR').format(data)
}

function formatarDataISO(dataISO: string): string {
  const [ano, mes, dia] = dataISO.split('-').map(Number)
  return formatarData(new Date(ano, mes - 1, dia))
}

function obterDataDeDevolucao(): string {
  const data = new Date()
  data.setDate(data.getDate() + 25)
  return formatarData(data)
}

export function EmprestimosPage() {
  const [, navigate] = useLocation()
  const usuarioCodigo = useAuthStore((state) => state.usuario?.codigo)
  const livros = useLivroStore((state) => state.livros)
  const leitoresArmazenados = useLeitorStore((state) => state.leitores)
  const emprestimosCarregadosPara = useEmprestimoStore((state) => state.carregadoPara)
  const emprestimosArmazenados = useEmprestimoStore((state) => state.emprestimos)
  const impedimentosArmazenados = useEmprestimoStore((state) => state.impedimentos)
  const emprestimosErro = useEmprestimoStore((state) => state.erro)
  const carregandoEmprestimos = useEmprestimoStore((state) => state.carregando)
  const salvandoEmprestimo = useEmprestimoStore((state) => state.salvando)
  const carregarEmprestimos = useEmprestimoStore((state) => state.carregarEmprestimos)
  const registrarEmprestimo = useEmprestimoStore((state) => state.registrarEmprestimo)
  const [openPicker, setOpenPicker] = useState<LoanPicker>(null)
  const [bookQuery, setBookQuery] = useState('')
  const [readerQuery, setReaderQuery] = useState('')
  const [selectedBook, setSelectedBook] = useState<Livro | null>(null)
  const [selectedReader, setSelectedReader] = useState<Leitor | null>(null)
  const [showConfirmation, setShowConfirmation] = useState(false)
  const [showPenalties, setShowPenalties] = useState(false)
  const [message, setMessage] = useState('')
  const leitoresCarregando = useLeitorStore((state) => state.carregando)
  const leitoresCarregados = useLeitorStore((state) => state.carregado)
  const leitoresCarregadosPara = useLeitorStore((state) => state.carregadoPara)
  const leitoresErro = useLeitorStore((state) => state.erro)
  const carregarLeitores = useLeitorStore((state) => state.carregarLeitores)
  const carregarLivros = useLivroStore((state) => state.carregarLivros)
  const dadosEmprestimoProntos = emprestimosCarregadosPara === usuarioCodigo
  const dadosLeitoresProntos = leitoresCarregadosPara === usuarioCodigo
  const emprestimos = dadosEmprestimoProntos ? emprestimosArmazenados : []
  const impedimentos = dadosEmprestimoProntos ? impedimentosArmazenados : []

  useEffect(() => {
    if (!leitoresCarregados || leitoresCarregadosPara !== usuarioCodigo) void carregarLeitores()
  }, [carregarLeitores, leitoresCarregados, leitoresCarregadosPara, usuarioCodigo])

  const availableBooks = useMemo(
    () =>
      livros.filter(
        (livro) =>
          !livro.arquivado &&
          livro.quantidade_disponivel > 0 &&
          normalizarBusca(`${livro.nome} ${livro.codigo} ${livro.autor}`).includes(
            normalizarBusca(bookQuery),
          ),
      ),
    [bookQuery, livros],
  )

  const filteredReaders = useMemo(() => {
    const leitores = dadosLeitoresProntos ? leitoresArmazenados : []
    return leitores.filter((leitor) =>
      normalizarBusca(`${leitor.nome} ${leitor.codigo}`).includes(
        normalizarBusca(readerQuery),
      ),
    )
  }, [dadosLeitoresProntos, leitoresArmazenados, readerQuery])

  function selecionarLivro(livro: Livro) {
    setSelectedBook(livro)
    setOpenPicker(null)
    setMessage('')
    if (selectedReader) setShowConfirmation(true)
  }

  function selecionarLeitor(leitor: Leitor) {
    if (obterImpedimentoAtivo(impedimentos, leitor.codigo)) {
      const fimImpedimento = obterFimImpedimentoAtivo(impedimentos, leitor.codigo)
      setOpenPicker(null)
      setMessage(
        `Este leitor está impedido de realizar empréstimos até ${
          fimImpedimento ? formatarDataISO(fimImpedimento) : 'o fim do período'
        }.`,
      )
      return
    }

    if (emprestimosDoLeitor(leitor.codigo).abertos > 0) {
      setOpenPicker(null)
      setMessage('Este leitor já possui um empréstimo em andamento.')
      return
    }

    setSelectedReader(leitor)
    setOpenPicker(null)
    setMessage('')
    if (selectedBook) setShowConfirmation(true)
  }

  async function confirmarEmprestimo() {
    if (!selectedBook || !selectedReader) return

    if (obterImpedimentoAtivo(impedimentos, selectedReader.codigo)) {
      const fimImpedimento = obterFimImpedimentoAtivo(impedimentos, selectedReader.codigo)
      setShowConfirmation(false)
      setMessage(
        `Este leitor está impedido de realizar empréstimos até ${
          fimImpedimento ? formatarDataISO(fimImpedimento) : 'o fim do período'
        }.`,
      )
      return
    }

    const livroAtual = useLivroStore
      .getState()
      .livros.find((livro) => livro.codigo === selectedBook.codigo)
    if (!livroAtual || livroAtual.quantidade_disponivel <= 0 || livroAtual.arquivado) {
      setShowConfirmation(false)
      setSelectedBook(null)
      setMessage('Este exemplar não está mais disponível. Escolha outro livro.')
      return
    }

    const registrado = await registrarEmprestimo({
      livroId: selectedBook.codigo,
      livroNome: selectedBook.nome,
      leitorId: selectedReader.codigo,
      leitorNome: selectedReader.nome,
    })
    if (!registrado) {
      setShowConfirmation(false)
      setMessage(
        useEmprestimoStore.getState().erro
          || 'Não foi possível registrar o empréstimo. Verifique se o leitor está impedido.',
      )
      return
    }

    await carregarLivros()
    navigate('/emprestimos')
  }

  function emprestimosDoLeitor(leitorCodigo: string) {
    const doLeitor = emprestimos.filter(
      (emprestimo) => emprestimo.leitorId === leitorCodigo,
    )
    return {
      abertos: doLeitor.filter(
        (emprestimo) =>
          emprestimo.status === 'EM_ANDAMENTO' || emprestimo.status === 'ATRASADO',
      ).length,
      atrasados: doLeitor.filter((emprestimo) => emprestimo.status === 'ATRASADO').length,
    }
  }

  return (
    <main className="loan-page">
      <figure className="loan-quote">
        <blockquote>“{quote.text}”</blockquote>
        <figcaption>{quote.author}</figcaption>
      </figure>

      <section className="loan-content loan-content--selection">
        <Link href="/" className="loan-home-link">← Voltar para a tela inicial</Link>
        <header className="loan-header">
          <h1>Qual livro emprestar e para quem?</h1>
          <p>
            Um empréstimo tem prazo automático de 25 dias.{' '}
            <button
              type="button"
              className="loan-policy-link"
              onClick={() => setShowPenalties(true)}
            >
              Consultar penalidades
            </button>
          </p>
        </header>

        <div className="loan-selection-grid">
          <button
            type="button"
            className="loan-picker"
            aria-haspopup="dialog"
            onClick={() => setOpenPicker('book')}
          >
            <img className="loan-picker-illustration" src="/emprestimo-livro.svg" alt="" />
            <span className="loan-picker-title" role="heading" aria-level={2}>
              Escolha o exemplar
            </span>
            {selectedBook && (
              <span className="loan-picker-selected">{selectedBook.nome}</span>
            )}
          </button>

          <img
            className="loan-arrow-illustration"
            src="/emprestimo-seta.svg"
            alt=""
            aria-hidden="true"
          />

          <button
            type="button"
            className="loan-picker"
            aria-haspopup="dialog"
            onClick={() => setOpenPicker('reader')}
          >
            <img className="loan-picker-illustration" src="/emprestimo-leitor.svg" alt="" />
            <span className="loan-picker-title" role="heading" aria-level={2}>
              Escolha o leitor
            </span>
            {selectedReader && (
              <span className="loan-picker-selected">{selectedReader.nome}</span>
            )}
          </button>
        </div>

        {message && <p className="loan-selection-message" role="status">{message}</p>}
        {(leitoresErro || emprestimosErro) && !message && (
          <div className="loan-selection-message" role="alert">
            <p>{leitoresErro || emprestimosErro}</p>
            <button
              type="button"
              className="book-button book-button--secondary"
              onClick={() => {
                if (leitoresErro) void carregarLeitores()
                if (emprestimosErro) void carregarEmprestimos()
              }}
            >
              Tentar novamente
            </button>
          </div>
        )}
        {(leitoresCarregando || carregandoEmprestimos) && (
          <p className="loan-selection-message" role="status">Carregando dados de empréstimos...</p>
        )}
      </section>

      {openPicker && (
        <div
          className="book-modal-backdrop loan-picker-backdrop"
          onMouseDown={(event) => {
            if (event.target === event.currentTarget) setOpenPicker(null)
          }}
        >
          <section
            className="book-modal loan-picker-modal"
            role="dialog"
            aria-modal="true"
            aria-labelledby="loan-picker-modal-title"
          >
            <button
              type="button"
              className="book-modal-close loan-policy-close"
              aria-label="Fechar"
              onClick={() => setOpenPicker(null)}
            >
              ×
            </button>
            <h2 id="loan-picker-modal-title">
              {openPicker === 'book' ? 'Escolha o exemplar' : 'Escolha o leitor'}
            </h2>
            {openPicker === 'book' ? (
              <>
                <label className="loan-search">
                  <span aria-hidden="true">⌕</span>
                  <input
                    type="search"
                    aria-label="Pesquisar livro"
                    placeholder="Pesquisar livro"
                    value={bookQuery}
                    onChange={(event) => setBookQuery(event.target.value)}
                  />
                </label>
                <ul className="loan-picker-options">
                  {availableBooks.map((livro) => (
                    <li key={livro.codigo}>
                      <button
                        type="button"
                        className="loan-picker-option"
                        aria-pressed={selectedBook?.codigo === livro.codigo}
                        onClick={() => selecionarLivro(livro)}
                      >
                        <span>{livro.nome}</span>
                        <span className="loan-option-code">{livro.codigo}</span>
                        {selectedBook?.codigo === livro.codigo && (
                          <span className="loan-option-check" aria-label="Selecionado">✓</span>
                        )}
                      </button>
                    </li>
                  ))}
                  {availableBooks.length === 0 && (
                    <li className="loan-picker-empty">Nenhum exemplar disponível encontrado.</li>
                  )}
                </ul>
              </>
            ) : (
              <>
                <label className="loan-search">
                  <span aria-hidden="true">⌕</span>
                  <input
                    type="search"
                    aria-label="Pesquisar leitor"
                    placeholder="Pesquisar leitor"
                    value={readerQuery}
                    onChange={(event) => setReaderQuery(event.target.value)}
                  />
                </label>
                <ul className="loan-picker-options">
                  {filteredReaders.map((leitor) => {
                    const resumo = emprestimosDoLeitor(leitor.codigo)
                    const impedido = obterImpedimentoAtivo(impedimentos, leitor.codigo)
                    const fimImpedimento = impedido
                      ? obterFimImpedimentoAtivo(impedimentos, leitor.codigo)
                      : null
                    return (
                      <li key={leitor.codigo}>
                        <button
                          type="button"
                          className={
                            `loan-picker-option loan-reader-option${impedido ? ' loan-reader-option--blocked' : ''}`
                          }
                          aria-pressed={selectedReader?.codigo === leitor.codigo}
                          disabled={
                            Boolean(impedido) || !dadosEmprestimoProntos || !dadosLeitoresProntos
                          }
                          onClick={() => selecionarLeitor(leitor)}
                        >
                          <span>{leitor.nome}</span>
                          <span className="loan-reader-counts">
                            {impedido && fimImpedimento
                              ? `Impedido até ${formatarDataISO(fimImpedimento)}`
                              : `${resumo.abertos} abertos · ${resumo.atrasados} atrasados`}
                          </span>
                          {selectedReader?.codigo === leitor.codigo && (
                            <span className="loan-option-check" aria-label="Selecionado">✓</span>
                          )}
                        </button>
                      </li>
                    )
                  })}
                  {filteredReaders.length === 0 && (
                    <li className="loan-picker-empty">Nenhum leitor encontrado.</li>
                  )}
                </ul>
              </>
            )}
          </section>
        </div>
      )}

      {showConfirmation && selectedBook && selectedReader && (
        <div
          className="book-modal-backdrop loan-confirm-backdrop"
          onMouseDown={(event) => {
            if (event.target === event.currentTarget) setShowConfirmation(false)
          }}
        >
          <section
            className="book-modal loan-confirm-modal"
            role="dialog"
            aria-modal="true"
            aria-labelledby="loan-confirm-title"
          >
            <button
              type="button"
              className="book-modal-close loan-policy-close"
              aria-label="Fechar"
              onClick={() => setShowConfirmation(false)}
            >
              ×
            </button>
            <h2 id="loan-confirm-title">Confirmar empréstimo</h2>
            <p>
              O livro <strong>{selectedBook.nome}</strong> será emprestado para{' '}
              <strong>{selectedReader.nome}</strong>. A devolução deve ocorrer até{' '}
              {obterDataDeDevolucao()}.
            </p>
            <div className="loan-confirm-actions">
              <button
                type="button"
                className="book-button book-button--secondary"
                onClick={() => setShowConfirmation(false)}
              >
                Cancelar
              </button>
              <button
                type="button"
                className="book-button"
                onClick={confirmarEmprestimo}
                disabled={salvandoEmprestimo}
              >
                {salvandoEmprestimo ? 'Registrando...' : 'Confirmar'}
              </button>
            </div>
          </section>
        </div>
      )}

      {showPenalties && (
        <div
          className="book-modal-backdrop"
          onMouseDown={(event) => {
            if (event.target === event.currentTarget) setShowPenalties(false)
          }}
        >
          <section
            className="book-modal loan-penalties-modal"
            role="dialog"
            aria-modal="true"
            aria-labelledby="loan-penalties-title"
          >
            <button
              type="button"
              className="book-modal-close loan-policy-close"
              aria-label="Fechar"
              onClick={() => setShowPenalties(false)}
            >
              ×
            </button>
            <h2 id="loan-penalties-title">Penalidades</h2>
            <p>
              Cada livro devolvido após o prazo gera 10 dias de impedimento, contados a
              partir da devolução. O período acumula por livro: dois livros devolvidos
              com atraso geram 20 dias; três geram 30 dias, e assim sucessivamente.
            </p>
            <p>
              O sistema registra o início e o fim de cada impedimento e não permite novos
              empréstimos durante sua vigência. Empréstimos já ativos ainda podem ser
              devolvidos normalmente.
            </p>
          </section>
        </div>
      )}
    </main>
  )
}
