import os
import warnings
from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.main import app

SCHEMA_SQL = Path(__file__).resolve().parents[1] / "database" / "schema.sql"


@pytest.fixture
def client() -> Iterator[TestClient]:
    """Cliente para endpoints que nÃ£o usam banco."""
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="session")
def db_engine() -> Iterator[Engine]:
    """PostgreSQL real: TEST_DATABASE_URL ou testcontainers. Sem nenhum dos dois, pula."""
    url = os.environ.get("TEST_DATABASE_URL")
    container = None
    if not url:
        try:
            from testcontainers.postgres import PostgresContainer

            container = PostgresContainer("postgres:17", driver="psycopg")
            container.start()
            url = container.get_connection_url()
        except Exception as exc:
            warnings.warn(
                f"PostgreSQL indisponÃ­vel, testes de integraÃ§Ã£o pulados: {exc}", stacklevel=2
            )
            pytest.skip("sem TEST_DATABASE_URL nem Docker para testcontainers")
    engine = create_engine(url)
    with engine.begin() as conn:
        conn.execute(text("DROP SCHEMA public CASCADE"))
        conn.execute(text("CREATE SCHEMA public"))
        # Driver direto: sem parâmetros o psycopg não interpreta o "%" do RAISE como placeholder.
        conn.connection.driver_connection.execute(SCHEMA_SQL.read_text(encoding="utf-8"))
    try:
        yield engine
    finally:
        engine.dispose()
        if container is not None:
            container.stop()


@pytest.fixture
def db_session(db_engine: Engine) -> Iterator[Session]:
    """SessÃ£o cujo trabalho Ã© desfeito (rollback) ao fim de cada teste."""
    connection = db_engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection, join_transaction_mode="create_savepoint")
    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture
def db_client(db_session: Session) -> Iterator[TestClient]:
    app.dependency_overrides[get_db] = lambda: db_session
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
