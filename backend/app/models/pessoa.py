from sqlalchemy import BigInteger
from sqlalchemy.orm import Mapped, mapped_column, String, Boolean

from backend.app.db.base import Base

class Pessoa(Base):
    __tablename__ = "pessoa"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    
    codigo: Mapped[str] = mapped_column(String(20), unique=True)
    matricula: Mapped[str] = mapped_column(String(30), unique=True)
    nome: Mapped[str] = mapped_column(String(150))
    email: Mapped[str] = mapped_column(String(100), unique=True)
    telefone: Mapped[str] = mapped_column(String(20))
    senha_hash: Mapped[str] = mapped_column(String(255))
    papel: Mapped[str] = mapped_column(String(20))
    ativo: Mapped[bool] = mapped_column(Boolean)