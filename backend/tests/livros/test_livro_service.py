"""Camada "Service": regras do catálogo de livros.

Contrato de `app.services.livro_service`:
- calcular_disponibilidade(quantidade_total, emprestados, arquivado) -> (disponiveis, status)
- criar_livro(db, dados: LivroCriar, responsavel: Pessoa) -> LivroSaida
- listar_livros(db, *, nome=None, autor=None, isbn=None, genero=None, codigo=None,
                incluir_arquivados=False) -> list[LivroSaida]
- obter_livro(db, codigo, *, incluir_arquivados=False) -> LivroSaida
- atualizar_livro(db, codigo, dados: LivroAtualizar, responsavel: Pessoa) -> LivroSaida
- arquivar_livro(db, codigo, responsavel: Pessoa) -> LivroSaida
- contar_emprestimos_ativos(db, codigo) -> int   (EMPRESTADO + ATRASADO)
- erros: LivroNaoEncontradoError, LivroDuplicadoError, QuantidadeInsuficienteError
"""

import pytest
from sqlalchemy import select

from app.models import Auditoria, Livro
from tests.livros.conftest import payload_livro

# --- RF14: cálculo da disponibilidade (puro, sem DB) -----------------------------------------


@pytest.mark.parametrize(
    "total, emprestados, arquivado, esperado",
    [
        (3, 0, False, (3, "DISPONIVEL")),
        (3, 2, False, (1, "DISPONIVEL")),
        (3, 3, False, (0, "EMPRESTADO")),  # todos os exemplares fora
        (3, 1, True, (2, "INDISPONIVEL")),  # arquivado: não aceita novos empréstimos
        (0, 0, False, (0, "INDISPONIVEL")),  # sem exemplares cadastrados
    ],
    ids=[
        "todos_na_estante",
        "alguns_emprestados",
        "todos_emprestados",
        "arquivado",
        "sem_exemplar",
    ],
)
def test_calcular_disponibilidade(total, emprestados, arquivado, esperado):
    from app.services.livro_service import calcular_disponibilidade

    assert calcular_disponibilidade(total, emprestados, arquivado) == esperado


# --- RF01: criar -----------------------------------------------------------------------------


@pytest.fixture
def novo(db_session, bibliotecario):
    from app.schemas.livro import LivroCriar
    from app.services.livro_service import criar_livro

    def _novo(**kw):
        return criar_livro(db_session, LivroCriar(**payload_livro(**kw)), bibliotecario)

    return _novo


@pytest.mark.integracao
def test_criar_livro_persiste_com_isbn_normalizado(db_session, novo):
    saida = novo()

    livro = db_session.scalars(select(Livro).where(Livro.codigo == saida.codigo)).one()
    assert saida.codigo.startswith("liv_")
    assert livro.isbn == "9783161484100"
    assert (livro.arquivado, saida.quantidade_disponivel) == (False, 3)


@pytest.mark.integracao
@pytest.mark.parametrize("repetido", ["9783161484100", "978-3-16-148410-0", " 978 3 16 148410 0"])
def test_criar_livro_com_isbn_repetido_mesmo_com_outra_formatacao(novo, repetido):
    from app.services.livro_service import LivroDuplicadoError

    novo()

    with pytest.raises(LivroDuplicadoError):
        novo(isbn=repetido, nome="Outro título")


@pytest.mark.integracao
def test_criar_livro_registra_auditoria(db_session, bibliotecario, novo):
    saida = novo()

    livro = db_session.scalars(select(Livro).where(Livro.codigo == saida.codigo)).one()
    (reg,) = db_session.scalars(
        select(Auditoria).where(Auditoria.acao == "CADASTRO", Auditoria.entidade == "LIVRO")
    ).all()
    assert (reg.responsavel_id, reg.entidade_id) == (bibliotecario.id, livro.id)


# --- RF02 / RF18: consultar ------------------------------------------------------------------


@pytest.fixture
def acervo(cria_livro):
    return (
        cria_livro(isbn="9783161484100", nome="Dom Casmurro", autor="Machado de Assis"),
        cria_livro(isbn="0306406152", nome="Duna", autor="Frank Herbert", genero="Ficção"),
    )


