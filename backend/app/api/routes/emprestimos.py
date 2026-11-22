"""Rotas do fluxo de empréstimo, renovação e devolução."""

from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import Bibliotecario, UsuarioAtual
from app.db.session import get_db
from app.schemas.emprestimo import EmprestimoCriar, EmprestimoSaida, StatusEmprestimo
from app.services import emprestimo_service

router = APIRouter(prefix="/emprestimos", tags=["emprestimos"])
DB = Annotated[Session, Depends(get_db)]


def _nao_encontrado(mensagem: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=mensagem)


def _conflito(exc: Exception) -> HTTPException:
    return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))


@router.post("", status_code=status.HTTP_201_CREATED, response_model=EmprestimoSaida)
def criar(dados: EmprestimoCriar, operador: Bibliotecario, db: DB):
    try:
        return emprestimo_service.criar_emprestimo(db, dados, operador)
    except emprestimo_service.PessoaNaoEncontradaError:
        raise _nao_encontrado("Leitor não encontrado") from None
    except emprestimo_service.LivroNaoEncontradoError:
        raise _nao_encontrado("Livro não encontrado") from None
    except emprestimo_service.RegraEmprestimoError as exc:
        raise _conflito(exc) from None


@router.get("", response_model=list[EmprestimoSaida])
def listar(
    solicitante: UsuarioAtual,
    db: DB,
    status_atual: Annotated[StatusEmprestimo | None, Query(alias="status")] = None,
    busca: str | None = None,
    data_inicio: date | None = None,
    data_fim: date | None = None,
):
    if data_inicio and data_fim and data_inicio > data_fim:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="A data inicial deve ser anterior à data final",
        )
    return emprestimo_service.listar_emprestimos(
        db,
        solicitante=solicitante,
        status_atual=status_atual,
        busca=busca,
        data_inicio=data_inicio,
        data_fim=data_fim,
    )


@router.get("/{codigo}", response_model=EmprestimoSaida)
def obter(codigo: str, solicitante: UsuarioAtual, db: DB):
    try:
        return emprestimo_service.obter_emprestimo(db, codigo, solicitante)
    except emprestimo_service.EmprestimoNaoEncontradoError:
        raise _nao_encontrado("Empréstimo não encontrado") from None
    except PermissionError:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso negado") from None


@router.post("/{codigo}/devolucao", response_model=EmprestimoSaida)
def devolver(codigo: str, operador: Bibliotecario, db: DB):
    try:
        return emprestimo_service.devolver_emprestimo(db, codigo, operador)
    except emprestimo_service.EmprestimoNaoEncontradoError:
        raise _nao_encontrado("Empréstimo não encontrado") from None
    except emprestimo_service.RegraEmprestimoError as exc:
        raise _conflito(exc) from None


@router.post("/{codigo}/renovacao", response_model=EmprestimoSaida)
def renovar(codigo: str, solicitante: UsuarioAtual, db: DB):
    try:
        return emprestimo_service.renovar_emprestimo(db, codigo, solicitante)
    except emprestimo_service.EmprestimoNaoEncontradoError:
        raise _nao_encontrado("Empréstimo não encontrado") from None
    except PermissionError:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso negado") from None
    except emprestimo_service.RegraEmprestimoError as exc:
        raise _conflito(exc) from None
