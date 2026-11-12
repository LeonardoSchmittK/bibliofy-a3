"""Fixtures dos testes de autenticação (issue #35, requisitos SEC01-SEC05 da issue #13).

Contrato que a implementação deve cumprir (os TODOs nos arquivos de `app/` seguem o mesmo):

- Login: `POST /auth/login`, formulário OAuth2 (`username` = e-mail, `password` = senha).
  Resposta 200: `{"access_token", "token_type": "bearer"}`. Falha: 401 genérico.
- Usuário atual: `GET /auth/me`. Logout: `POST /auth/logout` (204, sem estado no servidor).
- Usuários (rotas de gestão, só Bibliotecário): `POST /usuarios`, `GET /usuarios`,
  `GET /usuarios/{codigo}`, `PATCH /usuarios/{codigo}`, `PUT /usuarios/{codigo}/papel`.
- JWT HS256: claims `sub` (= `pessoa.codigo`), `iat` e `exp` (no máximo 15 min depois de `iat`).
- 401 = autenticação inválida (sem token, adulterado, expirado, conta inativa);
  403 = autenticado, mas sem permissão.

Os tokens e hashes das fixtures são gerados direto com PyJWT/pwdlib, sem usar código de `app/`,
para que cada camada possa ser testada sem depender das outras.
"""

import base64
import json
from datetime import UTC, datetime, timedelta
from itertools import count

import jwt
import pytest
import time_machine
from pwdlib import PasswordHash

from app.models import Pessoa

SENHA = "senha-forte-123"
AGORA = datetime(2026, 3, 10, 12, 0, tzinfo=UTC)
_seq = count(1)


def _segredo() -> str:
    from app.core.config import get_settings

    return get_settings().jwt_secret  # ainda não existe: fica vermelho


@pytest.fixture(autouse=True)
def agora():
    """Congela o relógio: expiração do JWT é testada viajando no tempo."""
    with time_machine.travel(AGORA, tick=False):
        yield AGORA


@pytest.fixture
def cria_usuario(db_session):
    def _cria(*, papel="LEITOR", ativo=True, senha=SENHA, **kw) -> Pessoa:
        n = next(_seq)
        campos = dict(
            matricula=f"mat{n}", nome=f"Usuario {n}", email=f"usuario{n}@escola.edu",
            senha_hash=PasswordHash.recommended().hash(senha), papel=papel, ativo=ativo,
        )  # fmt: skip
        pessoa = Pessoa(**{**campos, **kw})
        db_session.add(pessoa)
        db_session.flush()
        return pessoa

    return _cria


@pytest.fixture
def leitor(cria_usuario):
    return cria_usuario(nome="Lia Leitora")


@pytest.fixture
def outro_leitor(cria_usuario):
    return cria_usuario(nome="Otto Outro")


@pytest.fixture
def bibliotecario(cria_usuario):
    return cria_usuario(papel="BIBLIOTECARIO", nome="Bia Bibliotecária")


@pytest.fixture
def emite_token(agora):
    def _emite(pessoa, *, minutos=15, segredo=None, algoritmo="HS256", **claims) -> str:
        carga = {
            "sub": pessoa.codigo,
            "iat": agora,
            "exp": agora + timedelta(minutes=minutos),
            **claims,
        }
        return jwt.encode(carga, segredo or _segredo(), algorithm=algoritmo)

    return _emite


@pytest.fixture
def cabecalho(emite_token):
    def _cabecalho(pessoa, **kw) -> dict[str, str]:
        return {"Authorization": f"Bearer {emite_token(pessoa, **kw)}"}

    return _cabecalho


@pytest.fixture
def login(db_client):
    def _login(email: str, senha: str = SENHA):
        return db_client.post("/auth/login", data={"username": email, "password": senha})

    return _login


def _b64(dados: dict) -> str:
    bruto = json.dumps(dados, separators=(",", ":")).encode()
    return base64.urlsafe_b64encode(bruto).rstrip(b"=").decode()


@pytest.fixture
def adultera():
    """Troca claims do payload mantendo a assinatura original (assinatura passa a ser inválida)."""

    def _adultera(token: str, **claims) -> str:
        cabecalho, payload, assinatura = token.split(".")
        padding = "=" * (-len(payload) % 4)
        dados = json.loads(base64.urlsafe_b64decode(payload + padding))
        return ".".join([cabecalho, _b64({**dados, **claims}), assinatura])

    return _adultera
