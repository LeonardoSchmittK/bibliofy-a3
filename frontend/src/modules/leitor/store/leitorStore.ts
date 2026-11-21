import { create } from 'zustand'
import type { Leitor } from '../types/leitor'

interface LeitorState {
  leitores: Leitor[]
  adicionarLeitor: (nome: string) => void
}

const leitoresExemplo: Leitor[] = [
  { codigo: 'lei_00000001', nome: 'Ana Costa' },
  { codigo: 'lei_00000002', nome: 'Bruno Lima' },
  { codigo: 'lei_00000003', nome: 'Camila Rocha' },
  { codigo: 'lei_00000004', nome: 'Daniel Souza' },
  { codigo: 'lei_00000005', nome: 'Elena Martins' },
  { codigo: 'lei_00000006', nome: 'Felipe Nunes' },
  { codigo: 'lei_00000007', nome: 'Gabriela Alves' },
  { codigo: 'lei_00000008', nome: 'Henrique Silva' },
]

export const useLeitorStore = create<LeitorState>((set) => ({
  leitores: leitoresExemplo,
  adicionarLeitor: (nome) =>
    set((state) => ({
      leitores: [
        ...state.leitores,
        { codigo: `lei_${Date.now().toString(36)}`, nome },
      ],
    })),
}))