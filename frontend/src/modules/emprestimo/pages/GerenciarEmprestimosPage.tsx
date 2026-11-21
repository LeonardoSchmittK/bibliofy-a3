import { useMemo, useState } from 'react'
import { Link } from 'wouter'
import { getRandomQuote } from '../../../shared/utils/quotes'
import {
  obterFimImpedimentoAtivo,
  useEmprestimoStore,
} from '../store/emprestimoStore'
import { useLivroStore } from '../../livro/store/livroStore'
import type { Emprestimo, EmprestimoStatus } from '../types/emprestimo'

const quote = getRandomQuote()
type StatusFiltro = 'TODOS' | EmprestimoStatus

const nomesStatus: Record<EmprestimoStatus, string> = {
  EM_ANDAMENTO: 'Em andamento',
  ATRASADO: 'Fora do prazo',
  DEVOLVIDO: 'Devolvido',
  DEVOLVIDO_COM_ATRASO: 'Devolvido com atraso',
}

function formatarData(data: string): string {
  const [ano, mes, dia] = data.split('-').map(Number)
  return new Intl.DateTimeFormat('pt-BR').format(new Date(ano, mes - 1, dia))
}

function formatarDataISO(data: Date): string {
  return [
    data.getFullYear(),
    String(data.getMonth() + 1).padStart(2, '0'),
    String(data.getDate()).padStart(2, '0'),
  ].join('-')
}

function dataHoje(): string {
  return formatarDataISO(new Date())
}

function inicioDoAno(): string {
  return `${new Date().getFullYear()}-01-01`
}

function fimDoAno(): string {
  return `${new Date().getFullYear()}-12-31`
}

