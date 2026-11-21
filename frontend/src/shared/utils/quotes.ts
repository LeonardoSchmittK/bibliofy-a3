export const quotes = [
  { text: 'A leitura de todos os bons livros é como uma conversa com as melhores mentes dos séculos passados.', author: 'René Descartes' },
  { text: 'Os livros são espelhos: só se vê neles o que se possui dentro.', author: 'Carlos Ruiz Zafón' },
  { text: 'Ler é sonhar pela mão de outrem.', author: 'Fernando Pessoa' },
  { text: 'Um livro é um sonho que você segura nas mãos.', author: 'Neil Gaiman' },
  { text: 'A leitura é para o intelecto o que o exercício é para o corpo.', author: 'Joseph Addison' },
  { text: 'Sempre imaginei que o paraíso fosse uma espécie de biblioteca.', author: 'Jorge Luis Borges' },
  { text: 'Quem não lê, não pensa; e quem não pensa será para sempre um servo.', author: 'Paulo Francis' },
  { text: 'Os livros têm os mesmos inimigos que o homem: o fogo, a umidade, os animais, o tempo e o próprio conteúdo.', author: 'Paul Valéry' },
  { text: 'Aquele que lê muito e anda muito, vê muito e sabe muito.', author: 'Miguel de Cervantes' },
  { text: 'A literatura é a maneira mais agradável de ignorar a vida.', author: 'Fernando Pessoa' },
]

export function getRandomQuote() {
  return quotes[Math.floor(Math.random() * quotes.length)]
}
