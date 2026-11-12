"""Dependências reutilizáveis do FastAPI para autenticação e autorização (SEC04).

Testes que devem passar: tests/auth/test_dependencias.py.
"""

from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import TokenInvalidoError, decodificar_token
from app.db.session import get_db
from app.models import Pessoa

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def _nao_autenticado() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Não autenticado",  # mensagem genérica: não revela o motivo
        headers={"WWW-Authenticate": "Bearer"},
    )


def usuario_autenticado(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[Session, Depends(get_db)],
) -> Pessoa:
    try:
        claims = decodificar_token(token)
    except TokenInvalidoError:
        raise _nao_autenticado() from None

    pessoa = db.scalars(select(Pessoa).where(Pessoa.codigo == claims["sub"])).first()
    if pessoa is None or not pessoa.ativo:
        raise _nao_autenticado()
    return pessoa


def exige_bibliotecario(usuario: Annotated[Pessoa, Depends(usuario_autenticado)]) -> Pessoa:
    if usuario.papel != "BIBLIOTECARIO":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso negado")
    return usuario


UsuarioAtual = Annotated[Pessoa, Depends(usuario_autenticado)]
Bibliotecario = Annotated[Pessoa, Depends(exige_bibliotecario)]
