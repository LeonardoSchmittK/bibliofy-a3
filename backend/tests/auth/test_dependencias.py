"""SEC04: dependências reutilizáveis do FastAPI, testadas numa mini-aplicação.

Contrato de `app.api.deps`:
- usuario_autenticado: valida o JWT (Bearer), busca a pessoa pelo `sub` e exige conta ativa.
  Qualquer falha => 401 com `WWW-Authenticate: Bearer`. Retorna o `Pessoa` do banco.
- exige_bibliotecario: usa `usuario_autenticado` e exige papel BIBLIOTECARIO => senão 403.
  O papel vem do BANCO, nunca de claims do token.
"""

from types import SimpleNamespace
from typing import Annotated

import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from app.db.session import get_db
from app.models import Pessoa

pytestmark = pytest.mark.integracao


@pytest.fixture
def mini_api(db_session):
    from app.api.deps import exige_bibliotecario, usuario_autenticado

    app = FastAPI()

    @app.get("/_autenticado")
    def autenticado(usuario: Annotated[Pessoa, Depends(usuario_autenticado)]):
        return {"codigo": usuario.codigo, "papel": usuario.papel}

    @app.get("/_bibliotecario")
    def so_bibliotecario(usuario: Annotated[Pessoa, Depends(exige_bibliotecario)]):
        return {"codigo": usuario.codigo}

    app.dependency_overrides[get_db] = lambda: db_session
    with TestClient(app) as client:
        yield client


# --- usuario_autenticado: tudo que invalida a autenticação vira 401 --------------------------


def _quebrados(leitor, emite_token, adultera):
    return {
        "sem_cabecalho": {},
        "esquema_basic": {"Authorization": "Basic YTpi"},
        "token_lixo": {"Authorization": "Bearer abc.def.ghi"},
        "assinatura_de_outra_chave": {
            "Authorization": "Bearer "
            + emite_token(leitor, segredo="chave-de-outro-sistema-0123456789abc")
        },
        "expirado": {"Authorization": "Bearer " + emite_token(leitor, minutos=-1)},
        "adulterado": {
            "Authorization": "Bearer " + adultera(emite_token(leitor), sub="cus_00000099")
        },
        "pessoa_inexistente": {
            "Authorization": "Bearer " + emite_token(SimpleNamespace(codigo="cus_99999999"))
        },
    }


@pytest.mark.parametrize(
    "caso",
    [
        "sem_cabecalho", "esquema_basic", "token_lixo", "assinatura_de_outra_chave",
        "expirado", "adulterado", "pessoa_inexistente",
    ],
)  # fmt: skip
@pytest.mark.parametrize("rota", ["/_autenticado", "/_bibliotecario"])
def test_autenticacao_invalida_retorna_401(mini_api, leitor, emite_token, adultera, rota, caso):
    cabecalhos = _quebrados(leitor, emite_token, adultera)[caso]

    resp = mini_api.get(rota, headers=cabecalhos)

    assert resp.status_code == 401
    assert resp.headers["WWW-Authenticate"] == "Bearer"


def test_conta_inativa_com_token_valido_retorna_401(mini_api, cria_usuario, cabecalho):
    inativo = cria_usuario(ativo=False)
    assert mini_api.get("/_autenticado", headers=cabecalho(inativo)).status_code == 401


def test_conta_desativada_depois_da_emissao_perde_acesso(mini_api, db_session, leitor, cabecalho):
    headers = cabecalho(leitor)
    assert mini_api.get("/_autenticado", headers=headers).status_code == 200

    leitor.ativo = False
    db_session.flush()

    assert mini_api.get("/_autenticado", headers=headers).status_code == 401


def test_usuario_autenticado_entrega_a_pessoa_do_token(mini_api, leitor, cabecalho):
    resp = mini_api.get("/_autenticado", headers=cabecalho(leitor))

    assert resp.status_code == 200
    assert resp.json() == {"codigo": leitor.codigo, "papel": "LEITOR"}


# --- exige_bibliotecario: 403 para quem está autenticado mas não tem o papel -----------------


def test_leitor_recebe_403_na_rota_de_bibliotecario(mini_api, leitor, cabecalho):
    assert mini_api.get("/_bibliotecario", headers=cabecalho(leitor)).status_code == 403


def test_bibliotecario_acessa_a_rota_de_bibliotecario(mini_api, bibliotecario, cabecalho):
    resp = mini_api.get("/_bibliotecario", headers=cabecalho(bibliotecario))

    assert resp.status_code == 200
    assert resp.json() == {"codigo": bibliotecario.codigo}


def test_papel_vem_do_banco_e_nao_do_token(mini_api, leitor, cabecalho):
    """Claim `papel` forjada no payload (mesmo com a chave certa) não promove ninguém."""
    headers = cabecalho(leitor, papel="BIBLIOTECARIO")
    assert mini_api.get("/_bibliotecario", headers=headers).status_code == 403


def test_bibliotecario_inativo_recebe_401_e_nao_403(mini_api, cria_usuario, cabecalho):
    inativo = cria_usuario(papel="BIBLIOTECARIO", ativo=False)
    assert mini_api.get("/_bibliotecario", headers=cabecalho(inativo)).status_code == 401


def test_promocao_vale_no_proximo_request_sem_novo_token(mini_api, db_session, leitor, cabecalho):
    headers = cabecalho(leitor)
    assert mini_api.get("/_bibliotecario", headers=headers).status_code == 403

    leitor.papel = "BIBLIOTECARIO"
    db_session.flush()

    assert mini_api.get("/_bibliotecario", headers=headers).status_code == 200
