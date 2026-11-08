"""Camada "View": schemas de usuário (Pessoa). A senha e o hash nunca saem pela API.

Testes que devem passar: tests/auth/test_schemas.py.
Requisitos: SEC01 (papel nunca vem do cliente), SEC02 (sem senha/hash em respostas e logs).
"""
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, SecretStr


class UsuarioCriar(BaseModel):
    nome: str = Field(min_length=1, max_length=150)
    matricula : str = Field(min_length=1, max_length=30)
    email: EmailStr = Field(min_length=1, max_length=100)
    telefone: str | None = Field(default=None, max_length=20)
    senha: SecretStr = Field(min_length=1)

class UsuarioSaida(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    codigo: str
    matricula: str
    nome: str
    email: str
    telefone: str | None
    papel: str
    ativo: bool

class UsuarioAtualizar(BaseModel):
    nome: str | None = Field(default=None, min_length=1, max_length=150)
    matricula: str | None = Field(default=None, min_length=1, max_length=30)
    email: EmailStr | None = Field(default=None, min_length=1, max_length=100)
    telefone: str | None = Field(default=None, max_length=20)

class PapelAlterar(BaseModel):
    papel: Literal["LEITOR", "BIBLIOTECARIO"]
