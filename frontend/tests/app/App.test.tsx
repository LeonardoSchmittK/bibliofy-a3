
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

  it('deve exibir uma citação aleatória no canto superior', () => {
    render(<App />)

    const quote = document.querySelector('.random-quote')

    expect(quote).toBeInTheDocument()
    expect(quote?.textContent).toMatch(
      /Miguel de Cervantes|George R\. R\. Martin|Neil Gaiman/
    )
  })
})
