"""Logging estruturado: [NIVEL] timestamp logger mensagem, com trace em erros."""

import logging
import sys
import time
from collections.abc import Awaitable, Callable

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse

from app.core.security import TokenInvalidoError, decodificar_token

LOGGER_NAME = "bibliofy"
_NIVEIS = {
    "DEBUG": "DEBUG",
    "INFO": "INFO",
    "WARNING": "ALERTA",
    "ERROR": "ERRO",
    "CRITICAL": "ERRO",
}


class FormatadorBibliofy(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        nivel = _NIVEIS.get(record.levelname, record.levelname)
        ts = self.formatTime(record, "%Y-%m-%dT%H:%M:%S%z")
        linha = f"[{nivel}] {ts} {record.getMessage()}"
        if record.exc_info:
            linha += "\n" + self.formatException(record.exc_info)
        return linha


def configurar_logging(nivel: int = logging.INFO) -> logging.Logger:
    logger = logging.getLogger(LOGGER_NAME)
    logger.setLevel(nivel)
    logger.propagate = False
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(FormatadorBibliofy())
        logger.addHandler(handler)
    return logger


def _quem(request: Request) -> str:
    auth = request.headers.get("authorization", "")
    if auth.lower().startswith("bearer "):
        try:
            return str(decodificar_token(auth[7:]).get("sub", "anonimo"))
        except TokenInvalidoError:
            return "token-invalido"
    return "anonimo"


def instalar_logging(app: FastAPI) -> None:
    logger = configurar_logging()

    @app.middleware("http")
    async def log_requisicoes(
        request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        inicio = time.perf_counter()
        quem = _quem(request)
        try:
            response = await call_next(request)
        except Exception:
            ms = (time.perf_counter() - inicio) * 1000
            logger.error(
                "usuario=%s %s %s -> 500 (%.1fms) exceção não tratada",
                quem,
                request.method,
                request.url.path,
                ms,
                exc_info=True,
            )
            return JSONResponse({"detail": "Erro interno do servidor"}, status_code=500)
        ms = (time.perf_counter() - inicio) * 1000
        nivel = (
            logging.ERROR
            if response.status_code >= 500
            else (logging.WARNING if response.status_code >= 400 else logging.INFO)
        )
        logger.log(
            nivel,
            "usuario=%s %s %s -> %s (%.1fms)",
            quem,
            request.method,
            request.url.path,
            response.status_code,
            ms,
        )
        return response