export function GerenciarEmprestimosPage() {
  const emprestimos = useEmprestimoStore((state) => state.emprestimos)
  const registrarDevolucao = useEmprestimoStore((state) => state.registrarDevolucao)
  const [statusFiltro, setStatusFiltro] = useState<StatusFiltro>('TODOS')
  const [busca, setBusca] = useState('')
  const [dataInicial, setDataInicial] = useState(inicioDoAno)
  const [dataFinal, setDataFinal] = useState(fimDoAno)
  const [mensagemAcao, setMensagemAcao] = useState('')

  const intervaloInvalido = Boolean(dataInicial && dataFinal && dataInicial > dataFinal)
  const emprestimosFiltrados = useMemo(() => {
    const termo = busca.trim().toLocaleLowerCase('pt-BR')
    return emprestimos.filter((emprestimo) => {
      const statusCorresponde =
        statusFiltro === 'TODOS' || emprestimo.status === statusFiltro
      const buscaCorresponde =
        !termo ||
        [String(emprestimo.id), emprestimo.codigo, emprestimo.livroId]
          .some((identificador) => identificador.toLocaleLowerCase('pt-BR').includes(termo))
      const dataCorresponde =
        !intervaloInvalido &&
        (!dataInicial || emprestimo.dataEmprestimo >= dataInicial) &&
        (!dataFinal || emprestimo.dataEmprestimo <= dataFinal)
      return statusCorresponde && buscaCorresponde && dataCorresponde
    })
  }, [busca, dataFinal, dataInicial, emprestimos, intervaloInvalido, statusFiltro])

  function devolverEmprestimo(emprestimo: Emprestimo) {
    const livro = useLivroStore
      .getState()
      .livros.find((item) => item.codigo === emprestimo.livroId)
    if (!livro) {
      setMensagemAcao('Não foi possível registrar a devolução: o livro não foi encontrado no acervo.')
      return
    }

    if (!registrarDevolucao(emprestimo.id)) {
      setMensagemAcao('Este empréstimo já foi encerrado ou não está mais disponível para devolução.')
      return
    }

    useLivroStore.getState().devolverExemplar(emprestimo.livroId)

    if (dataHoje() > emprestimo.dataDevolucao) {
      const fimImpedimento = obterFimImpedimentoAtivo(
        useEmprestimoStore.getState().impedimentos,
        emprestimo.leitorId,
      )
      setMensagemAcao(
          `Devolução atrasada registrada. O leitor ficará impedido de realizar novos empréstimos até ${fimImpedimento ? formatarData(fimImpedimento) : 'o fim do período'}.`,
      )
      return
    }

    setMensagemAcao('Devolução registrada com sucesso.')
  }

  return (
    <main className="loan-page loan-management-page">
      <figure className="loan-quote">
        <blockquote>“{quote.text}”</blockquote>
        <figcaption>{quote.author}</figcaption>
      </figure>

      <section className="loan-management-content">
        <header className="loan-management-header">
          <Link href="/" className="loan-home-link">← Voltar para a tela inicial</Link>
          <h1>Gerir empréstimos</h1>
          <p>Aqui é possível filtrar e acompanhar cada empréstimo.</p>
        </header>

        <section className="loan-management-panel" aria-label="Filtros e empréstimos">
          <div className="loan-filters">
            <label className="loan-filter-status" htmlFor="loan-status">
              <span>Status</span>
              <select
                id="loan-status"
                value={statusFiltro}
                onChange={(event) => setStatusFiltro(event.target.value as StatusFiltro)}
              >
                <option value="TODOS">Todos</option>
                <option value="EM_ANDAMENTO">Em andamento</option>
                <option value="ATRASADO">Fora do prazo</option>
                <option value="DEVOLVIDO">Devolvido</option>
                <option value="DEVOLVIDO_COM_ATRASO">Devolvido com atraso</option>
              </select>
            </label>

            <label className="loan-filter-search" htmlFor="loan-search">
              <span>Buscar empréstimo</span>
              <input
                id="loan-search"
                type="search"
                placeholder="emp_04394934 ou liv_329323"
                value={busca}
                onChange={(event) => setBusca(event.target.value)}
              />
            </label>

            <fieldset className="loan-filter-interval">
              <legend>Intervalo</legend>
              <label htmlFor="loan-date-from">
                <span className="loan-visually-hidden">Data inicial</span>
                <input
                  id="loan-date-from"
                  type="date"
                  value={dataInicial}
                  onChange={(event) => setDataInicial(event.target.value)}
                />
              </label>
              <span aria-hidden="true">—</span>
              <label htmlFor="loan-date-to">
                <span className="loan-visually-hidden">Data final</span>
                <input
                  id="loan-date-to"
                  type="date"
                  value={dataFinal}
                  onChange={(event) => setDataFinal(event.target.value)}
                />
              </label>
            </fieldset>
          </div>

          <div className="loan-table-scroll">
            <table className="loan-table">
              <thead>
                <tr>
                  <th scope="col">Leitor</th>
                  <th scope="col">Livro</th>
                  <th scope="col">Empréstimo</th>
                  <th scope="col">Prevista</th>
                  <th scope="col">Realizada</th>
                  <th scope="col">Status</th>
                  <th scope="col">Ações</th>
                </tr>
              </thead>
              <tbody>
                {emprestimosFiltrados.map((emprestimo: Emprestimo) => (
                  <tr key={emprestimo.id}>
                    <td>{emprestimo.leitorNome}</td>
                    <td>{emprestimo.livroNome}</td>
                    <td>{formatarData(emprestimo.dataEmprestimo)}</td>
                    <td>{formatarData(emprestimo.dataDevolucao)}</td>
                    <td>
                      {emprestimo.dataDevolucaoRealizada
                        ? formatarData(emprestimo.dataDevolucaoRealizada)
                        : '—'}
                    </td>
                    <td>
                      <span className={`loan-status loan-status--${emprestimo.status.toLowerCase()}`}>
                        {nomesStatus[emprestimo.status]}
                      </span>
                    </td>
                    <td>
                      {emprestimo.status.startsWith('DEVOLVIDO') ? (
                        '—'
                      ) : (
                        <button
                          type="button"
                          className="book-button loan-return-button"
                          aria-label={`Registrar devolução do empréstimo ${emprestimo.codigo}`}
                          onClick={() => devolverEmprestimo(emprestimo)}
                        >
                          Registrar devolução
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
                {emprestimosFiltrados.length === 0 && (
                  <tr>
                    <td className="loan-table-empty" colSpan={7}>
                      {intervaloInvalido
                        ? 'A data inicial deve ser anterior à data final.'
                        : 'Nenhum empréstimo encontrado para esses filtros.'}
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
          {mensagemAcao && (
            <p className="loan-action-message" role="status">{mensagemAcao}</p>
          )}
          <p className="loan-results-count" role="status">
            {emprestimosFiltrados.length}{' '}
            {emprestimosFiltrados.length === 1 ? 'empréstimo encontrado' : 'empréstimos encontrados'}
          </p>
        </section>
      </section>
    </main>
  )
}
