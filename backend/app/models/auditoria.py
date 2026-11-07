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

    # TODO(auditoria) Relação com o responsável (usada por app/services/auditoria_consulta.py).
    #   Testes: tests/auditoria/test_consulta_service.py (`registro.responsavel.codigo`).
    #   1. Importar `relationship` de sqlalchemy.orm e `Pessoa` de app.models.pessoa.
    #   2. `responsavel: Mapped["Pessoa"] = relationship(lazy="raise")`: o serviço carrega com
    #      `selectinload`, e o acesso preguiçoso acidental falha alto em vez de gerar N+1.
