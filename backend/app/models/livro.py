from datetime import date

from sqlalchemy import BIGINT, BOOLEAN, INTEGER, VARCHAR, DATE
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base

class Livro(Base):
    __tablename__ = "livro"

    id: Mapped[int] = mapped_column(BIGINT, primary_key=True)
    
    codigo: Mapped[str] = mapped_column(VARCHAR(20), unique=True)
    isbn: Mapped[str] = mapped_column(VARCHAR(20), unique=True)
    nome: Mapped[str] = mapped_column(VARCHAR(200))
    autor: Mapped[str] = mapped_column(VARCHAR(150))
    editora: Mapped[str] = mapped_column(VARCHAR(150))
    genero: Mapped[str] = mapped_column(VARCHAR(80))
    data_lancamento: Mapped[date] = mapped_column(DATE)
    quantidade_total: Mapped[int] = mapped_column(INTEGER)
    arquivado: Mapped[bool] = mapped_column(BOOLEAN)