import { AppRoutes } from './routes/AppRoutes'
import './App.css'

const quotes = [
  {
    text: 'Quem lê muito e anda muito, vê muito e sabe muito.',
    author: 'Miguel de Cervantes',
  },
  {
    text: 'Um leitor vive mil vidas antes de morrer. O homem que nunca lê vive apenas uma.',
    author: 'George R. R. Martin',
  },
  {
    text: 'Um livro é um sonho que você segura nas mãos.',
    author: 'Neil Gaiman',
  },
]

function App() {
  const quote = quotes[Math.floor(Math.random() * quotes.length)]

  return (
    <>
      <figure className="random-quote">
        <blockquote>“{quote.text}”</blockquote>
        <figcaption>— {quote.author}</figcaption>
      </figure>
      <AppRoutes />
    </>
  )
}

export default App