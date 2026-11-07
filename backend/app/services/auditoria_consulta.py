"""Camada "Service": consulta do log de auditoria (RNF10). Só leitura.

Testes que devem passar: tests/auditoria/test_consulta_service.py e, para a escrita,
tests/auditoria/test_registrar.py (que exercita app/services/auditoria.py).
"""
from datetime import datetime

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session, selectinload

from app.models.auditoria import Auditoria
from app.models.pessoa import Pessoa


class RegistroNaoEncontradoError(Exception):
    pass


def _filtrar(
    stmt: Select, *, entidade, entidade_id, acao, responsavel_codigo, de, ate
) -> Select:
    if entidade is not None:
        stmt = stmt.where(Auditoria.entidade == entidade)
    if entidade_id is not None:
        stmt = stmt.where(Auditoria.entidade_id == entidade_id)
    if acao is not None:
        stmt = stmt.where(Auditoria.acao == acao)
    if responsavel_codigo is not None:
        stmt = stmt.join(Pessoa, Pessoa.id == Auditoria.responsavel_id).where(
            Pessoa.codigo == responsavel_codigo
        )
    if de is not None:
        stmt = stmt.where(Auditoria.criado_em >= de)
    if ate is not None:
        stmt = stmt.where(Auditoria.criado_em < ate)
    return stmt


def listar_auditoria(
    db: Session,
    *,
    entidade: str | None = None,
    entidade_id: int | None = None,
    acao: str | None = None,
    responsavel_codigo: str | None = None,
    de: datetime | None = None,
    ate: datetime | None = None,
    limite: int = 50,
    deslocamento: int = 0,
) -> tuple[list[Auditoria], int]:
    """Registros da página (mais recentes primeiro) e o total sem paginação."""
    if not 1 <= limite <= 200:
        raise ValueError("limite deve estar entre 1 e 200")
    if deslocamento < 0:
        raise ValueError("deslocamento não pode ser negativo")
    if de is not None and ate is not None and de > ate:
        raise ValueError("'de' não pode ser posterior a 'ate'")

    filtros = dict(
        entidade=entidade,
        entidade_id=entidade_id,
        acao=acao,
        responsavel_codigo=responsavel_codigo,
        de=de,
        ate=ate,
    )
    total = db.scalar(_filtrar(select(func.count()).select_from(Auditoria), **filtros)) or 0
    stmt = (
        _filtrar(select(Auditoria), **filtros)
        .options(selectinload(Auditoria.responsavel))
        .order_by(Auditoria.criado_em.desc(), Auditoria.id.desc())
        .limit(limite)
        .offset(deslocamento)
    )
    return list(db.scalars(stmt).all()), total


def obter_registro(db: Session, registro_id: int) -> Auditoria:
    registro = db.scalar(
        select(Auditoria)
        .options(selectinload(Auditoria.responsavel))
        .where(Auditoria.id == registro_id)
    )
    if registro is None:
        raise RegistroNaoEncontradoError(registro_id)
    return registro
