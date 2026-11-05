from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg://bibliofy:bibliofy@localhost:5432/bibliofy"
    cors_origins: list[str] = ["http://localhost:5173"]

    # TODO(#35) Configuração do JWT (SEC02/SEC03). Testes: tests/auth/test_config_jwt.py
    #   1. Adicionar `jwt_secret: str` SEM valor padrão: sem JWT_SECRET no .env a aplicação não
    #      sobe (nunca commitar uma chave padrão no código).
    #   2. Adicionar `jwt_algorithm: str = "HS256"`.
    #   3. Adicionar `jwt_expire_minutes: int = Field(default=15, ge=1, le=15)`
    #      (`from pydantic import Field`): o token vale no máximo 15 minutos.
    #   4. Gerar a chave real só no seu .env (ignorado pelo Git), por exemplo com
    #      `python -c "import secrets; print(secrets.token_urlsafe(48))"`.
    #   5. Documentar JWT_SECRET com valor fictício no .env.example (ver TODO lá).
    #   6. Os testes definem um JWT_SECRET de teste em tests/__init__.py, então o CI não
    #      precisa de segredo real.


@lru_cache
def get_settings() -> Settings:
    return Settings()
