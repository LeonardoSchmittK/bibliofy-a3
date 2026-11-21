import pytest
from sqlalchemy import func, select

from app.core.security import verificar_senha
from app.models import Livro, Pessoa
from scripts.seed import LIVROS, semear


def _digito_isbn13(base12: str) -> str:
    soma = sum(int(d) * (1 if i % 2 == 0 else 3) for i, d in enumerate(base12))
    return str((10 - soma % 10) % 10)


def test_isbns_do_catalogo_sao_isbn13_validos_e_unicos():
    isbns = [livro[0] for livro in LIVROS]
    assert len(set(isbns)) == len(isbns)
    for isbn in isbns:
        assert len(isbn) == 13 and isbn.isdigit()
        assert isbn[-1] == _digito_isbn13(isbn[:12]), isbn


@pytest.mark.integracao
def test_seed_cria_usuarios_e_livros_com_senha_hash(db_session):
    usuarios, livros = semear(db_session)

    assert (usuarios, livros) == (2, len(LIVROS))
    pessoas = {p.papel: p for p in db_session.scalars(select(Pessoa))}
    assert set(pessoas) == {"BIBLIOTECARIO", "LEITOR"}
    assert verificar_senha("Bibliofy@Demo1", pessoas["LEITOR"].senha_hash)
    assert pessoas["LEITOR"].senha_hash != "Bibliofy@Demo1"


@pytest.mark.integracao
def test_seed_e_idempotente_e_preserva_dados_existentes(db_session):
    semear(db_session)
    db_session.add(
        Livro(
            isbn="9780000000002",
            nome="Cadastrado na plataforma",
            autor="A",
            editora="E",
            genero="G",
            data_lancamento="2020-01-01",
            quantidade_total=1,
        )
    )
    db_session.commit()

    assert semear(db_session) == (0, 0)
    assert db_session.scalar(select(func.count()).select_from(Livro)) == len(LIVROS) + 1
    assert db_session.scalar(select(func.count()).select_from(Pessoa)) == 2
