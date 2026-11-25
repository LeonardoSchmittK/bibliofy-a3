"""Camada "Controller" do MVC: /auth/login, /auth/me e /auth/logout (SEC02, SEC03, SEC04)."""

import logging
from datetime import timedelta

import jwt
import pytest
import time_machine

from app.models import Bloqueio, Emprestimo, Livro
from tests.auth.conftest import AGORA, SENHA

pytestmark = pytest.mark.integracao


def _livro(session) -> Livro:
    livro = Livro(
        isbn="9783161484100", nome="L", autor="A", editora="E", genero="G",
        data_lancamento=AGORA.date(), quantidade_total=1,
    )  # fmt: skip
    session.add(livro)
    session.flush()
    return livro


# --- login: caminho feliz --------------------------------------------------------------------


def test_login_valido_devolve_bearer_token(login, leitor):
    resp = login(leitor.email)

    assert resp.status_code == 200
    corpo = resp.json()
    assert corpo["token_type"] == "bearer"
    assert corpo["access_token"].count(".") == 2  # JWT: header.payload.assinatura


def test_token_do_login_identifica_o_usuario_e_expira_em_ate_15_minutos(login, leitor):
    from app.core.config import get_settings

    token = login(leitor.email).json()["access_token"]

    claims = jwt.decode(token, get_settings().jwt_secret, algorithms=["HS256"])
    assert claims["sub"] == leitor.codigo
    assert claims["iat"] == int(AGORA.timestamp())
    assert timedelta(seconds=claims["exp"] - claims["iat"]) <= timedelta(minutes=15)


def test_login_nao_diferencia_maiusculas_no_email(login, leitor):
    assert login(leitor.email.upper()).status_code == 200


def test_login_do_bibliotecario(login, bibliotecario):
    assert login(bibliotecario.email).status_code == 200


def test_resposta_do_login_nao_expoe_senha_nem_hash(login, leitor):
    texto = login(leitor.email).text

    assert SENHA not in texto
    assert leitor.senha_hash not in texto
    assert "senha_hash" not in texto


def test_senha_continua_guardada_como_hash_apos_o_login(login, db_session, leitor):
    login(leitor.email)
    db_session.refresh(leitor)
    assert leitor.senha_hash.startswith("$argon2id$") and leitor.senha_hash != SENHA


# --- login: recusas (sempre 401 genérico, sem revelar se a conta existe) ---------------------


def test_login_com_senha_incorreta(login, leitor):
    resp = login(leitor.email, "senha-errada")

    assert resp.status_code == 401
    assert resp.headers["WWW-Authenticate"] == "Bearer"
    assert "access_token" not in resp.text


def test_login_com_email_inexistente(login):
    assert login("ninguem@escola.edu").status_code == 401


def test_mensagem_de_erro_e_identica_para_senha_errada_email_inexistente_e_conta_inativa(
    login, leitor, cria_usuario
):
    inativo = cria_usuario(ativo=False)

    respostas = [
        login(leitor.email, "senha-errada"),
        login("ninguem@escola.edu"),
        login(inativo.email),  # senha correta, mas conta inativa
    ]

    assert {r.status_code for r in respostas} == {401}
    assert len({r.text for r in respostas}) == 1


@pytest.mark.parametrize("faltando", ["username", "password"])
def test_login_exige_email_e_senha(db_client, leitor, faltando):
    dados = {"username": leitor.email, "password": SENHA}
    del dados[faltando]

    assert db_client.post("/auth/login", data=dados).status_code == 422


def test_login_nao_registra_senha_nem_token_nos_logs(login, leitor, caplog):
    caplog.set_level(logging.DEBUG)

    token = login(leitor.email).json()["access_token"]
    login(leitor.email, "senha-errada-123")

    assert SENHA not in caplog.text
    assert "senha-errada-123" not in caplog.text
    assert token not in caplog.text
    assert leitor.senha_hash not in caplog.text


# --- penalidade não bloqueia login nem consulta (SEC04) --------------------------------------


