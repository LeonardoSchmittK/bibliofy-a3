"""Cria o PRIMEIRO bibliotecário, fora da API (SEC01).

Uso (na pasta backend, com o banco no ar e o .env configurado):

    python -m scripts.criar_bibliotecario

Pede nome, matrícula, e-mail e senha pelo terminal. A senha é guardada só como hash Argon2id.
Os demais bibliotecários são promovidos por quem já é bibliotecário (PUT /usuarios/{codigo}/papel).
"""

import sys
from getpass import getpass

from sqlalchemy import func, select

from app.core.security import hash_senha
from app.db.session import SessionLocal
from app.models import Pessoa


def main() -> int:
    nome = input("Nome: ").strip()
    matricula = input("Matrícula: ").strip()
    email = input("E-mail: ").strip()
    senha = getpass("Senha: ")
    if senha != getpass("Confirme a senha: "):
        print("As senhas não conferem.")
        return 1
    if not all([nome, matricula, email, senha]):
        print("Todos os campos são obrigatórios.")
        return 1

    with SessionLocal() as db:
        ja_existe = db.scalars(
            select(Pessoa.id).where(
                (Pessoa.matricula == matricula) | (func.lower(Pessoa.email) == email.lower())
            )
        ).first()
        if ja_existe:
            print("Já existe uma pessoa com essa matrícula ou e-mail.")
            return 1
        pessoa = Pessoa(
            nome=nome,
            matricula=matricula,
            email=email,
            senha_hash=hash_senha(senha),
            papel="BIBLIOTECARIO",
            ativo=True,
        )
        db.add(pessoa)
        db.commit()
        print(f"Bibliotecário criado: {pessoa.codigo}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
