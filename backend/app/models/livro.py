from datetime import date

from sqlalchemy import BIGINT, BOOLEAN, DATE, INTEGER, VARCHAR, FetchedValue, text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Livro(Base):
    __tablename__ = "livro"

    id: Mapped[int] = mapped_column(BIGINT, primary_key=True)

    codigo: Mapped[str] = mapped_column(VARCHAR(20), unique=True, server_default=FetchedValue())
    isbn: Mapped[str] = mapped_column(VARCHAR(20), unique=True)
    nome: Mapped[str] = mapped_column(VARCHAR(200))
    autor: Mapped[str] = mapped_column(VARCHAR(150))
    editora: Mapped[str] = mapped_column(VARCHAR(150))
    genero: Mapped[str] = mapped_column(VARCHAR(80))
    data_lancamento: Mapped[date] = mapped_column(DATE)
    quantidade_total: Mapped[int] = mapped_column(INTEGER)
    arquivado: Mapped[bool] = mapped_column(BOOLEAN, server_default=text("FALSE"))

    # TODO(#36) Descrição do livro (RF01: "descrição opcional").
    #   Testes: tests/livros/test_rotas_livros.py
    #   1. Adicionar a coluna `descricao TEXT` (anulável) à tabela `livro` em database/schema.sql
    #      (ver TODO lá): o schema.sql é a fonte da verdade, não há Alembic.
    #   2. Mapear aqui: `descricao: Mapped[str | None] = mapped_column(TEXT)` (importar `TEXT` de
    #      sqlalchemy).
    #   3. Recriar o banco local para aplicar o schema novo: `docker compose down -v` e
    #      `docker compose up -d`; avisar o time, porque os dados locais são apagados.
