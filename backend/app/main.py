from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import auth, health, usuarios
from app.core.config import get_settings


def create_app() -> FastAPI:
    app = FastAPI(title="Bibliofy")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=get_settings().cors_origins,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(health.router)
    app.include_router(auth.router)
    app.include_router(usuarios.router)
    #   3. Confirmar em /docs que o botão "Authorize" aparece (OAuth2PasswordBearer).
    return app


app = create_app()
