
import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import App from '../../src/App'

describe('Aplicação Bibliofy', () => {
  it('deve abrir o login quando não há sessão', () => {
    render(<App />)

    expect(screen.getByLabelText(/email/i)).toBeInTheDocument()
  })

  it('deve exibir as opções de autenticação', () => {
    render(<App />)

    expect(screen.getByRole('link', { name: /criar conta/i })).toHaveAttribute('href', '/cadastro')
    expect(screen.getByRole('link', { name: /^entrar$/i })).toHaveAttribute('href', '/login')
  })
})
