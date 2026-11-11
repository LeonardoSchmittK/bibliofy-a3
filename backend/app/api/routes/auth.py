"""Camada "Controller": rotas /auth (login, usuário atual e logout).

Testes que devem passar: tests/auth/test_rotas_auth.py.
"""
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from starlette.responses import Response

from app.api.deps import UsuarioAtual
from app.db.session import get_db
from app.models import Pessoa
from app.schemas.auth import TokenSaida
from app.schemas.usuario import UsuarioSaida
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/login", response_model=TokenSaida)
def login(
    form: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Annotated[Session, Depends(get_db)],
) -> TokenSaida:
    pessoa = auth_service.autenticar(db, form.username, form.password)
    if pessoa is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciais inválidas",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return TokenSaida(access_token=auth_service.emitir_token(pessoa))

@router.get("/me", response_model=UsuarioSaida)
def me(usuario: UsuarioAtual) -> Pessoa:
    return usuario

@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(_usuario: UsuarioAtual) -> Response:
    return Response(status_code=status.HTTP_204_NO_CONTENT)