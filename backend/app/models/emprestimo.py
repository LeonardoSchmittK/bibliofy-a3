from datetime import date

from sqlalchemy import BIGINT, BOOLEAN, DATE, VARCHAR, FetchedValue, ForeignKey, text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Emprestimo(Base):
    __tablename__ = "emprestimo"

    id: Mapped[int] = mapped_column(BIGINT, primary_key=True)

    codigo: Mapped[str] = mapped_column(VARCHAR(20), unique=True, server_default=FetchedValue())
    pessoa_id: Mapped[int] = mapped_column(BIGINT, ForeignKey("pessoa.id"))
    livro_id: Mapped[int] = mapped_column(BIGINT, ForeignKey("livro.id"))
    data_emprestimo: Mapped[date] = mapped_column(DATE)
    data_prevista: Mapped[date] = mapped_column(DATE)
    data_devolucao: Mapped[date | None] = mapped_column(DATE)
    renovado: Mapped[bool] = mapped_column(BOOLEAN, server_default=text("FALSE"))
    status_atual: Mapped[str] = mapped_column(VARCHAR(25), server_default=text("'EMPRESTADO'"))