def test_leitor_com_penalidade_vigente_ainda_faz_login_e_consulta_seus_dados(
    db_client, db_session, login, leitor
):
    atrasado = Emprestimo(
        pessoa_id=leitor.id, livro_id=_livro(db_session).id,
        data_emprestimo=AGORA.date() - timedelta(days=40),
        data_prevista=AGORA.date() - timedelta(days=15),
        data_devolucao=AGORA.date(), status_atual="DEVOLVIDO_COM_ATRASO",
    )  # fmt: skip
    db_session.add(atrasado)
    db_session.flush()
    db_session.add(
        Bloqueio(
            pessoa_id=leitor.id,
            emprestimo_id=atrasado.id,
            inicio=AGORA.date(),
            fim_exclusivo=AGORA.date() + timedelta(days=10),
            motivo="atraso",
        )  # fmt: skip
    )
    db_session.flush()

    resp = login(leitor.email)
    me = db_client.get(
        "/auth/me", headers={"Authorization": f"Bearer {resp.json()['access_token']}"}
    )

    assert resp.status_code == 200
    assert me.status_code == 200


# --- GET /auth/me ----------------------------------------------------------------------------


def test_me_retorna_identificacao_e_perfil(db_client, leitor, cabecalho):
    resp = db_client.get("/auth/me", headers=cabecalho(leitor))

    assert resp.status_code == 200
    assert resp.json() == {
        "codigo": leitor.codigo, "matricula": leitor.matricula, "nome": leitor.nome,
        "email": leitor.email, "telefone": None, "papel": "LEITOR", "ativo": True,
    }  # fmt: skip


def test_me_do_bibliotecario_mostra_o_papel(db_client, bibliotecario, cabecalho):
    resp = db_client.get("/auth/me", headers=cabecalho(bibliotecario))
    assert resp.json()["papel"] == "BIBLIOTECARIO"


def test_me_nunca_expoe_senha_nem_hash(db_client, leitor, cabecalho):
    texto = db_client.get("/auth/me", headers=cabecalho(leitor)).text
    assert "senha" not in texto and "argon2" not in texto


def test_me_usa_a_identidade_do_token_e_ignora_o_que_o_cliente_informa(
    db_client, leitor, outro_leitor, cabecalho
):
    resp = db_client.get(
        "/auth/me", params={"codigo": outro_leitor.codigo}, headers=cabecalho(leitor)
    )
    assert resp.json()["codigo"] == leitor.codigo


@pytest.mark.parametrize(
    "caso", ["sem_token", "token_lixo", "expirado", "adulterado", "conta_inativa"]
)
def test_me_recusa_autenticacao_invalida(
    db_client, cria_usuario, cabecalho, emite_token, adultera, caso
):
    pessoa = cria_usuario(ativo=(caso != "conta_inativa"))
    headers = {
        "sem_token": {},
        "token_lixo": {"Authorization": "Bearer lixo"},
        "expirado": cabecalho(pessoa, minutos=-1),
        "adulterado": {
            "Authorization": "Bearer " + adultera(emite_token(pessoa), sub="cus_00000099")
        },
        "conta_inativa": cabecalho(pessoa),
    }[caso]

    resp = db_client.get("/auth/me", headers=headers)

    assert resp.status_code == 401


# --- POST /auth/logout (sem estado no servidor: SEC03) ---------------------------------------


def test_logout_responde_204(db_client, leitor, cabecalho):
    assert db_client.post("/auth/logout", headers=cabecalho(leitor)).status_code == 204


def test_logout_nao_invalida_copia_do_token_ate_expirar(db_client, leitor, cabecalho):
    """Decisão documentada em SEC03: não há refresh token nem tabela de sessões."""
    headers = cabecalho(leitor)

    db_client.post("/auth/logout", headers=headers)

    assert db_client.get("/auth/me", headers=headers).status_code == 200


def test_logout_sem_token_retorna_401(db_client):
    assert db_client.post("/auth/logout").status_code == 401


# --- fluxo completo --------------------------------------------------------------------------


def test_fluxo_login_me_logout_e_novo_login_apos_expirar(db_client, login, leitor):
    token = login(leitor.email).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    assert db_client.get("/auth/me", headers=headers).json()["codigo"] == leitor.codigo
    assert db_client.post("/auth/logout", headers=headers).status_code == 204

    with time_machine.travel(AGORA + timedelta(minutes=16), tick=False):
        assert db_client.get("/auth/me", headers=headers).status_code == 401  # recarregou: relogar
        assert login(leitor.email).status_code == 200
