"""Validação e normalização de ISBN (RF01 e RF02 da wiki citam a "regex de validação do ISBN").

Testes que devem passar: tests/livros/test_isbn.py.
"""

import re

ISBN10_REGEX = re.compile(r"^\d{9}[\dX]$")
ISBN13_REGEX = re.compile(r"^97[89]\d{10}$")


def isbn_valido(texto: str) -> bool:
    try:
        normalizar_isbn(texto)
        return True
    except ValueError:
        return False


def normalizar_isbn(texto: str) -> str:
    isbn = re.sub(r"[\s-]", "", texto.strip().upper())

    if not (ISBN10_REGEX.fullmatch(isbn) or ISBN13_REGEX.fullmatch(isbn)):
        raise ValueError(f"ISBN inválido: {isbn}")
    return isbn
