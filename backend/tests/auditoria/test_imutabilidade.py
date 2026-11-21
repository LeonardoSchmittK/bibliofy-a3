"""Log imutável (RNF10): o banco só aceita INSERT em `auditoria`."""

import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

pytestmark = pytest.mark.integracao


def test_update_e_recusado(db_session, cria_registro):
    registro = cria_registro()
    with pytest.raises(DBAPIError):
        db_session.execute(
            text("UPDATE auditoria SET acao = 'ALTERACAO' WHERE id = :id"), {"id": registro.id}
        )


def test_delete_e_recusado(db_session, cria_registro):
    registro = cria_registro()
    with pytest.raises(DBAPIError):
        db_session.execute(text("DELETE FROM auditoria WHERE id = :id"), {"id": registro.id})


def test_truncate_e_recusado(db_session, cria_registro):
    cria_registro()
    with pytest.raises(DBAPIError):
        db_session.execute(text("TRUNCATE auditoria"))


def test_insert_continua_permitido(db_session, cria_registro):
    assert cria_registro().id is not None
