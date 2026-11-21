"""Camada "Controller" do MVC: /usuarios (SEC01, SEC04, SEC05).

Cadastro feito pelo Bibliotecário, com a senha digitada pelo próprio usuário; o papel nunca
vem do cliente; só o Leitor vê os próprios dados; mudança de papel é uma operação à parte.
"""

import pytest
from pwdlib import PasswordHash
from sqlalchemy import select

from app.models import Auditoria, Pessoa
from tests.auth.conftest import SENHA

pytestmark = pytest.mark.integracao


def _novo(**kw) -> dict:
    base = dict(
        nome="Ana Souza", matricula="2026001", email="ana@escola.edu",
        telefone="48999990000", senha="senha-da-ana-123",
    )  # fmt: skip
    return {**base, **kw}


def _do_banco(session, matricula: str) -> Pessoa:
    return session.scalars(select(Pessoa).where(Pessoa.matricula == matricula)).one()


# --- SEC01: cadastro -------------------------------------------------------------------------


def test_bibliotecario_cadastra_leitor(db_client, bibliotecario, cabecalho):
    resp = db_client.post("/usuarios", json=_novo(), headers=cabecalho(bibliotecario))

    assert resp.status_code == 201
    corpo = resp.json()
    assert corpo["codigo"].startswith("cus_")
    assert (corpo["papel"], corpo["ativo"]) == ("LEITOR", True)
    assert corpo["email"] == "ana@escola.edu"


def test_cadastro_guarda_somente_o_hash_da_senha(db_client, db_session, bibliotecario, cabecalho):
    db_client.post("/usuarios", json=_novo(), headers=cabecalho(bibliotecario))

    pessoa = _do_banco(db_session, "2026001")
    assert pessoa.senha_hash != "senha-da-ana-123"
    assert pessoa.senha_hash.startswith("$argon2id$")
    assert PasswordHash.recommended().verify("senha-da-ana-123", pessoa.senha_hash)


def test_resposta_do_cadastro_nao_tem_senha_hash_nem_token(db_client, bibliotecario, cabecalho):
    resp = db_client.post("/usuarios", json=_novo(), headers=cabecalho(bibliotecario))

    assert "senha" not in resp.text and "argon2" not in resp.text
    assert "access_token" not in resp.text and "set-cookie" not in resp.headers


def test_cadastro_pelo_bibliotecario_sem_papel_cria_leitor(
    db_client, db_session, bibliotecario, cabecalho
):
    resp = db_client.post("/usuarios", json=_novo(), headers=cabecalho(bibliotecario))

    assert resp.json()["papel"] == "LEITOR"
    assert _do_banco(db_session, "2026001").papel == "LEITOR"


def test_bibliotecario_cadastra_outro_bibliotecario(
    db_client, db_session, bibliotecario, cabecalho
):
    resp = db_client.post(
        "/usuarios", json=_novo(papel="BIBLIOTECARIO"), headers=cabecalho(bibliotecario)
    )

    assert resp.status_code == 201
    assert resp.json()["papel"] == "BIBLIOTECARIO"
    assert _do_banco(db_session, "2026001").papel == "BIBLIOTECARIO"


def test_leitor_nao_cadastra_bibliotecario(db_client, db_session, leitor, cabecalho):
    resp = db_client.post("/usuarios", json=_novo(papel="BIBLIOTECARIO"), headers=cabecalho(leitor))

    assert resp.status_code == 403
    assert db_session.scalars(select(Pessoa).where(Pessoa.matricula == "2026001")).first() is None


def test_cadastro_com_papel_desconhecido_retorna_422(db_client, bibliotecario, cabecalho):
    resp = db_client.post("/usuarios", json=_novo(papel="ADMIN"), headers=cabecalho(bibliotecario))

    assert resp.status_code == 422


# --- cadastro público de leitor (/auth/registro) ---------------------------------------------


def test_registro_publico_cria_leitor_sem_autenticacao(db_client, db_session):
    resp = db_client.post("/auth/registro", json=_novo())

    assert resp.status_code == 201
    assert (resp.json()["papel"], resp.json()["ativo"]) == ("LEITOR", True)
    assert "senha" not in resp.text and "argon2" not in resp.text
    assert _do_banco(db_session, "2026001").senha_hash.startswith("$argon2id$")


