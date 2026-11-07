"""Escrita da auditoria: `app.services.auditoria` (RNF10 / SEC05).

`sanitizar_dados` e as constantes são puros e rodam sem banco; o resto exige PostgreSQL.
"""

import re
from pathlib import Path
from unittest.mock import patch

import pytest
from sqlalchemy import func, select

from app.models import Auditoria

SCHEMA_SQL = Path(__file__).resolve().parents[2] / "database" / "schema.sql"


def _servico():
    from app.services import auditoria

    return auditoria


# --- constantes alinhadas ao banco (puros) -----------------------------------------------------


def _valores_check(nome_constraint: str) -> set[str]:
    sql = SCHEMA_SQL.read_text(encoding="utf-8")
    bloco = re.search(rf"CONSTRAINT {nome_constraint} CHECK \(\w+ IN\s*\((.*?)\)\)", sql, re.S)
    assert bloco, f"CHECK {nome_constraint} não encontrado em schema.sql"
    return set(re.findall(r"'([A-Z_]+)'", bloco.group(1)))


def test_acoes_iguais_ao_check_do_banco():
    assert set(_servico().ACOES) == _valores_check("ck_auditoria_acao")


def test_entidades_iguais_ao_check_do_banco():
    assert set(_servico().ENTIDADES) == _valores_check("ck_auditoria_entidade")


# --- sanitização (pura) ------------------------------------------------------------------------


def test_sanitizar_remove_chaves_proibidas_em_qualquer_nivel():
    dados = {
        "nome": "Ana", "senha": "x", "senha_hash": "h", "access_token": "t",
        "extra": {"senha": "y", "ok": 1, "lista": [{"access_token": "z", "k": 2}]},
    }  # fmt: skip
    assert _servico().sanitizar_dados(dados) == {
        "nome": "Ana",
        "extra": {"ok": 1, "lista": [{"k": 2}]},
    }


def test_sanitizar_nao_altera_o_dicionario_original():
    dados = {"senha": "x", "nome": "Ana"}
    _servico().sanitizar_dados(dados)
    assert dados == {"senha": "x", "nome": "Ana"}


def test_sanitizar_none_continua_none():
    assert _servico().sanitizar_dados(None) is None


def test_sanitizar_converte_tipos_nao_json_para_texto():
    from datetime import date

    saida = _servico().sanitizar_dados({"data": date(2026, 3, 10)})
    assert saida == {"data": "2026-03-10"}


# --- registrar ---------------------------------------------------------------------------------


def test_registrar_grava_todos_os_campos(db_session, bibliotecario):
    registro = _servico().registrar(
        db_session, responsavel=bibliotecario, acao="CADASTRO", entidade="LIVRO",
        entidade_id=7, dados={"nome": "Dom Casmurro"},
    )  # fmt: skip
    assert registro.id is not None  # flush feito
    assert registro.responsavel_id == bibliotecario.id
    assert (registro.acao, registro.entidade, registro.entidade_id) == ("CADASTRO", "LIVRO", 7)
    assert registro.dados == {"nome": "Dom Casmurro"}
    assert registro.criado_em is not None and registro.criado_em.tzinfo is not None


def test_registrar_nunca_grava_senha_nem_token(db_session, bibliotecario):
    registro = _servico().registrar(
        db_session, responsavel=bibliotecario, acao="CADASTRO", entidade="PESSOA",
        entidade_id=1, dados={"nome": "Ana", "senha": "x", "senha_hash": "h", "access_token": "t"},
    )  # fmt: skip
    assert registro.dados == {"nome": "Ana"}


def test_registrar_aceita_dados_none(db_session, bibliotecario):
    registro = _servico().registrar(
        db_session, responsavel=bibliotecario, acao="PERDA", entidade="EMPRESTIMO", entidade_id=3
    )
    assert registro.dados is None


def test_registrar_nao_faz_commit(db_session, bibliotecario):
    with patch.object(db_session, "commit") as commit:
        _servico().registrar(
            db_session, responsavel=bibliotecario, acao="CADASTRO", entidade="LIVRO", entidade_id=1
        )
    commit.assert_not_called()


def test_registrar_participa_da_transacao_da_operacao(db_session, bibliotecario):
    """Se a operação auditada desfaz, o registro some junto (mesma transação)."""
    with db_session.begin_nested() as operacao:
        _servico().registrar(
            db_session, responsavel=bibliotecario, acao="EMPRESTIMO", entidade="EMPRESTIMO",
            entidade_id=1,
        )  # fmt: skip
        operacao.rollback()
    assert db_session.scalar(select(func.count()).select_from(Auditoria)) == 0


@pytest.mark.parametrize("acao", ["TROCAR", "", "cadastro", None])
def test_registrar_recusa_acao_invalida(db_session, bibliotecario, acao):
    with pytest.raises(_servico().AuditoriaInvalidaError):
        _servico().registrar(
            db_session, responsavel=bibliotecario, acao=acao, entidade="LIVRO", entidade_id=1
        )


@pytest.mark.parametrize("entidade", ["USUARIO", "", "livro", None])
def test_registrar_recusa_entidade_invalida(db_session, bibliotecario, entidade):
    with pytest.raises(_servico().AuditoriaInvalidaError):
        _servico().registrar(
            db_session, responsavel=bibliotecario, acao="CADASTRO", entidade=entidade, entidade_id=1
        )


def test_auditoria_invalida_error_e_value_error():
    assert issubclass(_servico().AuditoriaInvalidaError, ValueError)


def test_registrar_nao_cria_nada_quando_invalido(db_session, bibliotecario):
    with pytest.raises(_servico().AuditoriaInvalidaError):
        _servico().registrar(
            db_session, responsavel=bibliotecario, acao="X", entidade="LIVRO", entidade_id=1
        )
    assert db_session.scalar(select(func.count()).select_from(Auditoria)) == 0
