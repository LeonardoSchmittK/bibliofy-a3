from datetime import date

from sqlalchemy import BIGINT, BOOLEAN, DATE, INTEGER, TEXT, VARCHAR, FetchedValue, text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Livro(Base):
    __tablename__ = "livro"

    id: Mapped[int] = mapped_column(BIGINT, primary_key=True)

    codigo: Mapped[str] = mapped_column(VARCHAR(20), unique=True, server_default=FetchedValue())
    isbn: Mapped[str] = mapped_column(VARCHAR(20), unique=True, nullable=False)
    nome: Mapped[str] = mapped_column(VARCHAR(200), nullable=False)
    autor: Mapped[str] = mapped_column(VARCHAR(150), nullable=False)
    editora: Mapped[str] = mapped_column(VARCHAR(150), nullable=False)
    genero: Mapped[str] = mapped_column(VARCHAR(80), nullable=False)
    data_lancamento: Mapped[date] = mapped_column(DATE, nullable=False)
    quantidade_total: Mapped[int] = mapped_column(INTEGER, nullable=False)
    arquivado: Mapped[bool] = mapped_column(BOOLEAN, server_default=text("FALSE"))
    descricao: Mapped[str | None] = mapped_column(TEXT)