def test_registro_publico_ignora_papel_enviado(db_client, db_session):
    resp = db_client.post("/auth/registro", json=_novo(papel="BIBLIOTECARIO"))

    assert resp.status_code == 201
    assert resp.json()["papel"] == "LEITOR"
    assert _do_banco(db_session, "2026001").papel == "LEITOR"


def test_registro_publico_permite_login_com_a_senha_definida(db_client, login):
    db_client.post("/auth/registro", json=_novo())

    assert login("ana@escola.edu", "senha-da-ana-123").status_code == 200


@pytest.mark.parametrize("duplicado", [{"email": "ANA@escola.edu"}, {"matricula": "2026001"}])
def test_registro_publico_duplicado_retorna_409(db_client, duplicado):
    db_client.post("/auth/registro", json=_novo())

    unicos = {"matricula": "2026002", "email": "outra@escola.edu"}
    outro = _novo(nome="Outra", **{**unicos, **duplicado})
    resp = db_client.post("/auth/registro", json=outro)

    assert resp.status_code == 409
    assert resp.json()["detail"] == "E-mail ou matrícula já cadastrados"


@pytest.mark.parametrize("campo", ["nome", "matricula", "email", "senha"])
def test_registro_publico_exige_campos_obrigatorios(db_client, campo):
    corpo = _novo()
    del corpo[campo]

    assert db_client.post("/auth/registro", json=corpo).status_code == 422


def test_registro_publico_recusa_email_invalido(db_client):
    assert db_client.post("/auth/registro", json=_novo(email="nao-e-email")).status_code == 422


def test_registro_publico_e_auditado_com_o_proprio_cadastrado(db_client, db_session):
    db_client.post("/auth/registro", json=_novo())

    pessoa = _do_banco(db_session, "2026001")
    (reg,) = db_session.scalars(
        select(Auditoria).where(Auditoria.acao == "CADASTRO", Auditoria.entidade_id == pessoa.id,
                                Auditoria.entidade == "PESSOA")
    ).all()  # fmt: skip
    assert reg.responsavel_id == pessoa.id
    assert "senha" not in str(reg.dados or {}).lower()


def test_cadastro_nao_altera_a_sessao_de_quem_atende(db_client, bibliotecario, cabecalho):
    headers = cabecalho(bibliotecario)

    db_client.post("/usuarios", json=_novo(), headers=headers)

    assert db_client.get("/auth/me", headers=headers).json()["codigo"] == bibliotecario.codigo


def test_leitor_recem_cadastrado_entra_com_a_senha_que_ele_mesmo_definiu(
    db_client, login, bibliotecario, cabecalho
):
    db_client.post("/usuarios", json=_novo(), headers=cabecalho(bibliotecario))

    resp = login("ana@escola.edu", "senha-da-ana-123")
    me = db_client.get(
        "/auth/me", headers={"Authorization": f"Bearer {resp.json()['access_token']}"}
    )

    assert resp.status_code == 200
    assert (me.json()["papel"], me.json()["matricula"]) == ("LEITOR", "2026001")


@pytest.mark.parametrize(
    "duplicado",
    [{"matricula": "MAT-1"}, {"email": "USUARIO1@ESCOLA.EDU"}],
    ids=["matricula", "email_sem_diferenciar_maiusculas"],
)
def test_cadastro_duplicado_retorna_409(
    db_client, cria_usuario, bibliotecario, cabecalho, duplicado
):
    cria_usuario(matricula="MAT-1", email="usuario1@escola.edu")

    resp = db_client.post("/usuarios", json=_novo(**duplicado), headers=cabecalho(bibliotecario))

    assert resp.status_code == 409


@pytest.mark.parametrize("campo", ["nome", "matricula", "email", "senha"])
def test_cadastro_exige_campos_obrigatorios(db_client, bibliotecario, cabecalho, campo):
    corpo = _novo()
    del corpo[campo]
    assert (
        db_client.post("/usuarios", json=corpo, headers=cabecalho(bibliotecario)).status_code == 422
    )


def test_cadastro_e_auditado_sem_dados_sensiveis(db_client, db_session, bibliotecario, cabecalho):
    db_client.post("/usuarios", json=_novo(), headers=cabecalho(bibliotecario))

    pessoa = _do_banco(db_session, "2026001")
    (reg,) = db_session.scalars(
        select(Auditoria).where(Auditoria.acao == "CADASTRO", Auditoria.entidade == "PESSOA",
                                Auditoria.entidade_id == pessoa.id)
    ).all()  # fmt: skip
    assert reg.responsavel_id == bibliotecario.id
    assert "senha" not in str(reg.dados or {}).lower()
    assert "argon2" not in str(reg.dados or {})


