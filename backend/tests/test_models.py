from datetime import date

import pytest
from sqlalchemy.exc import IntegrityError

from app.models import Auditoria, Bloqueio, Emprestimo, Livro, Pessoa

pytestmark = pytest.mark.integracao


def _pessoa(n: int = 1, **kw) -> Pessoa:
    campos = dict(matricula=f"mat{n}", nome="Ana", email=f"ana{n}@x.com", senha_hash="h")
    return Pessoa(**{**campos, **kw})


def _livro(n: int = 1, **kw) -> Livro:
    campos = dict(
        isbn=f"978{n}", nome="L", autor="A", editora="E", genero="G",
        data_lancamento=date(2020, 1, 1), quantidade_total=1,
    )  # fmt: skip
    return Livro(**{**campos, **kw})


def _emprestimo(pessoa: Pessoa, livro: Livro, **kw) -> Emprestimo:
    campos = dict(
        pessoa_id=pessoa.id, livro_id=livro.id,
        data_emprestimo=date(2026, 1, 1), data_prevista=date(2026, 1, 8),
    )  # fmt: skip
    return Emprestimo(**{**campos, **kw})


def _salva(session, *objs):
    session.add_all(objs)
    session.flush()


def test_defaults_do_banco(db_session):
    pessoa, livro = _pessoa(), _livro()
    _salva(db_session, pessoa, livro)
    emp = _emprestimo(pessoa, livro)
    _salva(db_session, emp)

    assert pessoa.codigo.startswith("cus_") and pessoa.papel == "LEITOR" and pessoa.ativo
    assert pessoa.telefone is None
    assert livro.codigo.startswith("liv_") and livro.arquivado is False
    assert emp.codigo.startswith("emp_") and emp.status_atual == "EMPRESTADO"
    assert emp.renovado is False and emp.data_devolucao is None


@pytest.mark.parametrize(
    "outro",
    [
        dict(matricula="mat1"),
        dict(email="ANA1@X.COM"),
    ],
    ids=["matricula", "email_case_insensitive"],
)
def test_pessoa_unicidade(db_session, outro):
    _salva(db_session, _pessoa(1))
    with pytest.raises(IntegrityError):
        _salva(db_session, _pessoa(2, **outro))


def test_pessoa_papel_invalido(db_session):
    with pytest.raises(IntegrityError):
        _salva(db_session, _pessoa(papel="ADMIN"))


def test_livro_isbn_unico(db_session):
    _salva(db_session, _livro(1))
    with pytest.raises(IntegrityError):
        _salva(db_session, _livro(2, isbn="9781"))


def test_livro_quantidade_negativa(db_session):
    with pytest.raises(IntegrityError):
        _salva(db_session, _livro(quantidade_total=-1))


def test_emprestimo_so_um_ativo_por_pessoa(db_session):
    pessoa, l1, l2 = _pessoa(), _livro(1), _livro(2)
    _salva(db_session, pessoa, l1, l2)
    _salva(db_session, _emprestimo(pessoa, l1))
    with pytest.raises(IntegrityError):
        _salva(db_session, _emprestimo(pessoa, l2))


def test_emprestimo_devolvido_libera_novo(db_session):
    pessoa, l1, l2 = _pessoa(), _livro(1), _livro(2)
    _salva(db_session, pessoa, l1, l2)
    _salva(
        db_session,
        _emprestimo(pessoa, l1, status_atual="DEVOLVIDO", data_devolucao=date(2026, 1, 5)),
        _emprestimo(pessoa, l2),
    )


def test_emprestimo_status_exige_data_devolucao(db_session):
    pessoa, livro = _pessoa(), _livro()
    _salva(db_session, pessoa, livro)
    with pytest.raises(IntegrityError):
        _salva(db_session, _emprestimo(pessoa, livro, status_atual="DEVOLVIDO"))


def test_emprestimo_data_prevista_anterior(db_session):
    pessoa, livro = _pessoa(), _livro()
    _salva(db_session, pessoa, livro)
    with pytest.raises(IntegrityError):
        _salva(db_session, _emprestimo(pessoa, livro, data_prevista=date(2025, 12, 31)))


def test_emprestimo_livro_arquivado_bloqueado(db_session):
    pessoa, livro = _pessoa(), _livro(arquivado=True)
    _salva(db_session, pessoa, livro)
    with pytest.raises(IntegrityError):
        _salva(db_session, _emprestimo(pessoa, livro))


def test_fk_restrict_impede_apagar_pessoa_com_emprestimo(db_session):
    pessoa, livro = _pessoa(), _livro()
    _salva(db_session, pessoa, livro)
    _salva(db_session, _emprestimo(pessoa, livro))
    with pytest.raises(IntegrityError):
        db_session.delete(pessoa)
        db_session.flush()


def test_bloqueio(db_session):
    pessoa, livro = _pessoa(), _livro()
    _salva(db_session, pessoa, livro)
    emp = _emprestimo(pessoa, livro, status_atual="ATRASADO")
    _salva(db_session, emp)
    bloqueio = Bloqueio(
        pessoa_id=pessoa.id, emprestimo_id=emp.id,
        inicio=date(2026, 1, 10), fim_exclusivo=date(2026, 1, 17), motivo="atraso",
    )  # fmt: skip
    _salva(db_session, bloqueio)
    assert bloqueio.id is not None


def test_bloqueio_pessoa_diferente_do_emprestimo(db_session):
    p1, p2, livro = _pessoa(1), _pessoa(2), _livro()
    _salva(db_session, p1, p2, livro)
    emp = _emprestimo(p1, livro)
    _salva(db_session, emp)
    with pytest.raises(IntegrityError):
        _salva(
            db_session,
            Bloqueio(
                pessoa_id=p2.id,
                emprestimo_id=emp.id,
                inicio=date(2026, 1, 10),
                fim_exclusivo=date(2026, 1, 17),
                motivo="x",
            ),  # fmt: skip
        )


def test_bloqueio_periodo_invalido(db_session):
    pessoa, livro = _pessoa(), _livro()
    _salva(db_session, pessoa, livro)
    emp = _emprestimo(pessoa, livro)
    _salva(db_session, emp)
    with pytest.raises(IntegrityError):
        _salva(
            db_session,
            Bloqueio(
                pessoa_id=pessoa.id,
                emprestimo_id=emp.id,
                inicio=date(2026, 1, 10),
                fim_exclusivo=date(2026, 1, 10),
                motivo="x",
            ),  # fmt: skip
        )


def test_auditoria_jsonb_e_criado_em(db_session):
    pessoa = _pessoa()
    _salva(db_session, pessoa)
    aud = Auditoria(
        responsavel_id=pessoa.id, acao="CADASTRO", entidade="PESSOA",
        entidade_id=pessoa.id, dados={"nome": "Ana"},
    )  # fmt: skip
    _salva(db_session, aud)
    db_session.refresh(aud)
    assert aud.dados == {"nome": "Ana"}
    assert aud.criado_em is not None


def test_auditoria_acao_invalida(db_session):
    pessoa = _pessoa()
    _salva(db_session, pessoa)
    with pytest.raises(IntegrityError):
        _salva(
            db_session,
            Auditoria(
                responsavel_id=pessoa.id,
                acao="EXCLUSAO",
                entidade="PESSOA",
                entidade_id=pessoa.id,
            ),  # fmt: skip
        )
