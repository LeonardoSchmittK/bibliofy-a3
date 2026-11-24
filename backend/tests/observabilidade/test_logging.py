import logging

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.logging import instalar_logging


def _app() -> TestClient:
    app = FastAPI()
    instalar_logging(app)

    @app.get("/ok")
    def ok():
        return {"ok": True}

    @app.get("/boom")
    def boom():
        raise RuntimeError("falhou")

    return TestClient(app, raise_server_exceptions=False)


def test_loga_info(caplog):
    logging.getLogger("bibliofy").propagate = True
    with caplog.at_level(logging.INFO, logger="bibliofy"):
        assert _app().get("/ok").status_code == 200
    assert any(
        r.levelno == logging.INFO and "GET /ok -> 200" in r.getMessage() for r in caplog.records
    )


def test_excecao_gera_500_e_trace(caplog):
    logging.getLogger("bibliofy").propagate = True
    with caplog.at_level(logging.ERROR, logger="bibliofy"):
        r = _app().get("/boom")
    assert r.status_code == 500
    assert r.json() == {"detail": "Erro interno do servidor"}
    rec = next(r for r in caplog.records if r.levelno == logging.ERROR)
    assert rec.exc_info and "RuntimeError" in repr(rec.exc_info[1])
