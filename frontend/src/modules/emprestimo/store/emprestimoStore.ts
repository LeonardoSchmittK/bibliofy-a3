import { create } from 'zustand'
import { ApiError, apiRequest } from '../../../shared/api/client'
import { useAuthStore } from '../../auth/store/authStore'
import type {
  Emprestimo,
  EmprestimoStatus,
  ImpedimentoEmprestimo,
  NovoEmprestimo,
} from '../types/emprestimo'

interface EmprestimoApi {
  id: number
  codigo: string
  pessoa_codigo: string
  pessoa_nome: string
  livro_codigo: string
  livro_nome: string
  livro_isbn: string
  data_emprestimo: string
  data_prevista: string
  data_devolucao: string | null
  renovado: boolean
  status_atual: 'EMPRESTADO' | 'ATRASADO' | 'DEVOLVIDO' | 'DEVOLVIDO_COM_ATRASO' | 'PERDIDO'
  bloqueio_inicio: string | null
  bloqueio_fim_exclusivo: string | null
}

interface EmprestimoState {
  emprestimos: Emprestimo[]
  impedimentos: ImpedimentoEmprestimo[]
  carregando: boolean
  salvando: boolean
  carregado: boolean
  carregadoPara: string | null
  erro: string | null
  limparErro: () => void
  carregarEmprestimos: () => Promise<void>
  registrarEmprestimo: (dados: NovoEmprestimo) => Promise<boolean>
  registrarDevolucao: (codigo: string) => Promise<boolean>
  renovarEmprestimo: (codigo: string) => Promise<boolean>
}

function obterToken(): string {
  const token = useAuthStore.getState().accessToken
  if (!token) throw new ApiError('Sua sessão expirou. Entre novamente.', 401)
  return token
}

function mapearStatus(status: EmprestimoApi['status_atual']): EmprestimoStatus {
  if (status === 'EMPRESTADO') return 'EM_ANDAMENTO'
  return status
}

function mapearEmprestimoApi(emprestimo: EmprestimoApi): Emprestimo {
  return {
    id: emprestimo.id,
    codigo: emprestimo.codigo,
    leitorId: emprestimo.pessoa_codigo,
    leitorNome: emprestimo.pessoa_nome,
    livroId: emprestimo.livro_codigo,
    livroNome: emprestimo.livro_nome,
    livroIsbn: emprestimo.livro_isbn,
    dataEmprestimo: emprestimo.data_emprestimo,
    dataDevolucao: emprestimo.data_prevista,
    dataDevolucaoRealizada: emprestimo.data_devolucao ?? undefined,
    renovado: emprestimo.renovado,
    status: mapearStatus(emprestimo.status_atual),
    bloqueioInicio: emprestimo.bloqueio_inicio ?? undefined,
    bloqueioFimExclusivo: emprestimo.bloqueio_fim_exclusivo ?? undefined,
  }
}

function derivarImpedimentos(emprestimos: Emprestimo[]): ImpedimentoEmprestimo[] {
  return emprestimos.flatMap((emprestimo) => {
    if (
      emprestimo.status !== 'DEVOLVIDO_COM_ATRASO' ||
      !emprestimo.bloqueioInicio ||
      !emprestimo.bloqueioFimExclusivo
    ) {
      return []
    }
    return [{
      emprestimoId: emprestimo.id,
      leitorId: emprestimo.leitorId,
      inicio: emprestimo.bloqueioInicio,
      fimExclusivo: emprestimo.bloqueioFimExclusivo,
      motivo: 'Devolução realizada após a data prevista',
    }]
  })
}

function mensagemErro(error: unknown): string {
  if (error instanceof ApiError) {
    if (error.status === 401) return 'Sua sessão expirou. Entre novamente.'
    return error.message
  }
  if (error instanceof Error) return error.message
  return 'Não foi possível concluir a operação de empréstimo.'
}

function registrarErro(error: unknown, set: (partial: Partial<EmprestimoState>) => void) {
  set({ erro: mensagemErro(error) })
  if (error instanceof ApiError && error.status === 401) {
    useAuthStore.getState().sair()
  }
}

function aplicarEmprestimo(
  emprestimos: Emprestimo[],
  emprestimo: Emprestimo,
  inserir = false,
): Emprestimo[] {
  if (inserir) return [emprestimo, ...emprestimos]
  return emprestimos.map((atual) =>
    atual.codigo === emprestimo.codigo ? emprestimo : atual,
  )
}

