"""Camada "Controller": rotas /livros (CRUD do Bibliotecário; Leitor só consulta).

Cobre RF01-RF04, RF14, RF18 e RF19 da wiki, mais autorização e auditoria.
"""

import pytest
from sqlalchemy import select

from app.models import Auditoria, Livro
from tests.livros.conftest import payload_livro

pytestmark = pytest.mark.integracao


def _do_banco(session, codigo: str) -> Livro:
    return session.scalars(select(Livro).where(Livro.codigo == codigo)).one()


# --- RF01: cadastrar -------------------------------------------------------------------------


def test_bibliotecario_cadastra_livro(api):
    resp = api.post("/livros", json=payload_livro())

    assert resp.status_code == 201
    corpo = resp.json()
    assert corpo["codigo"].startswith("liv_")
    assert corpo["nome"] == "Dom Casmurro"
    assert corpo["descricao"] == "Clássico da literatura brasileira"
    assert (corpo["arquivado"], corpo["quantidade_disponivel"]) == (False, 3)
    assert corpo["disponibilidade"] == "DISPONIVEL"


def test_cadastro_guarda_o_isbn_so_com_digitos(api, db_session):
    codigo = api.post("/livros", json=payload_livro()).json()["codigo"]

    assert _do_banco(db_session, codigo).isbn == "9783161484100"
    assert api.get(f"/livros/{codigo}").json()["isbn"] == "9783161484100"


def test_cadastro_descricao_e_opcional(api):
    corpo = payload_livro()
    del corpo["descricao"]
    assert api.post("/livros", json=corpo).status_code == 201


@pytest.mark.parametrize(
    "campo", ["isbn", "nome", "autor", "editora", "genero", "data_lancamento", "quantidade_total"]
)
def test_cadastro_exige_campos_obrigatorios(api, campo):
    corpo = payload_livro()
    del corpo[campo]
    assert api.post("/livros", json=corpo).status_code == 422


@pytest.mark.parametrize("isbn", ["9783161484100", "978-3-16-148410-0", "0-306-40615-2"])
def test_cadastro_isbn_valido(api, isbn):
    assert api.post("/livros", json=payload_livro(isbn=isbn)).status_code == 201


@pytest.mark.parametrize("isbn", ["", "123", "abc", "978-3-16-148410"])
def test_cadastro_isbn_invalido(api, isbn):
    assert api.post("/livros", json=payload_livro(isbn=isbn)).status_code == 422


@pytest.mark.parametrize("repetido", ["9783161484100", "978-3-16-148410-0"])
def test_cadastro_isbn_duplicado_mesmo_com_outra_formatacao(api, repetido):
    api.post("/livros", json=payload_livro())

    resp = api.post("/livros", json=payload_livro(isbn=repetido, nome="Outro título"))

    assert resp.status_code == 409
    assert resp.json()["motivo"] == "ISBN_DUPLICADO"


def test_cadastro_quantidade_negativa(api):
    assert api.post("/livros", json=payload_livro(quantidade_total=-1)).status_code == 422


def test_cliente_nao_define_codigo_nem_arquivado_no_cadastro(api):
    resp = api.post("/livros", json=payload_livro(codigo="liv_00000999", arquivado=True))

    assert resp.status_code in (201, 422)
    if resp.status_code == 201:
        assert resp.json()["codigo"] != "liv_00000999"
        assert resp.json()["arquivado"] is False


def test_cadastro_e_auditado(api, db_session, bibliotecario):
    codigo = api.post("/livros", json=payload_livro()).json()["codigo"]

    (reg,) = db_session.scalars(
        select(Auditoria).where(Auditoria.acao == "CADASTRO", Auditoria.entidade == "LIVRO")
    ).all()
    assert (reg.responsavel_id, reg.entidade_id) == (
        bibliotecario.id,
        _do_banco(db_session, codigo).id,
    )


# --- RF02 / RF18: consultar (bibliotecário e leitor) -----------------------------------------