def test_leitor_nao_cadastra_usuarios(db_client, db_session, leitor, cabecalho):
    resp = db_client.post("/usuarios", json=_novo(), headers=cabecalho(leitor))

    assert resp.status_code == 403
    assert db_session.scalars(select(Pessoa).where(Pessoa.matricula == "2026001")).first() is None


# --- SEC04: leitor só enxerga os próprios registros ------------------------------------------


def test_leitor_consulta_os_proprios_dados(db_client, leitor, cabecalho):
    resp = db_client.get(f"/usuarios/{leitor.codigo}", headers=cabecalho(leitor))

    assert resp.status_code == 200
    assert resp.json()["codigo"] == leitor.codigo


def test_leitor_nao_consulta_dados_de_outro_leitor(db_client, leitor, outro_leitor, cabecalho):
    resp = db_client.get(f"/usuarios/{outro_leitor.codigo}", headers=cabecalho(leitor))

    assert resp.status_code == 403
    assert outro_leitor.email not in resp.text


@pytest.mark.parametrize("filtro", [{}, {"nome": "Otto"}, {"papel": "BIBLIOTECARIO"}])
def test_lista_do_leitor_so_traz_ele_mesmo_mesmo_com_filtros(
    db_client, leitor, outro_leitor, bibliotecario, cabecalho, filtro
):
    resp = db_client.get("/usuarios", params=filtro, headers=cabecalho(leitor))

    assert resp.status_code == 200
    assert {u["codigo"] for u in resp.json()} <= {leitor.codigo}


def test_bibliotecario_lista_e_consulta_qualquer_usuario(
    db_client, leitor, outro_leitor, bibliotecario, cabecalho
):
    headers = cabecalho(bibliotecario)

    codigos = {u["codigo"] for u in db_client.get("/usuarios", headers=headers).json()}
    unico = db_client.get(f"/usuarios/{outro_leitor.codigo}", headers=headers)

    assert {leitor.codigo, outro_leitor.codigo, bibliotecario.codigo} <= codigos
    assert unico.status_code == 200


def test_bibliotecario_recebe_404_para_usuario_inexistente(db_client, bibliotecario, cabecalho):
    resp = db_client.get("/usuarios/cus_99999999", headers=cabecalho(bibliotecario))
    assert resp.status_code == 404


@pytest.mark.parametrize(
    "metodo, rota, corpo",
    [
        ("post", "/usuarios", _novo()),
        ("get", "/usuarios", None),
        ("get", "/usuarios/cus_00000001", None),
        ("patch", "/usuarios/cus_00000001", {"nome": "X"}),
        ("put", "/usuarios/cus_00000001/papel", {"papel": "BIBLIOTECARIO"}),
    ],
)
def test_rotas_de_usuarios_exigem_autenticacao(db_client, metodo, rota, corpo):
    resp = getattr(db_client, metodo)(rota, **({"json": corpo} if corpo else {}))
    assert resp.status_code == 401


# --- edição cadastral: papel não muda por aqui (SEC04/SEC05) ---------------------------------


def test_bibliotecario_edita_dados_cadastrais(db_client, leitor, bibliotecario, cabecalho):
    resp = db_client.patch(
        f"/usuarios/{leitor.codigo}", json={"nome": "Lia Nova"}, headers=cabecalho(bibliotecario)
    )

    assert resp.status_code == 200
    assert resp.json()["nome"] == "Lia Nova"


def test_leitor_nao_edita_nem_o_proprio_cadastro(db_client, db_session, leitor, cabecalho):
    resp = db_client.patch(
        f"/usuarios/{leitor.codigo}", json={"nome": "Outro Nome"}, headers=cabecalho(leitor)
    )

    assert resp.status_code == 403


def test_leitor_nao_altera_o_proprio_papel_pelo_corpo_da_requisicao(
    db_client, db_session, leitor, cabecalho
):
    resp = db_client.patch(
        f"/usuarios/{leitor.codigo}", json={"papel": "BIBLIOTECARIO"}, headers=cabecalho(leitor)
    )

    assert resp.status_code == 403
    db_session.refresh(leitor)
    assert leitor.papel == "LEITOR"


