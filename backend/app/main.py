from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import auth, health, livros, usuarios
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
    app.include_router(livros.router)
    return app


app = create_app()
