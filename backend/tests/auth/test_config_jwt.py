"""SEC02/SEC03: configuração do JWT vem do ambiente, nunca do código (sem DB)."""

from pathlib import Path

import pytest
from pydantic import ValidationError

from app.core.config import Settings

RAIZ_BACKEND = Path(__file__).resolve().parents[2]


def test_settings_le_chave_e_expiracao_do_ambiente(monkeypatch):
    monkeypatch.setenv("JWT_SECRET", "outra-chave-0123456789abcdef0123456789")
    monkeypatch.setenv("JWT_EXPIRE_MINUTES", "10")

    s = Settings(_env_file=None)

    assert s.jwt_secret == "outra-chave-0123456789abcdef0123456789"
    assert s.jwt_expire_minutes == 10


def test_valores_padrao_de_algoritmo_e_expiracao(monkeypatch):
    monkeypatch.delenv("JWT_EXPIRE_MINUTES", raising=False)
    monkeypatch.delenv("JWT_ALGORITHM", raising=False)

    s = Settings(_env_file=None)

    assert s.jwt_algorithm == "HS256"
    assert s.jwt_expire_minutes == 15


def test_sem_chave_jwt_a_aplicacao_nao_sobe(monkeypatch):
    """Não existe chave padrão no código: faltou o .env, falha na hora."""
    monkeypatch.delenv("JWT_SECRET", raising=False)
    with pytest.raises(ValidationError):
        Settings(_env_file=None)


@pytest.mark.parametrize("minutos", ["0", "-5", "16", "60"])
def test_expiracao_do_token_vai_de_1_a_15_minutos(monkeypatch, minutos):
    monkeypatch.setenv("JWT_EXPIRE_MINUTES", minutos)
    with pytest.raises(ValidationError):
        Settings(_env_file=None)


def test_env_example_documenta_a_chave_sem_valor_real():
    linhas = (RAIZ_BACKEND / ".env.example").read_text(encoding="utf-8").splitlines()
    chave = next((ln for ln in linhas if ln.startswith("JWT_SECRET=")), None)

    assert chave is not None, "JWT_SECRET precisa constar no .env.example"
    assert "troque" in chave.lower()  # só um exemplo fictício, como POSTGRES_PASSWORD


def test_dot_env_esta_no_gitignore():
    gitignore = (RAIZ_BACKEND.parent / ".gitignore").read_text(encoding="utf-8").splitlines()
    assert any(ln.strip() in {".env", "*.env", "**/.env", "backend/.env"} for ln in gitignore)
