"""Camada "View" do catálogo: schemas Pydantic de entrada e saída de livros.

Testes que devem passar: tests/livros/test_schemas.py.
"""

from datetime import date
from typing import Annotated, Literal

from pydantic import AfterValidator, BaseModel, ConfigDict, Field, StringConstraints

from app.core.isbn import normalizar_isbn

Isbn = Annotated[str, AfterValidator(normalizar_isbn)]
Texto = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
Quantidade = Annotated[int, Field(ge=0, strict=True)]

Disponibilidade = Literal["DISPONIVEL", "EMPRESTADO", "INDISPONIVEL"]


class LivroCriar(BaseModel):
    isbn: Isbn
    nome: Texto
    autor: Texto
    editora: Texto
    genero: Texto
    data_lancamento: date
    quantidade_total: Quantidade
    descricao: str | None = None


class LivroAtualizar(BaseModel):
    isbn: Isbn | None = None
    nome: Texto | None = None
    autor: Texto | None = None
    editora: Texto | None = None
    genero: Texto | None = None
    data_lancamento: date | None = None
    quantidade_total: Quantidade | None = None
    descricao: str | None = None


class LivroSaida(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    codigo: str
    isbn: str
    nome: str
    autor: str
    editora: str
    genero: str
    data_lancamento: date
    descricao: str | None
    quantidade_total: int
    quantidade_disponivel: int
    disponibilidade: Disponibilidade
    arquivado: bool


class PreviaArquivamento(BaseModel):
    emprestimos_ativos: int
