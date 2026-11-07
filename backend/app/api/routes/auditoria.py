"""Camada "Controller": rotas /auditoria (somente leitura, só Bibliotecário).

Testes que devem passar: tests/auditoria/test_rotas_auditoria.py.
"""

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import exige_bibliotecario
from app.db.session import get_db
from app.schemas.auditoria import Acao, AuditoriaSaida, Entidade, PaginaAuditoria
from app.services import auditoria_consulta

router = APIRouter(
    prefix="/auditoria",
    tags=["auditoria"],
    dependencies=[Depends(exige_bibliotecario)],
)


@router.get(
    "",
    response_model=PaginaAuditoria,
    summary="Lista de registros de auditoria",
    description="Consulta paginada do histórico de auditoria com filtros opcionais.",
)
def listar_auditorias(
    db: Annotated[Session, Depends(get_db)],
    entidade: Entidade | None = None,
    acao: Acao | None = None,
    entidade_id: int | None = None,
    responsavel: str | None = None,
    de: datetime | None = None,
    ate: datetime | None = None,
    limite: int = Query(50, ge=1, le=200),
    deslocamento: int = Query(0, ge=0),
) -> PaginaAuditoria:
    try:
        itens, total = auditoria_consulta.listar_auditoria(
            db,
            entidade=entidade,
            entidade_id=entidade_id,
            acao=acao,
            responsavel_codigo=responsavel,
            de=de,
            ate=ate,
            limite=limite,
            deslocamento=deslocamento,
        )
    except ValueError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    return PaginaAuditoria(itens=itens, total=total, limite=limite, deslocamento=deslocamento)


@router.get(
    "/{registro_id}",
    response_model=AuditoriaSaida,
    summary="Detalhe de um registro de auditoria",
)
def obter_auditoria(registro_id: int, db: Annotated[Session, Depends(get_db)]):
    try:
        return auditoria_consulta.obter_registro(db, registro_id)
    except auditoria_consulta.RegistroNaoEncontradoError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Registro não encontrado") from exc
