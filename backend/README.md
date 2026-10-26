# Bibliofy — Back-end

FastAPI + PostgreSQL 17 + SQLAlchemy 2 (síncrono) + Alembic. Python 3.14.

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

Copie `.env.example` para `.env` e ajuste se necessário.

## Execução

```bash
docker compose up -d          # PostgreSQL local
alembic upgrade head          # aplica as migrations
uvicorn app.main:app --reload
```

- `GET /health` → `{"status": "ok"}`
- Swagger em `http://localhost:8000/docs`

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

## Migrations

```bash
alembic revision --autogenerate -m "descrição"
alembic upgrade head
alembic downgrade -1
```

`migrations/create-tables.sql` é o SQL de referência do schema; a migration inicial será criada em outra issue.
