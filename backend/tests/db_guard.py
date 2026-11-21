from __future__ import annotations

import os
import re
from collections.abc import Iterable
from pathlib import Path

from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL, Engine, make_url
from sqlalchemy.exc import ArgumentError

SCHEMA_SQL = Path(__file__).resolve().parents[1] / "database" / "schema.sql"

_LOCAL = {"", "localhost", "127.0.0.1", "::1"}
_NOME_TESTE = re.compile(r"^test$|_test$|^test_")


class DestinoNaoAutorizadoError(RuntimeError):
    pass


def _identidade(url: URL) -> tuple[str | None, int, str | None]:
    host = "localhost" if (url.host or "") in _LOCAL else url.host
    return host, url.port or 5432, url.database


def validar_destino(url: str, urls_app: Iterable[str | None] = ()) -> URL:
    try:
        alvo = make_url(url)
    except ArgumentError:
        raise DestinoNaoAutorizadoError("TEST_DATABASE_URL não é uma URL de banco válida") from None

    if not alvo.database or not _NOME_TESTE.search(alvo.database):
        raise DestinoNaoAutorizadoError(
            "TEST_DATABASE_URL aponta para um banco não identificado como teste "
            f"(banco: {alvo.database or '<vazio>'}); use um banco cujo nome seja "
            '"test", comece com "test_" ou termine em "_test"'
        )

    identidade = _identidade(alvo)
    for app_url in urls_app:
        if not app_url:
            continue
        try:
            app = make_url(app_url)
        except ArgumentError:
            continue
        if _identidade(app) == identidade:
            raise DestinoNaoAutorizadoError(
                "TEST_DATABASE_URL aponta para o mesmo banco da aplicação "
                f"(banco: {alvo.database}); os testes apagariam os dados de desenvolvimento"
            )

    return alvo


def _urls_da_aplicacao() -> list[str]:
    from app.core.config import Settings, get_settings

    urls: list[str | None] = [
        os.environ.get("DATABASE_URL"),
        Settings.model_fields["database_url"].default,
    ]
    try:
        urls.append(get_settings().database_url)
    except Exception:
        pass
    return [url for url in urls if url]


def preparar_banco(url: str, *, externo: bool) -> Engine:
    if externo:
        validar_destino(url, _urls_da_aplicacao())

    engine = create_engine(url)
    try:
        with engine.begin() as conn:
            conn.execute(text("DROP SCHEMA public CASCADE"))
            conn.execute(text("CREATE SCHEMA public"))
            conn.connection.driver_connection.execute(SCHEMA_SQL.read_text(encoding="utf-8"))
    except Exception:
        engine.dispose()
        raise
    return engine
