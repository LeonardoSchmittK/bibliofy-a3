"""Dependências reutilizáveis do FastAPI para autenticação e autorização (SEC04).

Testes que devem passar: tests/auth/test_dependencias.py.
"""
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import get_db
from app.models import Pessoa

_bearer = HTTPBearer(auto_error=False)

def _nao_autenticado() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Não autenticado",
        headers={"WWW-Authenticate": "Bearer"},
    )


def usuario_autenticado(
    credenciais: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
    db: Annotated[Session, Depends(get_db)],
) -> Pessoa:
    """Pessoa dona do token; 401 se faltar, for inválido/expirado ou a pessoa estiver inativa."""
    if credenciais is None:
        raise _nao_autenticado()
    try:
        payload = jwt.decode(
            credenciais.credentials, get_settings().jwt_secret, algorithms=["HS256"]
        )
    except jwt.PyJWTError:
        raise _nao_autenticado() from None

    codigo = payload.get("sub")
    if not isinstance(codigo, str):
        raise _nao_autenticado()

    pessoa = db.scalars(select(Pessoa).where(Pessoa.codigo == codigo)).one_or_none()
    if pessoa is None or not pessoa.ativo:
        raise _nao_autenticado()
    return pessoa


def exige_bibliotecario(pessoa: Annotated[Pessoa, Depends(usuario_autenticado)]) -> Pessoa:
    if pessoa.papel != "BIBLIOTECARIO":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso negado")
    return pessoa
# TODO(#35) Passo a passo da implementação:
#   1. `oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")` (faz o botão "Authorize" do
#      Swagger funcionar e já responde 401 + `WWW-Authenticate: Bearer` sem cabeçalho ou com
#      esquema diferente de Bearer).
#   2. `usuario_autenticado(token=Depends(oauth2_scheme), db=Depends(get_db)) -> Pessoa`:
#        a. `decodificar_token(token)`; `TokenInvalidoError` -> HTTP 401 com
#           `headers={"WWW-Authenticate": "Bearer"}` (mensagem genérica, sem detalhar o motivo);
#        b. buscar a `Pessoa` pelo `sub` (campo `codigo`) no banco;
#        c. pessoa inexistente OU `ativo == False` -> o mesmo 401 (a conta é consultada a cada
#           request, então desativar um usuário derruba os tokens que ele já tinha);
#        d. devolver a `Pessoa` carregada do banco.
#   3. `exige_bibliotecario(usuario=Depends(usuario_autenticado)) -> Pessoa`:
#        - `usuario.papel != "BIBLIOTECARIO"` -> HTTP 403;
#        - o papel vem do BANCO, nunca de claims do token (o token só carrega `sub`).
#   4. Opcional: aliases `UsuarioAtual = Annotated[Pessoa, Depends(usuario_autenticado)]` e
#      `Bibliotecario = Annotated[Pessoa, Depends(exige_bibliotecario)]` para as rotas.
#   5. Regra geral: 401 = autenticação inválida; 403 = autenticado sem permissão.
#   6. Rodar `pytest tests/auth/test_dependencias.py`.
