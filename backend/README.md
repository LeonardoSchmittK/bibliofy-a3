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

Copie `.env.example` para `.env` e ajuste se necessário.

## Execução

```bash
docker compose up -d          # PostgreSQL local
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

## Banco de dados

O schema é definido em `database/schema.sql` (fonte da verdade) e aplicado automaticamente
na primeira vez que o container sobe. Para recriar do zero (apaga os dados):

```bash
docker compose down -v
docker compose up -d
```

Não há Alembic: mudanças de schema são editadas em `database/schema.sql` e comunicadas ao time.
