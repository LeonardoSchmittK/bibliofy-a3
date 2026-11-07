"""Camada "View": schemas de livro (unitário, sem DB).

Contrato de `app.schemas.livro`:
- LivroCriar:     isbn (normalizado), nome, autor, editora, genero, data_lancamento,
                  quantidade_total >= 0, descricao opcional. Sem `codigo`/`arquivado`.
- LivroAtualizar: os mesmos campos, todos opcionais. Sem `codigo`/`arquivado`.
- LivroSaida:     codigo, isbn, nome, autor, editora, genero, data_lancamento, descricao,
                  quantidade_total, quantidade_disponivel, disponibilidade, arquivado.
                  disponibilidade in {"DISPONIVEL", "EMPRESTADO", "INDISPONIVEL"}.
"""

from datetime import date

import pytest
from pydantic import ValidationError

from tests.livros.conftest import payload_livro

OBRIGATORIOS = ["isbn", "nome", "autor", "editora", "genero", "data_lancamento", "quantidade_total"]


# --- LivroCriar ------------------------------------------------------------------------------


def test_livro_criar_valido_e_normaliza_o_isbn():
    from app.schemas.livro import LivroCriar

    dados = LivroCriar(**payload_livro())

    assert dados.isbn == "9783161484100"
    assert dados.data_lancamento == date(1899, 1, 1)
    assert dados.quantidade_total == 3


def test_livro_criar_descricao_e_opcional():
    from app.schemas.livro import LivroCriar

    corpo = payload_livro()
    del corpo["descricao"]
    assert LivroCriar(**corpo).descricao is None


@pytest.mark.parametrize("campo", OBRIGATORIOS)
def test_livro_criar_campo_obrigatorio(campo):
    from app.schemas.livro import LivroCriar

    corpo = payload_livro()
    del corpo[campo]
    with pytest.raises(ValidationError):
        LivroCriar(**corpo)


@pytest.mark.parametrize("campo", ["isbn", "nome", "autor", "editora", "genero"])
def test_livro_criar_texto_obrigatorio_nao_pode_ser_vazio(campo):
    from app.schemas.livro import LivroCriar

    with pytest.raises(ValidationError):
        LivroCriar(**payload_livro(**{campo: "  "}))


@pytest.mark.parametrize("isbn", ["123", "abc", "978-3-16-148410"])
def test_livro_criar_isbn_invalido(isbn):
    from app.schemas.livro import LivroCriar

    with pytest.raises(ValidationError):
        LivroCriar(**payload_livro(isbn=isbn))


@pytest.mark.parametrize("quantidade", [-1, "muitos", 1.5])
def test_livro_criar_quantidade_invalida(quantidade):
    from app.schemas.livro import LivroCriar

    with pytest.raises(ValidationError):
        LivroCriar(**payload_livro(quantidade_total=quantidade))


def test_livro_criar_data_invalida():
    from app.schemas.livro import LivroCriar

    with pytest.raises(ValidationError):
        LivroCriar(**payload_livro(data_lancamento="31/02/2020"))


def test_livro_criar_nao_deixa_o_cliente_definir_codigo_nem_arquivado():
    from app.schemas.livro import LivroCriar

    assert not {"codigo", "arquivado"} & set(LivroCriar.model_fields)


# --- LivroAtualizar --------------------------------------------------------------------------


def test_livro_atualizar_aceita_edicao_parcial():
    from app.schemas.livro import LivroAtualizar

    dados = LivroAtualizar(editora="Nova Editora")

    assert dados.model_dump(exclude_unset=True) == {"editora": "Nova Editora"}


def test_livro_atualizar_normaliza_isbn_quando_informado():
    from app.schemas.livro import LivroAtualizar

    assert LivroAtualizar(isbn="0-306-40615-2").isbn == "0306406152"


@pytest.mark.parametrize("campo", ["isbn", "nome", "autor", "editora", "genero"])
def test_livro_atualizar_nao_aceita_texto_obrigatorio_vazio(campo):
    from app.schemas.livro import LivroAtualizar

    with pytest.raises(ValidationError):
        LivroAtualizar(**{campo: ""})


def test_livro_atualizar_quantidade_negativa():
    from app.schemas.livro import LivroAtualizar

    with pytest.raises(ValidationError):
        LivroAtualizar(quantidade_total=-1)


def test_livro_atualizar_nao_edita_codigo_nem_arquivado():
    """Arquivar tem operação própria; `codigo` é gerado pelo banco."""
    from app.schemas.livro import LivroAtualizar

    assert not {"codigo", "arquivado", "quantidade_disponivel"} & set(LivroAtualizar.model_fields)


# --- LivroSaida ------------------------------------------------------------------------------


def _saida(**kw) -> dict:
    base = dict(
        codigo="liv_00000001", isbn="9783161484100", nome="Dom Casmurro",
        autor="Machado de Assis", editora="Garnier", genero="Romance",
        data_lancamento=date(1899, 1, 1), descricao=None, quantidade_total=3,
        quantidade_disponivel=2, disponibilidade="DISPONIVEL", arquivado=False,
    )  # fmt: skip
    return {**base, **kw}


def test_livro_saida_traz_disponibilidade():
    from app.schemas.livro import LivroSaida

    saida = LivroSaida(**_saida())

    assert (saida.quantidade_total, saida.quantidade_disponivel) == (3, 2)
    assert saida.disponibilidade == "DISPONIVEL"


@pytest.mark.parametrize("status", ["DISPONIVEL", "EMPRESTADO", "INDISPONIVEL"])
def test_livro_saida_aceita_os_tres_status(status):
    from app.schemas.livro import LivroSaida

    assert LivroSaida(**_saida(disponibilidade=status)).disponibilidade == status


@pytest.mark.parametrize("status", ["disponivel", "ATRASADO", ""])
def test_livro_saida_recusa_status_desconhecido(status):
    from app.schemas.livro import LivroSaida

    with pytest.raises(ValidationError):
        LivroSaida(**_saida(disponibilidade=status))
