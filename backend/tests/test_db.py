import pytest
from sqlalchemy import text

pytestmark = pytest.mark.integracao


def test_conecta_no_postgres(db_session):
    assert db_session.execute(text("SELECT 1")).scalar() == 1
