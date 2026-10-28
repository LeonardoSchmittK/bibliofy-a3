from datetime import date

from sqlalchemy import BIGINT, DATE, VARCHAR, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Bloqueio(Base):
    __tablename__ = "bloqueio"

    id: Mapped[int] = mapped_column(BIGINT, primary_key=True)

    pessoa_id: Mapped[int] = mapped_column(BIGINT, ForeignKey("pessoa.id"))
    emprestimo_id: Mapped[int] = mapped_column(BIGINT, ForeignKey("emprestimo.id"), unique=True)
    inicio: Mapped[date] = mapped_column(DATE)
    fim_exclusivo: Mapped[date] = mapped_column(DATE)
    motivo: Mapped[str] = mapped_column(VARCHAR(200))