@pytest.fixture
def acervo(cria_livro):
    return (
        cria_livro(isbn="9783161484100", nome="Dom Casmurro", autor="Machado de Assis"),
        cria_livro(isbn="0306406152", nome="Duna", autor="Frank Herbert", genero="Ficção"),
    )


@pytest.mark.parametrize("quem", ["bibliotecario", "leitor"])
@pytest.mark.parametrize(
    "filtro, idx",
    [
        ({"nome": "casmurro"}, 0),
        ({"autor": "HERBERT"}, 1),
        ({"isbn": "0306406152"}, 1),
        ({"isbn": "0-306-40615-2"}, 1),
        ({"genero": "ficção"}, 1),
    ],
    ids=["nome", "autor", "isbn", "isbn_com_hifens", "genero"],
)
def test_consultar_livros_por_filtro(api, cabecalho, request, acervo, quem, filtro, idx):
    pessoa = request.getfixturevalue(quem)

    resp = api.get("/livros", params=filtro, headers=cabecalho(pessoa))

    assert resp.status_code == 200
    assert [x["codigo"] for x in resp.json()] == [acervo[idx].codigo]


def test_consultar_livros_por_codigo_amigavel(api, acervo):
    resp = api.get("/livros", params={"codigo": acervo[1].codigo})
    assert [x["nome"] for x in resp.json()] == ["Duna"]


def test_consultar_sem_filtro_lista_o_catalogo_sem_arquivados(api, acervo, cria_livro):
    cria_livro(arquivado=True)

    codigos = {x["codigo"] for x in api.get("/livros").json()}

    assert codigos == {livro.codigo for livro in acervo}


def test_consulta_mostra_dados_e_disponibilidade(api, acervo):
    item = api.get(f"/livros/{acervo[1].codigo}").json()

    assert item["nome"] == "Duna"
    assert (item["quantidade_total"], item["quantidade_disponivel"]) == (1, 1)
    assert item["disponibilidade"] == "DISPONIVEL"


def test_consultar_livro_inexistente(api):
    assert api.get("/livros/liv_99999999").status_code == 404


def test_bibliotecario_ve_arquivados_quando_pede(api, cria_livro):
    arquivado = cria_livro(arquivado=True)

    lista = api.get("/livros", params={"arquivados": True}).json()
    unico = api.get(f"/livros/{arquivado.codigo}")

    assert arquivado.codigo in {x["codigo"] for x in lista}
    assert (unico.status_code, unico.json()["disponibilidade"]) == (200, "INDISPONIVEL")


def test_leitor_nunca_ve_livro_arquivado(api, cabecalho, leitor, cria_livro):
    arquivado = cria_livro(arquivado=True)
    headers = cabecalho(leitor)

    lista = api.get("/livros", params={"arquivados": True}, headers=headers).json()
    unico = api.get(f"/livros/{arquivado.codigo}", headers=headers)

    assert arquivado.codigo not in {x["codigo"] for x in lista}
    assert unico.status_code == 404


# --- RF14: disponibilidade -------------------------------------------------------------------


def test_disponibilidade_acompanha_os_emprestimos(api, cria_livro, cria_emprestimo, devolvido):
    livro = cria_livro(quantidade_total=2)

    def situacao():
        corpo = api.get(f"/livros/{livro.codigo}").json()
        return corpo["quantidade_disponivel"], corpo["disponibilidade"]

    assert situacao() == (2, "DISPONIVEL")
    cria_emprestimo(livro)
    assert situacao() == (1, "DISPONIVEL")
    cria_emprestimo(livro)
    assert situacao() == (0, "EMPRESTADO")
    cria_emprestimo(livro, **devolvido)  # devolvido não ocupa exemplar
    assert situacao() == (0, "EMPRESTADO")


# --- RF03: editar ----------------------------------------------------------------------------


def test_bibliotecario_edita_livro(api, acervo):
    resp = api.patch(f"/livros/{acervo[0].codigo}", json={"editora": "Nova Editora"})

    assert resp.status_code == 200
    assert resp.json()["editora"] == "Nova Editora"
    assert api.get(f"/livros/{acervo[0].codigo}").json()["editora"] == "Nova Editora"


