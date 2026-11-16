
import { render, screen, cleanup } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, it, expect, afterEach } from 'vitest'
import { AppRoutes } from '../../src/routes/AppRoutes'

afterEach(() => {
  cleanup()
  window.history.replaceState({}, '', '/')
})

describe('Rotas do Bibliofy', () => {
  it('deve navegar para Login', async () => {
    const user = userEvent.setup()
    render(<AppRoutes />)

    await user.click(screen.getByRole('link', { name: /login/i }))

    expect(screen.getByRole('heading', { name: /login/i })).toBeInTheDocument()
  })

  it('deve navegar para Cadastro', async () => {
    const user = userEvent.setup()
    render(<AppRoutes />)

    await user.click(screen.getByRole('link', { name: /^cadastro$/i }))

    expect(screen.getByRole('heading', { name: /cadastro/i })).toBeInTheDocument()
  })

  it('deve navegar para Área do bibliotecário', async () => {
    const user = userEvent.setup()
    render(<AppRoutes />)

    await user.click(screen.getByRole('link', { name: /bibliotecário/i }))

    expect(screen.getByRole('heading', { name: /bibliotecário/i })).toBeInTheDocument()
  })

  it('deve navegar para Área do leitor', async () => {
    const user = userEvent.setup()
    render(<AppRoutes />)

    await user.click(screen.getByRole('link', { name: /área do leitor/i }))

    expect(screen.getByRole('heading', { name: /área do leitor/i })).toBeInTheDocument()
  })

  it('deve navegar para Livros', async () => {
    const user = userEvent.setup()
    render(<AppRoutes />)

    await user.click(screen.getByRole('link', { name: /repositório de livros/i }))

    expect(screen.getByRole('heading', { name: /repositório de livros/i })).toBeInTheDocument()
  })

  it('deve navegar para Empréstimos', async () => {
    const user = userEvent.setup()
    render(<AppRoutes />)

    await user.click(screen.getByRole('link', { name: /empréstimos/i }))

    expect(screen.getByRole('heading', { name: /consulta de empréstimos/i })).toBeInTheDocument()
  })
})
