import pytest
from sqlalchemy.exc import OperationalError

from app.db.session import get_db
from app.main import app


@pytest.mark.integracao
def test_health_retorna_ok(db_client):
    resp = db_client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_health_retorna_503_sem_banco(client):
    class SessaoQuebrada:
        def execute(self, *args, **kwargs):
            raise OperationalError("SELECT 1", {}, Exception("sem conexão"))

    app.dependency_overrides[get_db] = lambda: SessaoQuebrada()
    try:
        resp = client.get("/health")
    finally:
        app.dependency_overrides.clear()
    assert resp.status_code == 503
