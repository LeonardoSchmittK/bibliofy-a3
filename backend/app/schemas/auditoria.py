"""Camada "Model/View": schemas de saída da auditoria.

Testes que devem passar: tests/auditoria/test_schemas.py.
"""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict

# Devem ser iguais aos CHECKs ck_auditoria_acao / ck_auditoria_entidade (e a ACOES/ENTIDADES
# em app/services/auditoria.py).
Acao = Literal[
    "CADASTRO",
    "ALTERACAO",
    "ARQUIVAMENTO",
    "EMPRESTIMO",
    "RENOVACAO",
    "DEVOLUCAO",
    "PERDA",
    "BLOQUEIO",
]
Entidade = Literal["PESSOA", "LIVRO", "EMPRESTIMO", "BLOQUEIO"]


class ResponsavelSaida(BaseModel):
    """Só código e nome: nunca e-mail, senha_hash ou id interno."""

    model_config = ConfigDict(from_attributes=True)

    codigo: str
    nome: str


class AuditoriaSaida(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    acao: Acao
    entidade: Entidade
    entidade_id: int
    responsavel: ResponsavelSaida
    dados: dict | None
    criado_em: datetime


class PaginaAuditoria(BaseModel):
    itens: list[AuditoriaSaida]
    total: int
    limite: int
    deslocamento: int