export function obterImpedimentoAtivo(
  impedimentos: ImpedimentoEmprestimo[],
  leitorId: string,
  hoje = dataHoje(),
): ImpedimentoEmprestimo | null {
  return impedimentos.find(
    (impedimento) =>
      impedimento.leitorId === leitorId &&
      impedimento.inicio <= hoje &&
      hoje < impedimento.fimExclusivo,
  ) ?? null
}

export function obterFimImpedimentoAtivo(
  impedimentos: ImpedimentoEmprestimo[],
  leitorId: string,
  hoje = dataHoje(),
): string | null {
  const fimMaisDistante = impedimentos
    .filter(
      (impedimento) =>
        impedimento.leitorId === leitorId && impedimento.fimExclusivo > hoje,
    )
    .reduce(
      (fim, impedimento) =>
        impedimento.fimExclusivo > fim ? impedimento.fimExclusivo : fim,
      '',
    )

  if (!fimMaisDistante) return null
  const [ano, mes, dia] = fimMaisDistante.split('-').map(Number)
  const ultimoDia = new Date(ano, mes - 1, dia - 1, 12)
  return [
    ultimoDia.getFullYear(),
    String(ultimoDia.getMonth() + 1).padStart(2, '0'),
    String(ultimoDia.getDate()).padStart(2, '0'),
  ].join('-')
}

export const useEmprestimoStore = create<EmprestimoState>((set) => ({
  emprestimos: [],
  impedimentos: [],
  carregando: false,
  salvando: false,
  carregado: false,
  carregadoPara: null,
  erro: null,
  limparErro: () => set({ erro: null }),
  carregarEmprestimos: async () => {
    set({ carregando: true, erro: null })
    try {
      const resposta = await apiRequest<EmprestimoApi[]>('/emprestimos', {
        token: obterToken(),
      })
      const emprestimos = resposta.map(mapearEmprestimoApi)
      set({
        emprestimos,
        impedimentos: derivarImpedimentos(emprestimos),
        carregado: true,
        carregadoPara: useAuthStore.getState().usuario?.codigo ?? null,
        erro: null,
      })
    } catch (error) {
      registrarErro(error, set)
    } finally {
      set({ carregando: false })
    }
  },
  registrarEmprestimo: async (dados) => {
    set({ erro: null, salvando: true })
    try {
      const resposta = await apiRequest<EmprestimoApi>('/emprestimos', {
        method: 'POST',
        token: obterToken(),
        body: { pessoa_codigo: dados.leitorId, livro_codigo: dados.livroId },
      })
      const emprestimo = mapearEmprestimoApi(resposta)
      set((state) => {
        const emprestimos = aplicarEmprestimo(state.emprestimos, emprestimo, true)
        return { emprestimos, impedimentos: derivarImpedimentos(emprestimos), erro: null }
      })
      return true
    } catch (error) {
      registrarErro(error, set)
      return false
    } finally {
      set({ salvando: false })
    }
  },
  registrarDevolucao: async (codigo) => {
    set({ erro: null, salvando: true })
    try {
      const resposta = await apiRequest<EmprestimoApi>(
        `/emprestimos/${encodeURIComponent(codigo)}/devolucao`,
        { method: 'POST', token: obterToken() },
      )
      const emprestimo = mapearEmprestimoApi(resposta)
      set((state) => {
        const emprestimos = aplicarEmprestimo(state.emprestimos, emprestimo)
        return { emprestimos, impedimentos: derivarImpedimentos(emprestimos), erro: null }
      })
      return true
    } catch (error) {
      registrarErro(error, set)
      return false
    } finally {
      set({ salvando: false })
    }
  },
  renovarEmprestimo: async (codigo) => {
    set({ erro: null, salvando: true })
    try {
      const resposta = await apiRequest<EmprestimoApi>(
        `/emprestimos/${encodeURIComponent(codigo)}/renovacao`,
        { method: 'POST', token: obterToken() },
      )
      const emprestimo = mapearEmprestimoApi(resposta)
      set((state) => {
        const emprestimos = aplicarEmprestimo(state.emprestimos, emprestimo)
        return { emprestimos, impedimentos: derivarImpedimentos(emprestimos), erro: null }
      })
      return true
    } catch (error) {
      registrarErro(error, set)
      return false
    } finally {
      set({ salvando: false })
    }
  },
}))

function dataHoje(): string {
  const hoje = new Date()
  return [
    hoje.getFullYear(),
    String(hoje.getMonth() + 1).padStart(2, '0'),
    String(hoje.getDate()).padStart(2, '0'),
  ].join('-')
}
