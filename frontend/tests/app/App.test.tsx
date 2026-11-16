
import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import App from '../../src/App'

describe('Aplicação Bibliofy', () => {
  it('deve exibir o título da página inicial', () => {
    render(<App />)

    expect(
      screen.getByRole('heading', { name: /Bibliofy/i })
    ).toBeInTheDocument()
  })
})
