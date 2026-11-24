import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { useAuthStore } from '../../src/modules/auth/store/authStore'
import { useLivroStore } from '../../src/modules/livro/store/livroStore'
import type { LivroDados } from '../../src/modules/livro/types/livro'

const dadosLivro: LivroDados = {
  nome: 'Dom Casmurro',
  autor: 'Machado de Assis',
  isbn: '9788535910663',
  editora: 'Companhia das Letras',
  genero: 'Ficção',
  data_lancamento: '1899-01-01',
  quantidade_total: 4,
}

function respostaApi(body: unknown, status = 200): Response {
  return {
    ok: status >= 200 && status < 300,
    status,
    text: async () => body === undefined ? '' : JSON.stringify(body),
  } as Response
}

function livroApi(dados: Partial<LivroDados> = {}, arquivado = false) {
  return {
    codigo: 'liv_test',
    isbn: dados.isbn ?? dadosLivro.isbn,
    nome: dados.nome ?? dadosLivro.nome,
    autor: dados.autor ?? dadosLivro.autor,
    editora: dados.editora ?? dadosLivro.editora,
    genero: dados.genero ?? dadosLivro.genero,
    data_lancamento: dados.data_lancamento ?? dadosLivro.data_lancamento,
    descricao: null,
    quantidade_total: dados.quantidade_total ?? dadosLivro.quantidade_total,
    quantidade_disponivel: dados.quantidade_total ?? dadosLivro.quantidade_total,
    disponibilidade: 'DISPONIVEL',
    arquivado,
  }
}

describe('Armazenamento de livros integrado à API', () => {
  beforeEach(() => {
    window.sessionStorage.setItem('access_token', 'test-token')
    useAuthStore.setState({
      accessToken: 'test-token',
      estado: 'authenticated',
    })
    useLivroStore.setState({
      livros: [],
      carregado: false,
      carregando: false,
      erro: null,
    })
    vi.stubGlobal('fetch', vi.fn(async (_input: RequestInfo | URL, init?: RequestInit) => {
      const method = init?.method ?? 'GET'
      if (method === 'POST' && String(_input).endsWith('/arquivar')) {
        return respostaApi(livroApi({}, true))
      }
      if (method === 'POST' || method === 'PATCH') {
        const dados = JSON.parse(String(init?.body)) as LivroDados
        return respostaApi(livroApi(dados))
      }
      return respostaApi([])
    }))
  })

  afterEach(() => {
    vi.unstubAllGlobals()
    window.sessionStorage.clear()
  })

  it('carrega e converte as quantidades retornadas pela API', async () => {
    vi.stubGlobal('fetch', vi.fn(async () => respostaApi([
      { ...livroApi(), quantidade_disponivel: 1 },
    ])))

    await useLivroStore.getState().carregarLivros()

    expect(useLivroStore.getState().livros[0]).toMatchObject({
      codigo: 'liv_test',
      quantidade_total: 4,
      quantidade_disponivel: 1,
      quantidade_emprestada: 3,
      arquivado: false,
    })
    expect(useLivroStore.getState().carregado).toBe(true)
  })

  it('cadastra um livro na API e atualiza o catálogo', async () => {
    expect(await useLivroStore.getState().adicionarLivro(dadosLivro)).toBe(true)

    expect(useLivroStore.getState().livros).toMatchObject([
      {
        ...dadosLivro,
        quantidade_disponivel: 4,
        quantidade_emprestada: 0,
        arquivado: false,
      },
    ])
    expect(fetch).toHaveBeenCalledWith(
      expect.stringContaining('/livros/'),
      expect.objectContaining({ method: 'POST' }),
    )
  })

  it('edita e arquiva um livro por meio da API', async () => {
    await useLivroStore.getState().adicionarLivro(dadosLivro)
    const [livro] = useLivroStore.getState().livros
    expect(await useLivroStore.getState().atualizarLivro(livro.codigo, {
      ...dadosLivro,
      quantidade_total: 8,
      nome: 'Dom Casmurro — edição nova',
    })).toBe(true)

    expect(useLivroStore.getState().livros[0]).toMatchObject({
      nome: 'Dom Casmurro — edição nova',
      quantidade_total: 8,
      quantidade_disponivel: 8,
    })
    expect(await useLivroStore.getState().arquivarLivro(livro.codigo)).toBe(true)
    expect(useLivroStore.getState().livros[0].arquivado).toBe(true)
  })

  it('expõe erro de cadastro duplicado sem alterar o catálogo', async () => {
    vi.stubGlobal('fetch', vi.fn(async () => respostaApi(
      { detail: 'ISBN_DUPLICADO' },
      409,
    )))

    expect(await useLivroStore.getState().adicionarLivro(dadosLivro)).toBe(false)
    expect(useLivroStore.getState().erro).toMatch(/ISBN/i)
    expect(useLivroStore.getState().livros).toEqual([])
  })
})
