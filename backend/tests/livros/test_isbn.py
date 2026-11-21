"""Regex de validação do ISBN citada em RF01/RF02 (unitário, sem DB).

Contrato de `app.core.isbn`:
- isbn_valido(texto) -> bool       valida só o FORMATO (ISBN-10 ou ISBN-13, com ou sem
                                   hífens/espaços); não confere o dígito verificador
- normalizar_isbn(texto) -> str    só dígitos (e `X` maiúsculo); levanta ValueError se inválido
"""

import pytest

VALIDOS = [
    "9783161484100",
    "978-3-16-148410-0",
    "978 3 16 148410 0",
    "979-10-90636-07-1",
    "0306406152",
    "0-306-40615-2",
    "080442957X",
    "0-8044-2957-X",
    "0-8044-2957-x",
]

INVALIDOS = [
    "",
    "   ",
    "123",
    "abc-def-ghi",
    "978-3-16-148410",  # 12 dígitos
    "97831614841000",  # 14 dígitos
    "1234567890123",  # 13 dígitos, mas não começa com 978/979
    "X234567890",  # X só vale no último dígito do ISBN-10
    "978316148410X",  # X não existe no ISBN-13
    "978-3-16-14841O-0",  # letra O no lugar do zero
    "0306406152 ; DROP TABLE livro",
]


@pytest.mark.parametrize("isbn", VALIDOS)
def test_isbn_valido(isbn):
    from app.core.isbn import isbn_valido

    assert isbn_valido(isbn) is True


@pytest.mark.parametrize("isbn", INVALIDOS)
def test_isbn_invalido(isbn):
    from app.core.isbn import isbn_valido

    assert isbn_valido(isbn) is False


@pytest.mark.parametrize(
    "entrada, esperado",
    [
        ("978-3-16-148410-0", "9783161484100"),
        (" 978 3 16 148410 0 ", "9783161484100"),
        ("0-306-40615-2", "0306406152"),
        ("0-8044-2957-x", "080442957X"),
    ],
)
def test_normalizar_isbn_deixa_so_digitos(entrada, esperado):
    from app.core.isbn import normalizar_isbn

    assert normalizar_isbn(entrada) == esperado


@pytest.mark.parametrize("isbn", ["", "123", "abc"])
def test_normalizar_isbn_invalido_levanta_value_error(isbn):
    from app.core.isbn import normalizar_isbn

    with pytest.raises(ValueError):
        normalizar_isbn(isbn)


def test_isbn_normalizado_cabe_na_coluna():
    from app.core.isbn import normalizar_isbn
    from app.models import Livro

    assert len(normalizar_isbn("978-3-16-148410-0")) <= Livro.__table__.c.isbn.type.length
