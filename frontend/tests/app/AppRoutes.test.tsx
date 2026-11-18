
import { render, screen, cleanup } from '@testing-library/react'
import { describe, it, expect, afterEach } from 'vitest'
import { AppRoutes } from '../../src/routes/AppRoutes'

afterEach(() => {
  cleanup()
  window.localStorage.clear()
  window.history.replaceState({}, '', '/')
})

describe('Rotas do Bibliofy', () => {
  it('deve navegar para Login', async () => {
    window.history.replaceState({}, '', '/login')
    render(<AppRoutes />)

    expect(screen.getByLabelText(/qual seu email/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/qual sua senha/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /acessar/i })).toBeInTheDocument()
    expect(screen.queryByRole('link', { name: /voltar ao início/i })).not.toBeInTheDocument()
  })

  it('deve navegar para Cadastro', async () => {
    window.history.replaceState({}, '', '/cadastro')
    render(<AppRoutes />)

    expect(screen.getByLabelText(/qual seu nome/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/qual sua matrícula/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /cadastrar/i })).toBeInTheDocument()
  })

  it('redireciona para login quando a pessoa não está autenticada', () => {
    window.history.replaceState({}, '', '/')
    render(<AppRoutes />)

    expect(screen.getByLabelText(/qual seu email/i)).toBeInTheDocument()
  })

  it('redireciona rotas privadas para login sem sessão', () => {
    window.history.replaceState({}, '', '/livros')
    render(<AppRoutes />)

    expect(screen.getByLabelText(/qual seu email/i)).toBeInTheDocument()
  })

  it('permite acesso às rotas privadas com token de sessão', () => {
    window.localStorage.setItem('access_token', 'test-token')
    window.history.replaceState({}, '', '/livros')
    render(<AppRoutes />)

    expect(screen.getByRole('heading', { name: /repositório de livros/i })).toBeInTheDocument()
  })

  it('permite acesso à área do bibliotecário com token de sessão', () => {
    window.localStorage.setItem('access_token', 'test-token')
    window.history.replaceState({}, '', '/bibliotecario')
    render(<AppRoutes />)

    expect(screen.getByRole('heading', { name: /área do bibliotecário/i })).toBeInTheDocument()
  })
})
