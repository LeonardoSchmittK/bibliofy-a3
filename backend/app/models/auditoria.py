import datetime
from typing import Any

from sqlalchemy import BIGINT, TIMESTAMP, VARCHAR, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import JSONB

from backend.app.db.base import Base


class Auditoria(Base):
    __tablename__ = "auditoria"

    id: Mapped[int] = mapped_column(BIGINT, primary_key=True)

    responsavel_id: Mapped[int] = mapped_column(BIGINT, ForeignKey("pessoa.id"))
    acao: Mapped[str] = mapped_column(VARCHAR(30))
    entidade: Mapped[str] = mapped_column(VARCHAR(30))
    entidade_id: Mapped[int] = mapped_column(BIGINT)
    dados: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    criado_em: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True))
