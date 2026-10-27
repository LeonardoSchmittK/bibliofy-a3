from datetime import date

from sqlalchemy import BigInteger, Boolean, Date, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base

class Livro(Base):
    __tablename__ = "Livro"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    codigo: Mapped[str] = mapped_column(String(20), unique=True)
    isbn: Mapped[str] = mapped_column(String(20), unique=True)
    nome: Mapped[str] = mapped_column(String(200))
    autor: Mapped[str] = mapped_column(String(150))
    editora: Mapped[str] = mapped_column(String(150))
    genero: Mapped[str] = mapped_column(String(80))
    data_lancamento: Mapped[date] = mapped_column(Date)
    quantidade_total: Mapped[int] = mapped_column(Integer)
    arquivado: Mapped[bool] = mapped_column(Boolean)