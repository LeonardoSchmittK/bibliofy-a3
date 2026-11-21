import { create } from 'zustand'

interface LeitorState {
  leitores: string[]
  adicionarLeitor: (nome: string) => void
}

export const useLeitorStore = create<LeitorState>((set) => ({
  leitores: [],
  adicionarLeitor: (nome) =>
    set((state) => ({ leitores: [...state.leitores, nome] })),
}))