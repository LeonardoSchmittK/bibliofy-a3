# Bibliofy — Back-end

FastAPI + PostgreSQL 17 + SQLAlchemy 2 (síncrono). Python 3.14.

## Instalação

Com **uv** (recomendado):

```bash
uv sync
```

Com **pip** (≥ 25.1):

```bash
python -m venv .venv
.venv\Scripts\activate        # Linux/macOS: source .venv/bin/activate
pip install -e . --group dev
```

Copie `.env.example` para `.env` e defina `DATABASE_URL` e um `JWT_SECRET` forte antes de iniciar a API.

## Execução

```bash
docker compose up -d          # PostgreSQL local
uvicorn app.main:app --reload
```

- `GET /health` → `{"status": "ok"}`
- Swagger em `http://localhost:8000/docs`

## Empréstimos

As rotas usam o token de acesso. Bibliotecários podem criar empréstimos, consultar o acervo
completo e registrar devoluções; leitores consultam apenas os próprios empréstimos e podem
solicitar uma renovação.

| Método e rota | Acesso | Uso |
| --- | --- | --- |
| `POST /emprestimos` | Bibliotecário | Cria empréstimo com `pessoa_codigo` e `livro_codigo` |
| `GET /emprestimos` | Usuário autenticado | Lista empréstimos, com filtros opcionais `status`, `busca`, `data_inicio` e `data_fim` |
| `GET /emprestimos/{codigo}` | Usuário autenticado | Consulta empréstimo próprio ou qualquer empréstimo, como bibliotecário |
| `POST /emprestimos/{codigo}/renovacao` | Titular ou bibliotecário | Renova uma vez, se ainda estiver no prazo |
| `POST /emprestimos/{codigo}/devolucao` | Bibliotecário | Registra devolução e eventual bloqueio |

O prazo inicial e o acréscimo da renovação são de 25 dias, contados a partir do vencimento
anterior. O leitor pode manter apenas um empréstimo ativo. Devoluções feitas após o vencimento
geram um bloqueio de 10 dias a partir da devolução; a disponibilidade dos livros é calculada
pelos empréstimos ativos e perdidos.

## Execução com Docker (banco + API) e dados de demonstração

```bash
cp .env.example .env          # SEED_DEMO=true já vem ligado
docker compose up -d --build  # sobe o PostgreSQL e a API em http://localhost:8000
```

Com `SEED_DEMO=true` a API roda `scripts/seed.py` a cada subida, criando (só se ainda não
existirem) 2 usuários e 15 livros. O seed nunca altera nem apaga dados existentes.

| Perfil        | E-mail                    | Senha            |
| ------------- | ------------------------- | ---------------- |
| Bibliotecário | bibliotecario@bibliofy.com | `Bibliofy@Demo1` |
| Aluno (LEITOR) | aluno@bibliofy.com        | `Bibliofy@Demo1` |

Os dados ficam no volume `pgdata` e **persistem** entre `docker compose down` / `up`
(inclusive livros cadastrados pela plataforma). Só `docker compose down -v` apaga tudo.
O `schema.sql` só é aplicado na primeira criação do volume: mudanças de schema exigem recriá-lo.
Em produção, use `SEED_DEMO=false` e um `JWT_SECRET` forte.

Para rodar o seed manualmente (API local): `python -m scripts.seed`.

## Testes

```bash
pytest                         # integração usa TEST_DATABASE_URL ou testcontainers
pytest -m "not integracao"     # só testes sem banco
```

Sem `TEST_DATABASE_URL` e sem Docker, os testes marcados com `integracao` são pulados com aviso.

## Qualidade

```bash
ruff check .
ruff format --check .
```

## Banco de dados

O schema é definido em `database/schema.sql` (fonte da verdade) e aplicado automaticamente
na primeira vez que o container sobe. Para recriar do zero (apaga os dados):

```bash
docker compose down -v
docker compose up -d
```

Não há Alembic: mudanças de schema são editadas em `database/schema.sql` e comunicadas ao time.

### Primeiro bibliotecário

Criado fora da API, pelo terminal (banco no ar e `.env` configurado):

```bash
python -m scripts.criar_bibliotecario
```
