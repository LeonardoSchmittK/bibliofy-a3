
import { describe, it, expect, beforeEach } from 'vitest'
import { useLivroStore } from '../../src/modules/livro/store/livroStore'

describe('Armazenamento de livros', () => {
  beforeEach(() => {
    useLivroStore.setState({ livros: [] })
  })

  it('deve iniciar com a lista de livros vazia', () => {
    expect(useLivroStore.getState().livros).toEqual([])
  })

  it('deve adicionar um livro à lista', () => {
    useLivroStore.getState().adicionarLivro('Dom Casmurro')

    expect(useLivroStore.getState().livros).toContain('Dom Casmurro')
  })

  it('deve permitir adicionar mais de um livro', () => {
    useLivroStore.getState().adicionarLivro('Dom Casmurro')
    useLivroStore.getState().adicionarLivro('O Pequeno Príncipe')

    expect(useLivroStore.getState().livros).toEqual([
      'Dom Casmurro',
      'O Pequeno Príncipe',
    ])
  })
})
