from app.core.config import Settings


def test_settings_le_variaveis_de_ambiente(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://u:p@h/db")
    monkeypatch.setenv("CORS_ORIGINS", '["http://a.com"]')
    s = Settings()
    assert s.database_url == "postgresql+psycopg://u:p@h/db"
    assert s.cors_origins == ["http://a.com"]
