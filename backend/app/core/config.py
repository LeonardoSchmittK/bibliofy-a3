from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg://bibliofy:bibliofy@localhost:5432/bibliofy"
    cors_origins: list[str] = ["http://localhost:5173"]

    # JWT (SEC02/SEC03). Sem valor padrão para a chave: sem JWT_SECRET a aplicação não sobe.
    jwt_secret: str
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = Field(default=15, ge=1, le=15)


@lru_cache
def get_settings() -> Settings:
    return Settings()
