export type EmprestimoStatus =
  | 'EM_ANDAMENTO'
  | 'ATRASADO'
  | 'DEVOLVIDO'
  | 'DEVOLVIDO_COM_ATRASO'
  | 'PERDIDO'

export interface Emprestimo {
  id: number
  codigo: string
  livroId: string
  livroNome: string
  livroIsbn?: string
  leitorId: string
  leitorNome: string
  dataEmprestimo: string
  dataDevolucao: string
  dataDevolucaoRealizada?: string
  renovado: boolean
  status: EmprestimoStatus
  bloqueioInicio?: string
  bloqueioFimExclusivo?: string
}

export interface NovoEmprestimo {
  livroId: string
  livroNome: string
  leitorId: string
  leitorNome: string
}

export interface ImpedimentoEmprestimo {
  emprestimoId: number
  leitorId: string
  inicio: string
  fimExclusivo: string
  motivo: string
}