@pytest.mark.integracao
@pytest.mark.parametrize(
    "filtro, idx",
    [
        ({"nome": "CASMURRO"}, 0),  # parcial, sem diferenciar maiúsculas
        ({"autor": "herbert"}, 1),
        ({"isbn": "0-306-40615-2"}, 1),  # a busca também normaliza o ISBN
        ({"genero": "ficção"}, 1),
        ({"codigo": "__codigo__"}, 0),
    ],
    ids=["nome", "autor", "isbn_com_hifens", "genero", "codigo_amigavel"],
)
def test_listar_livros_por_filtro(db_session, acervo, filtro, idx):
    from app.services.livro_service import listar_livros

    filtro = {k: (acervo[idx].codigo if v == "__codigo__" else v) for k, v in filtro.items()}

    assert [x.codigo for x in listar_livros(db_session, **filtro)] == [acervo[idx].codigo]


@pytest.mark.integracao
def test_listar_livros_sem_filtro_traz_todos_menos_arquivados(db_session, acervo, cria_livro):
    from app.services.livro_service import listar_livros

    arquivado = cria_livro(arquivado=True)

    codigos = {x.codigo for x in listar_livros(db_session)}
    com_arquivados = {x.codigo for x in listar_livros(db_session, incluir_arquivados=True)}

    assert codigos == {livro.codigo for livro in acervo}
    assert arquivado.codigo in com_arquivados


@pytest.mark.integracao
def test_listar_livros_calcula_disponibilidade_com_emprestimos_e_perdas(
    db_session, cria_livro, cria_emprestimo, devolvido
):
    from app.services.livro_service import obter_livro

    livro = cria_livro(quantidade_total=4)
    cria_emprestimo(livro)  # EMPRESTADO: ocupa exemplar
    cria_emprestimo(livro, status_atual="ATRASADO")  # ocupa exemplar
    cria_emprestimo(livro, **devolvido)  # devolvido: exemplar voltou
    cria_emprestimo(livro, status_atual="PERDIDO")  # perdido: exemplar não volta

    saida = obter_livro(db_session, livro.codigo)

    assert (saida.quantidade_total, saida.quantidade_disponivel) == (4, 1)
    assert saida.disponibilidade == "DISPONIVEL"


@pytest.mark.integracao
def test_obter_livro_inexistente(db_session):
    from app.services.livro_service import LivroNaoEncontradoError, obter_livro

    with pytest.raises(LivroNaoEncontradoError):
        obter_livro(db_session, "liv_99999999")


@pytest.mark.integracao
def test_obter_livro_arquivado_so_com_incluir_arquivados(db_session, cria_livro):
    from app.services.livro_service import LivroNaoEncontradoError, obter_livro

    livro = cria_livro(arquivado=True)

    with pytest.raises(LivroNaoEncontradoError):
        obter_livro(db_session, livro.codigo)
    saida = obter_livro(db_session, livro.codigo, incluir_arquivados=True)
    assert (saida.arquivado, saida.disponibilidade) == (True, "INDISPONIVEL")


# --- RF03: editar ----------------------------------------------------------------------------


@pytest.mark.integracao
def test_atualizar_livro_altera_so_o_que_foi_enviado(db_session, bibliotecario, acervo):
    from app.schemas.livro import LivroAtualizar
    from app.services.livro_service import atualizar_livro

    antes = acervo[0]
    autor = antes.autor

    saida = atualizar_livro(
        db_session, antes.codigo, LivroAtualizar(editora="Nova Editora"), bibliotecario
    )

    assert (saida.editora, saida.autor) == ("Nova Editora", autor)


@pytest.mark.integracao
def test_atualizar_livro_com_isbn_de_outro_livro(db_session, bibliotecario, acervo):
    from app.schemas.livro import LivroAtualizar
    from app.services.livro_service import LivroDuplicadoError, atualizar_livro

    with pytest.raises(LivroDuplicadoError):
        atualizar_livro(
            db_session, acervo[0].codigo, LivroAtualizar(isbn="0-306-40615-2"), bibliotecario
        )


@pytest.mark.integracao
def test_atualizar_livro_mantendo_o_proprio_isbn_nao_e_duplicidade(
    db_session, bibliotecario, acervo
):
    from app.schemas.livro import LivroAtualizar
    from app.services.livro_service import atualizar_livro

    saida = atualizar_livro(
        db_session, acervo[1].codigo, LivroAtualizar(isbn="0-306-40615-2"), bibliotecario
    )
    assert saida.isbn == "0306406152"


