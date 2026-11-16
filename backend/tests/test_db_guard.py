import uuid

import pytest
from sqlalchemy import create_engine, text

from tests import db_guard
from tests.db_guard import DestinoNaoAutorizadoError, preparar_banco, validar_destino

APP_URL = "postgresql+psycopg://app:senha-da-app@localhost:5432/bibliofy"
APP_TEST_URL = "postgresql+psycopg://app:senha-da-app@localhost:5432/bibliofy_test"
BASE = "postgresql+psycopg://teste:senha-de-teste@localhost:5432"


@pytest.mark.parametrize(
    "url",
    [
        f"{BASE}/bibliofy_test",
        f"{BASE}/test",
        f"{BASE}/test_bibliofy",
        f"{BASE}/bibliofy_test?sslmode=disable",
        "postgresql+psycopg://teste:senha-de-teste@127.0.0.1:5432/bibliofy_test",
    ],
)
def test_aceita_banco_identificado_como_teste(url):
    alvo = validar_destino(url, [APP_URL])

    assert alvo.database in {"bibliofy_test", "test", "test_bibliofy"}


@pytest.mark.parametrize(
    "url",
    [
        f"{BASE}/bibliofy",
        f"{BASE}/postgres",
        f"{BASE}/bibliofy_dev",
        f"{BASE}/meu_banco",
        "postgresql+psycopg://teste:senha-de-teste@localhost:5432/",
        "",
        "nao-e-url",
    ],
)
def test_recusa_banco_nao_identificado_como_teste(url):
    with pytest.raises(DestinoNaoAutorizadoError):
        validar_destino(url, [APP_URL])


@pytest.mark.parametrize(
    "url",
    [
        "postgresql+psycopg://outro:senha@localhost:5432/bibliofy_test",
        "postgresql+psycopg://outro:senha@localhost/bibliofy_test",
        "postgresql+psycopg://outro:senha@127.0.0.1:5432/bibliofy_test",
        "postgresql+psycopg://outro:senha@127.0.0.1/bibliofy_test",
        "postgresql+psycopg://outro:senha@localhost:5432/bibliofy_test?sslmode=disable",
    ],
)
def test_recusa_mesmo_destino_da_aplicacao(url):
    with pytest.raises(DestinoNaoAutorizadoError, match="mesmo banco da aplicação"):
        validar_destino(url, [APP_TEST_URL])


def test_recusa_mesmo_destino_mesmo_com_hosts_equivalentes():
    app = "postgresql+psycopg://app:senha@127.0.0.1:5432/bibliofy_test"
    teste = "postgresql+psycopg://teste:senha@localhost:5432/bibliofy_test"

    with pytest.raises(DestinoNaoAutorizadoError, match="mesmo banco da aplicação"):
        validar_destino(teste, [app])


@pytest.mark.parametrize(
    "url",
    [
        "postgresql+psycopg://teste:super-segredo@localhost:5432/bibliofy",
        "postgresql+psycopg://teste:super-segredo@localhost:5432/bibliofy_test",
        "postgresql+psycopg://teste:super-segredo@nao-e-url",
    ],
)
def test_recusa_nunca_imprime_a_senha(url):
    with pytest.raises(DestinoNaoAutorizadoError) as excinfo:
        validar_destino(url, [APP_TEST_URL])

    assert "super-segredo" not in str(excinfo.value)


@pytest.mark.parametrize(
    "url",
    [
        f"{BASE}/bibliofy",
        f"{BASE}/bibliofy_test",
    ],
)
def test_recusa_sem_chamar_create_engine(monkeypatch, url):
    def create_engine_que_falha(*args, **kwargs):
        raise AssertionError("create_engine não deveria ser chamado antes da validação")

    monkeypatch.setattr(db_guard, "create_engine", create_engine_que_falha)
    monkeypatch.setattr(db_guard, "_urls_da_aplicacao", lambda: [APP_TEST_URL])

    with pytest.raises(DestinoNaoAutorizadoError):
        preparar_banco(url, externo=True)


@pytest.mark.integracao
def test_banco_recusado_permanece_intacto(db_engine):
    nome = f"decoy_{uuid.uuid4().hex[:12]}"
    admin_url = db_engine.url.set(database="postgres").render_as_string(hide_password=False)
    decoy_url = db_engine.url.set(database=nome).render_as_string(hide_password=False)

    admin = create_engine(admin_url, isolation_level="AUTOCOMMIT")
    try:
        with admin.connect() as conn:
            conn.execute(text(f'CREATE DATABASE "{nome}"'))

        decoy = create_engine(decoy_url)
        try:
            with decoy.begin() as conn:
                conn.execute(text("CREATE TABLE sentinela (valor text NOT NULL)"))
                conn.execute(text("INSERT INTO sentinela (valor) VALUES ('intacto')"))
        finally:
            decoy.dispose()

        with pytest.raises(DestinoNaoAutorizadoError):
            preparar_banco(decoy_url, externo=True)

        verificacao = create_engine(decoy_url)
        try:
            with verificacao.connect() as conn:
                valor = conn.execute(text("SELECT valor FROM sentinela")).scalar_one()
        finally:
            verificacao.dispose()

        assert valor == "intacto"
    finally:
        with admin.connect() as conn:
            conn.execute(text(f'DROP DATABASE IF EXISTS "{nome}" WITH (FORCE)'))
        admin.dispose()
