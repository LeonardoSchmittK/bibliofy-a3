FROM ghcr.io/astral-sh/uv:python3.14-bookworm-slim

ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy PYTHONUNBUFFERED=1
WORKDIR /app

# Dependências primeiro, para aproveitar o cache de camadas.
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project --no-build

COPY app ./app
COPY scripts ./scripts
ENV PATH="/app/.venv/bin:$PATH" PYTHONPATH="/app"
RUN useradd --system --no-create-home bibliofy
USER bibliofy

EXPOSE 8000
CMD ["sh", "scripts/entrypoint.sh"]