@pytest.mark.integracao
def test_atualizar_livro_nao_pode_deixar_menos_exemplares_que_emprestimos_ativos(
    db_session, bibliotecario, cria_livro, cria_emprestimo
):
    """Regra proposta: `quantidade_total` não pode ficar abaixo do que está emprestado."""
    from app.schemas.livro import LivroAtualizar
    from app.services.livro_service import QuantidadeInsuficienteError, atualizar_livro

    livro = cria_livro(quantidade_total=2)
    cria_emprestimo(livro)
    cria_emprestimo(livro)

    with pytest.raises(QuantidadeInsuficienteError):
        atualizar_livro(db_session, livro.codigo, LivroAtualizar(quantidade_total=1), bibliotecario)


@pytest.mark.integracao
def test_atualizar_livro_registra_auditoria_com_antes_e_depois(db_session, bibliotecario, acervo):
    from app.schemas.livro import LivroAtualizar
    from app.services.livro_service import atualizar_livro

    atualizar_livro(db_session, acervo[0].codigo, LivroAtualizar(editora="Nova"), bibliotecario)

    (reg,) = db_session.scalars(
        select(Auditoria).where(Auditoria.acao == "ALTERACAO", Auditoria.entidade == "LIVRO")
    ).all()
    assert reg.entidade_id == acervo[0].id
    assert reg.dados["depois"]["editora"] == "Nova"
    assert reg.dados["antes"]["editora"] == "Editora"


@pytest.mark.integracao
def test_atualizar_livro_inexistente(db_session, bibliotecario):
    from app.schemas.livro import LivroAtualizar
    from app.services.livro_service import LivroNaoEncontradoError, atualizar_livro

    with pytest.raises(LivroNaoEncontradoError):
        atualizar_livro(db_session, "liv_99999999", LivroAtualizar(nome="X"), bibliotecario)


# --- RF04 / RF19: arquivar -------------------------------------------------------------------


@pytest.mark.integracao
def test_contar_emprestimos_ativos(db_session, cria_livro, cria_emprestimo, devolvido):
    from app.services.livro_service import contar_emprestimos_ativos

    livro = cria_livro(quantidade_total=6)
    cria_emprestimo(livro)
    cria_emprestimo(livro, status_atual="ATRASADO")
    cria_emprestimo(livro, **devolvido)
    cria_emprestimo(
        livro, status_atual="DEVOLVIDO_COM_ATRASO", data_devolucao=devolvido["data_devolucao"]
    )
    cria_emprestimo(livro, status_atual="PERDIDO")

    assert contar_emprestimos_ativos(db_session, livro.codigo) == 2


@pytest.mark.integracao
def test_arquivar_livro_nao_apaga_nem_mexe_nos_emprestimos(
    db_session, bibliotecario, cria_livro, cria_emprestimo
):
    from app.services.livro_service import arquivar_livro

    livro = cria_livro()
    emprestimo = cria_emprestimo(livro)

    saida = arquivar_livro(db_session, livro.codigo, bibliotecario)

    db_session.refresh(emprestimo)
    assert (saida.arquivado, saida.disponibilidade) == (True, "INDISPONIVEL")
    assert emprestimo.status_atual == "EMPRESTADO" and emprestimo.data_devolucao is None


@pytest.mark.integracao
def test_arquivar_livro_registra_auditoria(db_session, bibliotecario, cria_livro):
    from app.services.livro_service import arquivar_livro

    livro = cria_livro()

    arquivar_livro(db_session, livro.codigo, bibliotecario)

    (reg,) = db_session.scalars(
        select(Auditoria).where(Auditoria.acao == "ARQUIVAMENTO", Auditoria.entidade == "LIVRO")
    ).all()
    assert (reg.responsavel_id, reg.entidade_id) == (bibliotecario.id, livro.id)


@pytest.mark.integracao
def test_arquivar_livro_inexistente(db_session, bibliotecario):
    from app.services.livro_service import LivroNaoEncontradoError, arquivar_livro

    with pytest.raises(LivroNaoEncontradoError):
        arquivar_livro(db_session, "liv_99999999", bibliotecario)