def test_edicao_normaliza_o_isbn(api, db_session, acervo):
    api.patch(f"/livros/{acervo[0].codigo}", json={"isbn": "0-8044-2957-X"})
    assert _do_banco(db_session, acervo[0].codigo).isbn == "080442957X"


@pytest.mark.parametrize("campo", ["nome", "autor", "editora", "genero", "isbn"])
def test_edicao_nao_aceita_obrigatorio_vazio(api, acervo, campo):
    assert api.patch(f"/livros/{acervo[0].codigo}", json={campo: ""}).status_code == 422


def test_edicao_com_isbn_de_outro_livro(api, acervo):
    resp = api.patch(f"/livros/{acervo[0].codigo}", json={"isbn": acervo[1].isbn})
    assert (resp.status_code, resp.json()["motivo"]) == (409, "ISBN_DUPLICADO")


def test_edicao_ignora_codigo_e_arquivado_enviados_no_corpo(api, db_session, acervo):
    resp = api.patch(
        f"/livros/{acervo[0].codigo}",
        json={"nome": "Novo nome", "codigo": "liv_00000999", "arquivado": True},
    )

    assert resp.status_code in (200, 422)
    livro = _do_banco(db_session, acervo[0].codigo)
    assert (livro.codigo, livro.arquivado) == (acervo[0].codigo, False)


def test_edicao_nao_altera_emprestimos_existentes(api, db_session, acervo, cria_emprestimo):
    emprestimo = cria_emprestimo(acervo[0])
    antes = (emprestimo.livro_id, emprestimo.data_emprestimo, emprestimo.data_prevista)

    api.patch(f"/livros/{acervo[0].codigo}", json={"nome": "Dom Casmurro (ed. revista)"})

    db_session.refresh(emprestimo)
    assert (emprestimo.livro_id, emprestimo.data_emprestimo, emprestimo.data_prevista) == antes
    assert emprestimo.status_atual == "EMPRESTADO"


def test_edicao_nao_reduz_exemplares_abaixo_dos_emprestimos_ativos(
    api, cria_livro, cria_emprestimo
):
    livro = cria_livro(quantidade_total=2)
    cria_emprestimo(livro)
    cria_emprestimo(livro)

    resp = api.patch(f"/livros/{livro.codigo}", json={"quantidade_total": 1})

    assert (resp.status_code, resp.json()["motivo"]) == (409, "QUANTIDADE_INSUFICIENTE")


def test_edicao_de_livro_inexistente(api):
    assert api.patch("/livros/liv_99999999", json={"nome": "X"}).status_code == 404


def test_edicao_e_auditada_com_antes_e_depois(api, db_session, acervo, bibliotecario):
    api.patch(f"/livros/{acervo[0].codigo}", json={"editora": "Nova"})

    (reg,) = db_session.scalars(
        select(Auditoria).where(Auditoria.acao == "ALTERACAO", Auditoria.entidade == "LIVRO")
    ).all()
    assert reg.responsavel_id == bibliotecario.id
    assert (reg.dados["antes"]["editora"], reg.dados["depois"]["editora"]) == ("Editora", "Nova")


# --- RF04 / RF19: arquivar -------------------------------------------------------------------


def test_arquivar_nao_apaga_o_registro(api, db_session, cria_livro):
    livro = cria_livro()

    resp = api.post(f"/livros/{livro.codigo}/arquivar")

    assert resp.status_code == 200
    assert resp.json()["arquivado"] is True
    assert _do_banco(db_session, livro.codigo).arquivado is True
    assert api.get(f"/livros/{livro.codigo}").status_code == 200  # histórico preservado


def test_livro_arquivado_sai_do_catalogo_do_leitor(api, cabecalho, leitor, cria_livro):
    livro = cria_livro()
    api.post(f"/livros/{livro.codigo}/arquivar")

    catalogo = api.get("/livros", headers=cabecalho(leitor)).json()

    assert livro.codigo not in {x["codigo"] for x in catalogo}


