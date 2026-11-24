"""Contratos de entrada e saída da API de empréstimos."""

from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

StatusEmprestimo = Literal[
    "EMPRESTADO",
    "ATRASADO",
    "DEVOLVIDO",
    "DEVOLVIDO_COM_ATRASO",
    "PERDIDO",
]


class EmprestimoCriar(BaseModel):
    pessoa_codigo: str = Field(min_length=1, max_length=20)
    livro_codigo: str = Field(min_length=1, max_length=20)


class EmprestimoSaida(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    codigo: str
    pessoa_codigo: str
    pessoa_nome: str
    livro_codigo: str
    livro_nome: str
    livro_isbn: str
    data_emprestimo: date
    data_prevista: date
    data_devolucao: date | None
    renovado: bool
    status_atual: StatusEmprestimo
    bloqueio_inicio: date | None = None
    bloqueio_fim_exclusivo: date | None = None
