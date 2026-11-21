"""Popula o banco com dados de demonstração: 2 usuários e um catálogo inicial.

Uso (na pasta backend, com o banco no ar e o .env configurado):

    python -m scripts.seed

É idempotente: só insere o que ainda não existe (pessoa por matrícula/e-mail, livro por ISBN).
Nunca altera nem apaga dados existentes, então o que for cadastrado na plataforma é preservado.
As credenciais podem ser trocadas pelas variáveis SEED_* (veja .env.example).
"""

import os
import sys
from datetime import date

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.security import hash_senha
from app.db.session import SessionLocal
from app.models import Livro, Pessoa


def _usuarios() -> list[dict]:
    return [
        {
            "matricula": "BIB0001",
            "nome": "Maria Bibliotecária",
            "email": os.getenv("SEED_BIBLIOTECARIO_EMAIL", "bibliotecario@bibliofy.com"),
            "senha": os.getenv("SEED_BIBLIOTECARIO_SENHA", "Bibliofy@Demo1"),
            "papel": "BIBLIOTECARIO",
        },
        {
            "matricula": "ALU0001",
            "nome": "João Aluno",
            "email": os.getenv("SEED_ALUNO_EMAIL", "aluno@bibliofy.com"),
            "senha": os.getenv("SEED_ALUNO_SENHA", "Bibliofy@Demo1"),
            "papel": "LEITOR",
        },
    ]


# (isbn-13, nome, autor, editora, genero, data_lancamento, quantidade_total)
LIVROS: list[tuple[str, str, str, str, str, date, int]] = [
    (
        "9780132350884",
        "Clean Code",
        "Robert C. Martin",
        "Prentice Hall",
        "Tecnologia",
        date(2008, 8, 1),
        4,
    ),
    (
        "9780135957059",
        "The Pragmatic Programmer",
        "David Thomas; Andrew Hunt",
        "Addison-Wesley",
        "Tecnologia",
        date(2019, 9, 13),
        3,
    ),
    (
        "9780201633610",
        "Design Patterns",
        "Erich Gamma et al.",
        "Addison-Wesley",
        "Tecnologia",
        date(1994, 10, 31),
        2,
    ),
    (
        "9780321125217",
        "Domain-Driven Design",
        "Eric Evans",
        "Addison-Wesley",
        "Tecnologia",
        date(2003, 8, 30),
        2,
    ),
    (
        "9780262033848",
        "Introduction to Algorithms",
        "Thomas H. Cormen et al.",
        "MIT Press",
        "Tecnologia",
        date(2009, 7, 31),
        5,
    ),
    ("9780451524935", "1984", "George Orwell", "Signet Classics", "Ficção", date(1961, 1, 1), 6),
    (
        "9780060850524",
        "Brave New World",
        "Aldous Huxley",
        "Harper Perennial",
        "Ficção",
        date(2006, 10, 17),
        3,
    ),
    (
        "9780743273565",
        "The Great Gatsby",
        "F. Scott Fitzgerald",
        "Scribner",
        "Romance",
        date(2004, 9, 30),
        4,
    ),
    (
        "9780141439518",
        "Pride and Prejudice",
        "Jane Austen",
        "Penguin Classics",
        "Romance",
        date(2002, 12, 31),
        3,
    ),
    (
        "9780061120084",
        "To Kill a Mockingbird",
        "Harper Lee",
        "Harper Perennial",
        "Romance",
        date(2006, 5, 23),
        5,
    ),
    (
        "9780316769488",
        "The Catcher in the Rye",
        "J. D. Salinger",
        "Little, Brown",
        "Ficção",
        date(1991, 5, 1),
        2,
    ),
    (
        "9780547928227",
        "The Hobbit",
        "J. R. R. Tolkien",
        "Mariner Books",
        "Fantasia",
        date(2012, 9, 18),
        7,
    ),
    (
        "9780156012195",
        "The Little Prince",
        "Antoine de Saint-Exupéry",
        "Harcourt",
        "Infantil",
        date(2000, 5, 15),
        4,
    ),
    ("9780062315007", "The Alchemist", "Paulo Coelho", "HarperOne", "Ficção", date(2014, 4, 15), 5),
    ("9780735211292", "Atomic Habits", "James Clear", "Avery", "Autoajuda", date(2018, 10, 16), 0),
]


def semear(db: Session) -> tuple[int, int]:
    """Insere o que falta e devolve (usuários criados, livros criados)."""
    pessoas = 0
    for u in _usuarios():
        existe = db.scalars(
            select(Pessoa.id).where(
                (Pessoa.matricula == u["matricula"])
                | (func.lower(Pessoa.email) == u["email"].lower())
            )
        ).first()
        if existe:
            continue
        db.add(
            Pessoa(
                matricula=u["matricula"],
                nome=u["nome"],
                email=u["email"],
                senha_hash=hash_senha(u["senha"]),
                papel=u["papel"],
                ativo=True,
            )
        )
        pessoas += 1

    livros = 0
    existentes = set(db.scalars(select(Livro.isbn)))
    for isbn, nome, autor, editora, genero, lancamento, qtd in LIVROS:
        if isbn in existentes:
            continue
        db.add(
            Livro(
                isbn=isbn,
                nome=nome,
                autor=autor,
                editora=editora,
                genero=genero,
                data_lancamento=lancamento,
                quantidade_total=qtd,
            )
        )
        livros += 1

    db.commit()
    return pessoas, livros


def main() -> int:
    with SessionLocal() as db:
        pessoas, livros = semear(db)
    print(f"Seed concluído: {pessoas} usuário(s) e {livros} livro(s) criados.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
