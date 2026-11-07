"""Camada "Controller": rotas /auditoria (somente leitura, só Bibliotecário)."""

import pytest

pytestmark = pytest.mark.integracao


def test_bibliotecario_lista_a_auditoria(api, cria_registro, bibliotecario):
    cria_registro(entidade_id=3, dados={"nome": "X"})

    resp = api.get("/auditoria")

    assert resp.status_code == 200
    corpo = resp.json()
    assert (corpo["total"], corpo["limite"], corpo["deslocamento"]) == (1, 50, 0)
    item = corpo["itens"][0]
    assert (item["acao"], item["entidade"], item["entidade_id"]) == ("CADASTRO", "LIVRO", 3)
    assert item["dados"] == {"nome": "X"}
    assert item["responsavel"] == {"codigo": bibliotecario.codigo, "nome": bibliotecario.nome}
    assert item["criado_em"].startswith("2026-03-10T12:00:00")


def test_lista_vem_do_mais_recente_para_o_mais_antigo(api, cria_registro):
    antigo = cria_registro(minutos_atras=10)
    recente = cria_registro(minutos_atras=1)

    ids = [i["id"] for i in api.get("/auditoria").json()["itens"]]

    assert ids == [recente.id, antigo.id]


def test_filtros_por_query_string(api, cria_registro):
    alvo = cria_registro(entidade="LIVRO", entidade_id=7, acao="ARQUIVAMENTO")
    cria_registro(entidade="LIVRO", entidade_id=8, acao="ARQUIVAMENTO")
    cria_registro(entidade="PESSOA", entidade_id=7, acao="CADASTRO")

    resp = api.get("/auditoria", params={"entidade": "LIVRO", "entidade_id": 7})
    assert [i["id"] for i in resp.json()["itens"]] == [alvo.id]

    resp = api.get("/auditoria", params={"acao": "ARQUIVAMENTO", "entidade": "LIVRO"})
    assert resp.json()["total"] == 2


def test_filtro_por_responsavel_e_periodo(api, cria_registro, cria_usuario):
    outro = cria_usuario(papel="BIBLIOTECARIO")
    alvo = cria_registro(responsavel=outro, minutos_atras=5)
    cria_registro(responsavel=outro, minutos_atras=120)
    cria_registro(minutos_atras=5)

    resp = api.get(
        "/auditoria",
        params={"responsavel": outro.codigo, "de": "2026-03-10T11:00:00+00:00"},
    )

    assert [i["id"] for i in resp.json()["itens"]] == [alvo.id]


def test_paginacao(api, cria_registro):
    for minutos in range(5):
        cria_registro(minutos_atras=minutos)

    corpo = api.get("/auditoria", params={"limite": 2, "deslocamento": 4}).json()

    assert (len(corpo["itens"]), corpo["total"], corpo["limite"], corpo["deslocamento"]) == (
        1, 5, 2, 4,
    )  # fmt: skip


@pytest.mark.parametrize(
    "params",
    [
        {"acao": "TROCAR"}, {"entidade": "USUARIO"}, {"limite": 0}, {"limite": 201},
        {"deslocamento": -1}, {"entidade_id": "abc"}, {"de": "ontem"},
        {"de": "2026-03-10T12:00:00+00:00", "ate": "2026-03-09T12:00:00+00:00"},
    ],
)  # fmt: skip
def test_filtro_invalido_da_422(api, params):
    assert api.get("/auditoria", params=params).status_code == 422


def test_obtem_registro_por_id(api, cria_registro):
    registro = cria_registro(acao="ALTERACAO", dados={"antes": {"a": 1}, "depois": {"a": 2}})

    resp = api.get(f"/auditoria/{registro.id}")

    assert resp.status_code == 200
    assert resp.json()["dados"] == {"antes": {"a": 1}, "depois": {"a": 2}}


def test_registro_inexistente_da_404(api):
    assert api.get("/auditoria/999999").status_code == 404


# --- autorização ---------------------------------------------------------------------------


def test_leitor_nao_consulta_a_auditoria(db_client, leitor, cabecalho, cria_registro):
    registro = cria_registro()
    headers = cabecalho(leitor)

    assert db_client.get("/auditoria", headers=headers).status_code == 403
    assert db_client.get(f"/auditoria/{registro.id}", headers=headers).status_code == 403


def test_anonimo_recebe_401(db_client, cria_registro):
    registro = cria_registro()

    assert db_client.get("/auditoria").status_code == 401
    assert db_client.get(f"/auditoria/{registro.id}").status_code == 401


def test_bibliotecario_inativo_recebe_401(db_client, cria_usuario, cabecalho):
    inativo = cria_usuario(papel="BIBLIOTECARIO", ativo=False)
    assert db_client.get("/auditoria", headers=cabecalho(inativo)).status_code == 401


# --- imutabilidade pela API ----------------------------------------------------------------


@pytest.mark.parametrize("metodo", ["post", "put", "patch", "delete"])
def test_api_nao_altera_a_auditoria(api, cria_registro, metodo):
    registro = cria_registro()

    assert getattr(api, metodo)(f"/auditoria/{registro.id}").status_code == 405
    assert getattr(api, metodo)("/auditoria").status_code == 405


def test_registro_continua_igual_apos_tentativas_de_alteracao(api, cria_registro):
    registro = cria_registro(acao="CADASTRO")
    api.patch(f"/auditoria/{registro.id}", json={"acao": "PERDA"})
    api.delete(f"/auditoria/{registro.id}")

    assert api.get(f"/auditoria/{registro.id}").json()["acao"] == "CADASTRO"
