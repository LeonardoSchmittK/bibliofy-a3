import { create } from 'zustand'

interface LivroState {
  livros: string[]
  adicionarLivro: (titulo: string) => void
}

export const useLivroStore = create<LivroState>((set) => ({
  livros: [],
  adicionarLivro: (titulo) =>
    set((state) => ({ livros: [...state.livros, titulo] })),
}))