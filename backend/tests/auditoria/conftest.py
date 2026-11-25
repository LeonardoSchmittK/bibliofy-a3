"""Fixtures dos testes de auditoria (issue de auditoria; wiki RNF10 e SEC05).

Depende do contrato de autenticação da issue #35 (token JWT HS256 com `sub` = `pessoa.codigo`,
chave em `get_settings().jwt_secret`, dependência `exige_bibliotecario`). Os tokens são gerados
aqui com PyJWT, sem usar código de `app/`.

Contrato (ajustar aqui e nos TODOs de `app/` se o time decidir outro):

- Escrita: `app.services.auditoria.registrar` (criado na #35) é a ÚNICA porta de entrada;
  grava na mesma transação da operação auditada, sem commit próprio.
- Leitura: `GET /auditoria` (lista paginada, filtros) e `GET /auditoria/{id}`, só Bibliotecário.
- Imutabilidade: a API não tem POST/PUT/PATCH/DELETE e o banco recusa UPDATE, DELETE e TRUNCATE.
- 401 sem autenticação válida, 403 para o Leitor, 404 inexistente, 422 filtro inválido.
"""

from datetime import UTC, datetime, timedelta
from itertools import count

import jwt
import pytest
import time_machine

from app.models import Auditoria, Pessoa

AGORA = datetime(2026, 3, 10, 12, 0, tzinfo=UTC)
_seq = count(1)


@pytest.fixture(autouse=True)
def _relogio_congelado():
    with time_machine.travel(AGORA, tick=False):
        yield


@pytest.fixture
def cria_usuario(db_session):
    def _cria(*, papel="LEITOR", ativo=True, **kw) -> Pessoa:
        n = next(_seq)
        campos = dict(
            matricula=f"mat{n}", nome=f"Usuario {n}", email=f"usuario{n}@escola.edu",
            senha_hash="hash-que-nao-e-usado-aqui", papel=papel, ativo=ativo,
        )  # fmt: skip
        pessoa = Pessoa(**{**campos, **kw})
        db_session.add(pessoa)
        db_session.flush()
        return pessoa

    return _cria


@pytest.fixture
def bibliotecario(cria_usuario):
    return cria_usuario(papel="BIBLIOTECARIO", nome="Bia Bibliotecária")


@pytest.fixture
def leitor(cria_usuario):
    return cria_usuario(nome="Lia Leitora")


@pytest.fixture
def cria_registro(db_session, bibliotecario):
    """Insere uma linha direto em `auditoria` (sem passar pelo serviço sob teste)."""

    def _cria(*, responsavel=None, minutos_atras=0, **kw) -> Auditoria:
        campos = dict(
            responsavel_id=(responsavel or bibliotecario).id,
            acao="CADASTRO", entidade="LIVRO", entidade_id=1, dados={"nome": "Livro"},
            criado_em=AGORA - timedelta(minutes=minutos_atras),
        )  # fmt: skip
        registro = Auditoria(**{**campos, **kw})
        db_session.add(registro)
        db_session.flush()
        return registro

    return _cria


@pytest.fixture
def cabecalho():
    def _cabecalho(pessoa: Pessoa) -> dict[str, str]:
        from app.core.config import get_settings

        token = jwt.encode(
            {"sub": pessoa.codigo, "iat": AGORA, "exp": AGORA + timedelta(minutes=15)},
            get_settings().jwt_secret,  # ainda não existe: fica vermelho
            algorithm="HS256",
        )
        return {"Authorization": f"Bearer {token}"}

    return _cabecalho


@pytest.fixture
def api(db_client, bibliotecario, cabecalho):
    """Cliente autenticado como bibliotecário. Para o leitor: `headers=cabecalho(leitor)`."""
    db_client.headers.update(cabecalho(bibliotecario))
    return db_client
