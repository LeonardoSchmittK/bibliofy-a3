"""Camada "Controller": rotas /usuarios (cadastro, consulta, edição e papel).

Testes que devem passar: tests/auth/test_rotas_usuarios.py.
"""
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from starlette import status

from app.api.deps import Bibliotecario, UsuarioAtual
from app.db.session import get_db
from app.schemas.usuario import PapelAlterar, UsuarioAtualizar, UsuarioCriar, UsuarioSaida
from app.services import usuario_service

router = APIRouter(prefix="/usuarios", tags=["usuarios"])

DB = Annotated[Session, Depends(get_db)]

def _nao_encontrado() -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuário não encontrado")

@router.post("", status_code=status.HTTP_201_CREATED, response_model=UsuarioSaida)
def criar(dados: UsuarioCriar, operador: Bibliotecario, db: DB):
    try:
        return usuario_service.criar_usuario(db, dados, operador)
    except usuario_service.ConflitoError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="E-mail ou matrícula já cadastrados"
        ) from None

@router.get("", response_model=list[UsuarioSaida])
def listar(
    solicitante: UsuarioAtual,
    db: DB,
    nome: str | None = None,
    matricula: str | None = None,
    papel: str | None = None,
):
    return usuario_service.listar_usuarios(db, solicitante, nome, matricula, papel)

@router.get("/{codigo}", response_model=UsuarioSaida)
def obter(codigo: str, solicitante: UsuarioAtual, db: DB):
    try:
        return usuario_service.obter_usuario(db, solicitante, codigo)
    except PermissionError:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso negado") from None
    except usuario_service.UsuarioNaoEncontradoError:
        raise _nao_encontrado() from None

@router.patch("/{codigo}", response_model=UsuarioSaida)
def atualizar(codigo: str, dados: UsuarioAtualizar, operador: Bibliotecario, db: DB):
    try:
        return usuario_service.atualizar_usuario(db, operador, codigo, dados)
    except usuario_service.UsuarioNaoEncontradoError:
        raise _nao_encontrado() from None
    except usuario_service.ConflitoError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="E-mail ou matrícula já cadastrados"
        ) from None

@router.put("/{codigo}/papel", response_model=UsuarioSaida)
def alterar_papel(codigo: str, dados: PapelAlterar, operador: Bibliotecario, db: DB):
    try:
        return usuario_service.alterar_papel(db, operador, codigo, dados.papel)
    except usuario_service.UsuarioNaoEncontradoError:
        raise _nao_encontrado() from None