def test_edicao_cadastral_do_bibliotecario_tambem_ignora_papel(
    db_client, db_session, leitor, bibliotecario, cabecalho
):
    resp = db_client.patch(
        f"/usuarios/{leitor.codigo}",
        json={"nome": "Lia", "papel": "BIBLIOTECARIO"},
        headers=cabecalho(bibliotecario),
    )

    assert resp.status_code in (200, 422)
    db_session.refresh(leitor)
    assert leitor.papel == "LEITOR"


# --- SEC01/SEC04: mudança de papel em operação específica ------------------------------------


def test_bibliotecario_promove_leitor_a_bibliotecario(
    db_client, db_session, leitor, bibliotecario, cabecalho
):
    resp = db_client.put(
        f"/usuarios/{leitor.codigo}/papel",
        json={"papel": "BIBLIOTECARIO"},
        headers=cabecalho(bibliotecario),
    )

    assert resp.status_code == 200
    assert resp.json()["papel"] == "BIBLIOTECARIO"
    db_session.refresh(leitor)
    assert leitor.papel == "BIBLIOTECARIO"


def test_novo_bibliotecario_ja_consegue_executar_operacoes_de_gestao(
    db_client, leitor, bibliotecario, cabecalho
):
    db_client.put(
        f"/usuarios/{leitor.codigo}/papel",
        json={"papel": "BIBLIOTECARIO"},
        headers=cabecalho(bibliotecario),
    )

    resp = db_client.post("/usuarios", json=_novo(), headers=cabecalho(leitor))

    assert resp.status_code == 201


def test_mudanca_de_papel_e_auditada(db_client, db_session, leitor, bibliotecario, cabecalho):
    db_client.put(
        f"/usuarios/{leitor.codigo}/papel",
        json={"papel": "BIBLIOTECARIO"},
        headers=cabecalho(bibliotecario),
    )

    (reg,) = db_session.scalars(
        select(Auditoria).where(Auditoria.acao == "ALTERACAO", Auditoria.entidade_id == leitor.id)
    ).all()
    assert reg.responsavel_id == bibliotecario.id
    assert "BIBLIOTECARIO" in str(reg.dados)


def test_leitor_nao_muda_papel_de_ninguem_nem_o_proprio(
    db_client, db_session, leitor, outro_leitor, cabecalho
):
    for alvo in (leitor, outro_leitor):
        resp = db_client.put(
            f"/usuarios/{alvo.codigo}/papel",
            json={"papel": "BIBLIOTECARIO"},
            headers=cabecalho(leitor),
        )
        assert resp.status_code == 403
        db_session.refresh(alvo)
        assert alvo.papel == "LEITOR"


@pytest.mark.parametrize("papel", ["ADMIN", "leitor", ""])
def test_mudanca_para_papel_desconhecido_retorna_422(
    db_client, leitor, bibliotecario, cabecalho, papel
):
    resp = db_client.put(
        f"/usuarios/{leitor.codigo}/papel", json={"papel": papel}, headers=cabecalho(bibliotecario)
    )
    assert resp.status_code == 422


def test_mudanca_de_papel_de_usuario_inexistente_retorna_404(db_client, bibliotecario, cabecalho):
    resp = db_client.put(
        "/usuarios/cus_99999999/papel",
        json={"papel": "LEITOR"},
        headers=cabecalho(bibliotecario),
    )
    assert resp.status_code == 404


# --- conta inativa não opera, mesmo com token ainda válido -----------------------------------


def test_bibliotecario_inativo_nao_opera(db_client, cria_usuario, cabecalho):
    inativo = cria_usuario(papel="BIBLIOTECARIO", ativo=False)
    assert db_client.get("/usuarios", headers=cabecalho(inativo)).status_code == 401


def test_senha_do_leitor_cadastrado_pelo_operador_nao_e_a_do_operador(
    db_client, login, bibliotecario, cabecalho
):
    """O operador não define a senha de quem ele cadastra (SEC01): só a senha enviada vale."""
    db_client.post("/usuarios", json=_novo(), headers=cabecalho(bibliotecario))

    assert login("ana@escola.edu", SENHA).status_code == 401  # senha do operador não serve
    assert login("ana@escola.edu", "senha-da-ana-123").status_code == 200
