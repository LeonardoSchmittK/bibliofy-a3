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


def isbn_equivalentes(texto: str) -> set[str]:
    """Todas as formas do mesmo ISBN: ele próprio e o equivalente ISBN-10 <-> ISBN-13.

    O ISBN-10 sempre tem equivalente (prefixo 978); o ISBN-13 só tem se começar com 978.
    """
    isbn = normalizar_isbn(texto)
    formas = {isbn}

    if len(isbn) == 10:
        base = "978" + isbn[:9]
        formas.add(base + _digito_isbn13(base))
    elif isbn.startswith("978"):
        base = isbn[3:12]
        formas.add(base + _digito_isbn10(base))
    return formas


def _digito_isbn13(base12: str) -> str:
    soma = sum(int(d) * (1 if i % 2 == 0 else 3) for i, d in enumerate(base12))
    return str((10 - soma % 10) % 10)


def _digito_isbn10(base9: str) -> str:
    soma = sum(int(d) * (10 - i) for i, d in enumerate(base9))
    resto = (11 - soma % 11) % 11
    return "X" if resto == 10 else str(resto)
