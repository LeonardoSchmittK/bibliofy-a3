from sqlalchemy import BIGINT, BOOLEAN, VARCHAR
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.base import Base

class Pessoa(Base):
    __tablename__ = "pessoa"

    id: Mapped[int] = mapped_column(BIGINT, primary_key=True)
    
    codigo: Mapped[str] = mapped_column(VARCHAR(20), unique=True)
    matricula: Mapped[str] = mapped_column(VARCHAR(30), unique=True)
    nome: Mapped[str] = mapped_column(VARCHAR(150))
    email: Mapped[str] = mapped_column(VARCHAR(100), unique=True)
    telefone: Mapped[str] = mapped_column(VARCHAR(20))
    senha_hash: Mapped[str] = mapped_column(VARCHAR(255))
    papel: Mapped[str] = mapped_column(VARCHAR(20))
    ativo: Mapped[bool] = mapped_column(BOOLEAN)