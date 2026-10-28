from sqlalchemy import BIGINT, BOOLEAN, VARCHAR, FetchedValue, text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Pessoa(Base):
    __tablename__ = "pessoa"

    id: Mapped[int] = mapped_column(BIGINT, primary_key=True)

    codigo: Mapped[str] = mapped_column(VARCHAR(20), unique=True, server_default=FetchedValue())
    matricula: Mapped[str] = mapped_column(VARCHAR(30), unique=True)
    nome: Mapped[str] = mapped_column(VARCHAR(150))
    email: Mapped[str] = mapped_column(VARCHAR(100), unique=True)
    telefone: Mapped[str | None] = mapped_column(VARCHAR(20))
    senha_hash: Mapped[str] = mapped_column(VARCHAR(255))
    papel: Mapped[str] = mapped_column(VARCHAR(20), server_default=text("'LEITOR'"))
    ativo: Mapped[bool] = mapped_column(BOOLEAN, server_default=text("TRUE"))
