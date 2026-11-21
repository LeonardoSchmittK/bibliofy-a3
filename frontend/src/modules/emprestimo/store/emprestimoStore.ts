import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type {
  Emprestimo,
  ImpedimentoEmprestimo,
  NovoEmprestimo,
} from '../types/emprestimo'

interface EmprestimoState {
  emprestimos: Emprestimo[]
  impedimentos: ImpedimentoEmprestimo[]
  registrarEmprestimo: (dados: NovoEmprestimo) => boolean
  registrarDevolucao: (emprestimoId: number) => boolean
}

const DIAS_IMPEDIMENTO_POR_ATRASO = 10

function formatarDataISO(data: Date): string {
  return [
    data.getFullYear(),
    String(data.getMonth() + 1).padStart(2, '0'),
    String(data.getDate()).padStart(2, '0'),
  ].join('-')
}

function adicionarDias(dataISO: string, dias: number): string {
  const [ano, mes, dia] = dataISO.split('-').map(Number)
  const data = new Date(ano, mes - 1, dia + dias, 12)
  return formatarDataISO(data)
}

function dataHoje(): string {
  return formatarDataISO(new Date())
}

function dataComDeslocamento(dias: number): string {
  return adicionarDias(dataHoje(), dias)
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

  return fimMaisDistante ? adicionarDias(fimMaisDistante, -1) : null
}

function criarExemplo(
  id: number,
  codigo: string,
  leitorId: string,
  leitorNome: string,
  livroId: string,
  livroNome: string,
  inicioEmDias: number,
  devolucaoEmDias: number,
  status: Emprestimo['status'],
  devolvidoEmDias?: number,
): Emprestimo {
  return {
    id,
    codigo,
    leitorId,
    leitorNome,
    livroId,
    livroNome,
    dataEmprestimo: dataComDeslocamento(inicioEmDias),
    dataDevolucao: dataComDeslocamento(devolucaoEmDias),
    dataDevolucaoRealizada:
      devolvidoEmDias === undefined ? undefined : dataComDeslocamento(devolvidoEmDias),
    status,
  }
}

const emprestimosExemplo: Emprestimo[] = [
  criarExemplo(1, 'emp_04394934', 'lei_00000001', 'Ana Costa', 'liv_00000002', 'O Pequeno Príncipe', -14, 11, 'EM_ANDAMENTO'),
  criarExemplo(2, 'emp_32910482', 'lei_00000002', 'Bruno Lima', 'liv_00000001', 'Dom Quixote', -40, -15, 'ATRASADO'),
  criarExemplo(3, 'emp_72018364', 'lei_00000003', 'Camila Rocha', 'liv_00000004', 'O Alquimista', -10, 15, 'EM_ANDAMENTO'),
  criarExemplo(4, 'emp_68235091', 'lei_00000004', 'Daniel Souza', 'liv_00000005', 'Memórias Póstumas', -50, -25, 'DEVOLVIDO', -20),
  criarExemplo(5, 'emp_91537420', 'lei_00000005', 'Elena Martins', 'liv_00000006', 'O Código da Vinci', -45, -20, 'ATRASADO'),
  criarExemplo(6, 'emp_27461903', 'lei_00000006', 'Felipe Nunes', 'liv_00000001', 'Dom Quixote', -7, 18, 'EM_ANDAMENTO'),
  criarExemplo(7, 'emp_50381726', 'lei_00000007', 'Gabriela Alves', 'liv_00000003', 'A Hora da Estrela', -3, 22, 'EM_ANDAMENTO'),
  criarExemplo(8, 'emp_16029847', 'lei_00000008', 'Henrique Silva', 'liv_00000002', 'O Pequeno Príncipe', -65, -40, 'DEVOLVIDO', -35),
]

function criarCodigoEmprestimo(emprestimos: Emprestimo[]): string {
  let codigo: string
  do {
    codigo = `emp_${Math.floor(10_000_000 + Math.random() * 90_000_000)}`
  } while (emprestimos.some((emprestimo) => emprestimo.codigo === codigo))
  return codigo
}

export const useEmprestimoStore = create<EmprestimoState>()(
  persist(
    (set) => ({
      emprestimos: emprestimosExemplo,
      impedimentos: [],
      registrarEmprestimo: (dados) => {
        let registrado = false
        set((state) => {
          if (obterImpedimentoAtivo(state.impedimentos, dados.leitorId)) return state

          registrado = true
          const hoje = dataHoje()
          return {
            emprestimos: [
              {
                id: state.emprestimos.reduce(
                  (maiorId, emprestimo) => Math.max(maiorId, emprestimo.id),
                  0,
                ) + 1,
                codigo: criarCodigoEmprestimo(state.emprestimos),
                ...dados,
                dataEmprestimo: hoje,
                dataDevolucao: dataComDeslocamento(25),
                status: 'EM_ANDAMENTO',
              },
              ...state.emprestimos,
            ],
          }
        })
        return registrado
      },
      registrarDevolucao: (emprestimoId) => {
        let registrada = false
        set((state) => {
          const emprestimo = state.emprestimos.find((item) => item.id === emprestimoId)
          if (
            !emprestimo ||
            emprestimo.status === 'DEVOLVIDO' ||
            emprestimo.status === 'DEVOLVIDO_COM_ATRASO'
          ) {
            return state
          }

          registrada = true
          const hoje = dataHoje()
          const devolvidoComAtraso = hoje > emprestimo.dataDevolucao
          let impedimentos = state.impedimentos

          if (devolvidoComAtraso) {
            const fimDoImpedimentoAtual = state.impedimentos
              .filter(
                (impedimento) =>
                  impedimento.leitorId === emprestimo.leitorId &&
                  impedimento.fimExclusivo > hoje,
              )
              .reduce(
                (fim, impedimento) =>
                  impedimento.fimExclusivo > fim ? impedimento.fimExclusivo : fim,
                hoje,
              )
            const inicio = fimDoImpedimentoAtual
            impedimentos = [
              ...state.impedimentos,
              {
                emprestimoId: emprestimo.id,
                leitorId: emprestimo.leitorId,
                inicio,
                fimExclusivo: adicionarDias(inicio, DIAS_IMPEDIMENTO_POR_ATRASO),
                motivo: 'Devolução realizada após a data prevista',
              },
            ]
          }

          return {
            emprestimos: state.emprestimos.map((item) =>
              item.id === emprestimo.id
                ? {
                    ...item,
                    dataDevolucaoRealizada: hoje,
                    status: devolvidoComAtraso
                      ? 'DEVOLVIDO_COM_ATRASO'
                      : 'DEVOLVIDO',
                  }
                : item,
            ),
            impedimentos,
          }
        })
        return registrada
      },
    }),
    { name: 'bibliofy-emprestimos' },
  ),
)