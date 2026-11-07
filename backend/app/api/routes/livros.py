"""Camada "Controller": rotas /livros (CRUD pelo Bibliotecário; Leitor só consulta).

Testes que devem passar: tests/livros/test_rotas_livros.py.
Depende da issue #35 (autenticação): dependências `usuario_autenticado` e `exige_bibliotecario`
em app/api/deps.py e o serviço de auditoria em app/services/auditoria.py.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.api.deps import exige_bibliotecario, usuario_autenticado  # issue #35
from app.db.session import get_db
from app.models import Pessoa
from app.schemas.livro import LivroAtualizar, LivroCriar, LivroSaida, PreviaArquivamento
from app.services import livro_service
from app.services.livro_service import (
    LivroDuplicadoError,
    LivroNaoEncontradoError,
    QuantidadeInsuficienteError,
)

router = APIRouter(prefix="/livros", tags=["livros"])


def _conflito(motivo: str) -> JSONResponse:
    return JSONResponse(status_code=status.HTTP_409_CONFLICT, content={"motivo": motivo})


def _nao_encontrado() -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Livro não encontrado")


def _eh_bibliotecario(usuario: Pessoa) -> bool:
    return usuario.papel == "BIBLIOTECARIO"


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=LivroSaida)
def criar_livro(
    dados: LivroCriar,
    db: Annotated[Session, Depends(get_db)],
    responsavel: Annotated[Pessoa, Depends(exige_bibliotecario)],
):
    try:
        return livro_service.criar_livro(db, dados, responsavel)
    except LivroDuplicadoError:
        return _conflito("ISBN_DUPLICADO")


@router.get("/", response_model=list[LivroSaida])
def listar_livros(
    db: Annotated[Session, Depends(get_db)],
    usuario: Annotated[Pessoa, Depends(usuario_autenticado)],
    nome: str | None = None,
    autor: str | None = None,
    isbn: str | None = None,
    genero: str | None = None,
    codigo: str | None = None,
    arquivados: bool = False,
):
    # RF19: arquivado nunca aparece no catálogo do leitor.
    return livro_service.listar_livros(
        db,
        nome=nome,
        autor=autor,
        isbn=isbn,
        genero=genero,
        codigo=codigo,
        incluir_arquivados=arquivados and _eh_bibliotecario(usuario),
    )


@router.get("/{codigo}", response_model=LivroSaida)
def obter_livro(
    codigo: str,
    db: Annotated[Session, Depends(get_db)],
    usuario: Annotated[Pessoa, Depends(usuario_autenticado)],
):
    try:
        return livro_service.obter_livro(db, codigo, incluir_arquivados=_eh_bibliotecario(usuario))
    except LivroNaoEncontradoError:
        raise _nao_encontrado() from None


@router.patch("/{codigo}", response_model=LivroSaida)
def atualizar_livro(
    codigo: str,
    dados: LivroAtualizar,
    db: Annotated[Session, Depends(get_db)],
    responsavel: Annotated[Pessoa, Depends(exige_bibliotecario)],
):
    try:
        return livro_service.atualizar_livro(db, codigo, dados, responsavel)
    except LivroNaoEncontradoError:
        raise _nao_encontrado() from None
    except LivroDuplicadoError:
        return _conflito("ISBN_DUPLICADO")
    except QuantidadeInsuficienteError:
        return _conflito("QUANTIDADE_INSUFICIENTE")


@router.post("/{codigo}/arquivar", response_model=LivroSaida)
def arquivar_livro(
    codigo: str,
    db: Annotated[Session, Depends(get_db)],
    responsavel: Annotated[Pessoa, Depends(exige_bibliotecario)],
):
    try:
        return livro_service.arquivar_livro(db, codigo, responsavel)
    except LivroNaoEncontradoError:
        raise _nao_encontrado() from None


@router.get("/{codigo}/previa-arquivamento", response_model=PreviaArquivamento)
def previa_arquivamento(
    codigo: str,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[Pessoa, Depends(exige_bibliotecario)],
):
    try:
        n = livro_service.contar_emprestimos_ativos(db, codigo)
    except LivroNaoEncontradoError:
        raise _nao_encontrado() from None
    return PreviaArquivamento(emprestimos_ativos=n)
