# Bibliofy - Frontend

Frontend do sistema de biblioteca Bibliofy, feito com **React**, **TypeScript** e **Vite**, usando **Zustand** para gerenciamento de estado.

## Como rodar

### Pré-requisitos

- [Node.js](https://nodejs.org/) (versão 20 ou superior)
- npm (já vem com o Node)

### Passo a passo

1. Entre na pasta do frontend:

   ```bash
   cd frontend
   ```

2. Instale as dependências:

   ```bash
   npm install
   ```

3. Inicie o servidor de desenvolvimento:

   ```bash
   npm run dev
   ```

4. Abra o endereço mostrado no terminal (normalmente `http://localhost:5173`). Se a mensagem **"Está rodando, funcionou!"** aparecer, está tudo certo.

Para parar o servidor, use `Ctrl + C`.

### Outros comandos

| Comando | O que faz |
|---|---|
| `npm run dev` | Inicia o servidor de desenvolvimento |
| `npm run build` | Gera a versão de produção |
| `npm run lint` | Verifica o código com o ESLint |

### Problemas comuns no Windows

Se o PowerShell exibir o erro de "execução de scripts desabilitada", rode:

```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```

## Tecnologias

- **React**: biblioteca para construir a interface
- **TypeScript**: JavaScript com tipagem, que evita erros comuns
- **Vite**: ferramenta que roda e empacota o projeto
- **Zustand**: biblioteca simples para gerenciar o estado da aplicação
- **ESLint**: verificação de qualidade do código

## Organização do projeto (DDD)

### O que é DDD

**DDD** significa **Domain-Driven Design** (Design Orientado ao Domínio). A ideia é organizar o código pelos **assuntos do negócio** (o "domínio"), e não pelo tipo técnico do arquivo.

Em vez de juntar todos os componentes em uma pasta, todos os estados em outra e assim por diante, cada assunto da biblioteca tem sua própria pasta, contendo tudo o que ele precisa: componentes, estado e tipos.

Vantagens:

- Quem for mexer em empréstimos encontra tudo em um único lugar
- Cada pessoa pode trabalhar em um módulo diferente, com menos conflitos no Git
- O código reflete a linguagem do negócio (livro, empréstimo, leitor)

### Estrutura de pastas

```
src/
├── modules/
│   ├── livro/
│   │   ├── components/
│   │   └── store/
│   │       └── livroStore.ts
│   ├── emprestimo/
│   │   ├── components/
│   │   └── store/
│   │       └── emprestimoStore.ts
│   └── leitor/
│       ├── components/
│       └── store/
│           └── leitorStore.ts
├── shared/
├── App.tsx
└── main.tsx
```

### Módulos

| Módulo | Responsabilidade |
|---|---|
| `livro` | Acervo: cadastro, edição, exclusão, estoque e consulta de livros |
| `emprestimo` | Empréstimo, renovação, atraso, devolução e histórico |
| `leitor` | Cadastro e dados do aluno/leitor, incluindo bloqueio por atraso |
| `shared` | Itens genéricos usados por vários módulos (botões, funções utilitárias etc.) |

Atraso, devolução e bloqueio não têm pasta própria porque são regras de um empréstimo, então ficam dentro de `emprestimo`.

### Dentro de cada módulo

- `components/`: telas e pedaços de interface daquele assunto
- `store/`: estado do Zustand daquele assunto

## Estado com Zustand

Cada módulo tem o **seu próprio estado**, dentro da sua pasta. Não existe um estado global único.

| Store | Arquivo | Guarda |
|---|---|---|
| `useLivroStore` | `modules/livro/store/livroStore.ts` | Lista de livros |
| `useEmprestimoStore` | `modules/emprestimo/store/emprestimoStore.ts` | Lista de empréstimos |
| `useLeitorStore` | `modules/leitor/store/leitorStore.ts` | Lista de leitores |

Exemplo de uso em um componente:

```tsx
import { useLivroStore } from '../store/livroStore'

function ListaLivros() {
  const livros = useLivroStore((state) => state.livros)
  const adicionarLivro = useLivroStore((state) => state.adicionarLivro)

  return (
    <button onClick={() => adicionarLivro('Dom Casmurro')}>
      Adicionar ({livros.length})
    </button>
  )
}
```

## Estado atual e próximos passos

Esta é a **base do projeto**. As stores são simples (listas de texto) e ainda não são usadas por nenhuma tela. A estrutura serve para o time saber onde cada parte deve ficar.

Pontos que dependem de decisões das regras de negócio:

- Tipos completos de `Livro`, `Emprestimo` e `Leitor` (pasta `types/` de cada módulo)
- Módulo de autenticação (`auth`), conforme a definição de login
- Telas de cada fluxo