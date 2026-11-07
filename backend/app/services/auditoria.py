"""Camada "Service": escrita do log de auditoria (RNF10 / SEC05)."""

from datetime import date, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy.orm import Session

from app.models.auditoria import Auditoria
from app.models.pessoa import Pessoa

# Iguais aos CHECKs de database/schema.sql.
ACOES = (
    "CADASTRO",
    "ALTERACAO",
    "ARQUIVAMENTO",
    "EMPRESTIMO",
    "RENOVACAO",
    "DEVOLUCAO",
    "PERDA",
    "BLOQUEIO",
)
ENTIDADES = ("PESSOA", "LIVRO", "EMPRESTIMO", "BLOQUEIO")

_CHAVES_PROIBIDAS = {"senha", "senha_hash", "access_token"}


class AuditoriaInvalidaError(ValueError):
    pass


def _limpar(valor: Any) -> Any:
    if isinstance(valor, dict):
        return {k: _limpar(v) for k, v in valor.items() if k not in _CHAVES_PROIBIDAS}
    if isinstance(valor, (list, tuple)):
        return [_limpar(v) for v in valor]
    if valor is None or isinstance(valor, (str, int, float, bool)):
        return valor
    if isinstance(valor, (date, datetime, Decimal)):
        return str(valor)
    return str(valor)


def sanitizar_dados(dados: dict | None) -> dict | None:
    """Cópia sem senha/senha_hash/access_token em qualquer nível; tipos não JSON viram str."""
    if dados is None:
        return None
    return _limpar(dados)


def registrar(
    db: Session,
    *,
    responsavel: Pessoa,
    acao: str,
    entidade: str,
    entidade_id: int,
    dados: dict | None = None,
) -> Auditoria:
    """Grava um registro na transação corrente (flush, nunca commit)."""
    if acao not in ACOES:
        raise AuditoriaInvalidaError(f"Ação inválida: {acao!r}")
    if entidade not in ENTIDADES:
        raise AuditoriaInvalidaError(f"Entidade inválida: {entidade!r}")

    registro = Auditoria(
        responsavel_id=responsavel.id,
        acao=acao,
        entidade=entidade,
        entidade_id=entidade_id,
        dados=sanitizar_dados(dados),
    )
    db.add(registro)
    db.flush()
    db.refresh(registro, attribute_names=["criado_em"])
    return registro
