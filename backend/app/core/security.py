"""Núcleo de segurança: hash de senha (Argon2id) e JWT.

Testes que devem passar: tests/auth/test_security.py (e tests/auth/test_config_jwt.py).
Requisitos: SEC02 (senhas) e SEC03 (autenticação e sessão), issue #13.
"""

from datetime import UTC, datetime, timedelta

import jwt
from pwdlib import PasswordHash
from pwdlib.exceptions import PwdlibError

from app.core.config import get_settings
from app.models import Pessoa

_hasher = PasswordHash.recommended()

def hash_senha(senha: str) -> str:
    return _hasher.hash(senha)

def verificar_senha(senha: str, senha_hash: str) -> bool:
    try:
        return _hasher.verify(senha, senha_hash)
    except PwdlibError:
        return False

class TokenInvalidoError(Exception):
    pass

def criar_token_acesso(pessoa: Pessoa) -> str:
    settings = get_settings()
    agora = datetime.now(UTC)
    payload = {
        "sub": pessoa.codigo,
        "iat": agora,
        "exp": agora + timedelta(minutes=settings.jwt_expire_minutes)
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)

def decodificar_token(token: str) -> dict:
    settings = get_settings()
    try:
        return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm],
                          options={"require": ["sub", "exp", "iat"]})
    except jwt.PyJWTError as exc:
        raise TokenInvalidoError from exc