def test_previa_informa_quantos_emprestimos_ainda_estao_ativos(
    api, cria_livro, cria_emprestimo, devolvido
):
    livro = cria_livro(quantidade_total=4)
    cria_emprestimo(livro)
    cria_emprestimo(livro, status_atual="ATRASADO")
    cria_emprestimo(livro, **devolvido)

    resp = api.get(f"/livros/{livro.codigo}/previa-arquivamento")

    assert resp.status_code == 200
    assert resp.json() == {"emprestimos_ativos": 2}


def test_previa_nao_arquiva(api, db_session, cria_livro):
    livro = cria_livro()
    api.get(f"/livros/{livro.codigo}/previa-arquivamento")
    assert _do_banco(db_session, livro.codigo).arquivado is False


def test_arquivar_nao_altera_emprestimos_em_andamento(api, db_session, cria_livro, cria_emprestimo):
    livro = cria_livro()
    emprestimo = cria_emprestimo(livro)

    api.post(f"/livros/{livro.codigo}/arquivar")

    db_session.refresh(emprestimo)
    assert (emprestimo.status_atual, emprestimo.data_devolucao) == ("EMPRESTADO", None)


def test_arquivar_livro_inexistente(api):
    assert api.post("/livros/liv_99999999/arquivar").status_code == 404
    assert api.get("/livros/liv_99999999/previa-arquivamento").status_code == 404


def test_arquivamento_e_auditado(api, db_session, cria_livro, bibliotecario):
    livro = cria_livro()

    api.post(f"/livros/{livro.codigo}/arquivar")

    (reg,) = db_session.scalars(
        select(Auditoria).where(Auditoria.acao == "ARQUIVAMENTO", Auditoria.entidade == "LIVRO")
    ).all()
    assert (reg.responsavel_id, reg.entidade_id) == (bibliotecario.id, livro.id)


# --- autorização: Leitor só consulta; sem login nada funciona --------------------------------


@pytest.fixture
def alvo(cria_livro):
    return cria_livro()


@pytest.mark.parametrize(
    "metodo, rota, corpo",
    [
        ("post", "/livros", payload_livro()),
        ("patch", "/livros/{codigo}", {"nome": "X"}),
        ("post", "/livros/{codigo}/arquivar", None),
        ("get", "/livros/{codigo}/previa-arquivamento", None),
    ],
    ids=["cadastrar", "editar", "arquivar", "previa"],
)
def test_leitor_nao_executa_operacoes_de_gestao(
    api, db_session, cabecalho, leitor, alvo, metodo, rota, corpo
):
    nome_antes, arquivado_antes = alvo.nome, alvo.arquivado

    resp = getattr(api, metodo)(
        rota.format(codigo=alvo.codigo),
        headers=cabecalho(leitor),
        **({"json": corpo} if corpo else {}),
    )

    assert resp.status_code == 403
    db_session.refresh(alvo)
    assert (alvo.nome, alvo.arquivado) == (nome_antes, arquivado_antes)


@pytest.mark.parametrize(
    "metodo, rota, corpo",
    [
        ("post", "/livros", payload_livro()),
        ("get", "/livros", None),
        ("get", "/livros/{codigo}", None),
        ("patch", "/livros/{codigo}", {"nome": "X"}),
        ("post", "/livros/{codigo}/arquivar", None),
        ("get", "/livros/{codigo}/previa-arquivamento", None),
    ],
)
def test_rotas_de_livros_exigem_autenticacao(db_client, alvo, metodo, rota, corpo):
    resp = getattr(db_client, metodo)(
        rota.format(codigo=alvo.codigo), **({"json": corpo} if corpo else {})
    )
    assert resp.status_code == 401


def test_bibliotecario_inativo_nao_opera(db_client, cabecalho, cria_usuario):
    inativo = cria_usuario(papel="BIBLIOTECARIO", ativo=False)
    resp = db_client.post("/livros", json=payload_livro(), headers=cabecalho(inativo))
    assert resp.status_code == 401
