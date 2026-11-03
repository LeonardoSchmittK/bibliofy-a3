from datetime import datetime
from typing import Any

from sqlalchemy import BIGINT, TIMESTAMP, VARCHAR, ForeignKey, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Auditoria(Base):
    __tablename__ = "auditoria"

    id: Mapped[int] = mapped_column(BIGINT, primary_key=True)

    responsavel_id: Mapped[int] = mapped_column(BIGINT, ForeignKey("pessoa.id"))
    acao: Mapped[str] = mapped_column(VARCHAR(30))
    entidade: Mapped[str] = mapped_column(VARCHAR(30))
    entidade_id: Mapped[int] = mapped_column(BIGINT)
    dados: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    criado_em: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
