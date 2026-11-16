import pytest

from tests.db_guard import DestinoNaoAutorizadoError, validar_destino

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
