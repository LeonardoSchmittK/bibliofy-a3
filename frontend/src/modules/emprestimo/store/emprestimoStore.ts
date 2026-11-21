import { create } from 'zustand'

interface EmprestimoState {
  emprestimos: string[]
  registrarEmprestimo: (id: string) => void
}

export const useEmprestimoStore = create<EmprestimoState>((set) => ({
  emprestimos: [],
  registrarEmprestimo: (id) =>
    set((state) => ({ emprestimos: [...state.emprestimos, id] })),
}))