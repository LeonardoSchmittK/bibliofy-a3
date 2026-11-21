"""Camada "Model/View": schemas de saída da auditoria (app/schemas/auditoria.py). Sem banco."""

from datetime import UTC, datetime
from types import SimpleNamespace

import pytest
from pydantic import ValidationError


def _registro(**kw):
    responsavel = SimpleNamespace(
        codigo="cus_00000001", nome="Bia", senha_hash="NUNCA", email="bia@escola.edu"
    )
    base = dict(
        id=5, acao="ALTERACAO", entidade="LIVRO", entidade_id=9, responsavel=responsavel,
        dados={"antes": {"nome": "A"}, "depois": {"nome": "B"}},
        criado_em=datetime(2026, 3, 10, 12, 0, tzinfo=UTC),
        responsavel_id=1,
    )  # fmt: skip
    return SimpleNamespace(**{**base, **kw})


def test_saida_le_o_registro_do_banco():
    from app.schemas.auditoria import AuditoriaSaida

    saida = AuditoriaSaida.model_validate(_registro())
    assert (saida.id, saida.acao, saida.entidade, saida.entidade_id) == (5, "ALTERACAO", "LIVRO", 9)
    assert saida.dados == {"antes": {"nome": "A"}, "depois": {"nome": "B"}}
    assert saida.criado_em == datetime(2026, 3, 10, 12, 0, tzinfo=UTC)


def test_saida_mostra_o_responsavel_por_codigo_e_nome_apenas():
    from app.schemas.auditoria import AuditoriaSaida

    saida = AuditoriaSaida.model_validate(_registro()).model_dump()
    assert saida["responsavel"] == {"codigo": "cus_00000001", "nome": "Bia"}
    assert "senha_hash" not in str(saida) and "bia@escola.edu" not in str(saida)
    assert "responsavel_id" not in saida  # id interno não vaza


def test_saida_aceita_dados_nulos():
    from app.schemas.auditoria import AuditoriaSaida

    assert AuditoriaSaida.model_validate(_registro(dados=None)).dados is None


@pytest.mark.parametrize("campo,valor", [("acao", "TROCAR"), ("entidade", "USUARIO")])
def test_saida_recusa_acao_ou_entidade_fora_do_dominio(campo, valor):
    from app.schemas.auditoria import AuditoriaSaida

    with pytest.raises(ValidationError):
        AuditoriaSaida.model_validate(_registro(**{campo: valor}))


def test_pagina_tem_itens_total_limite_e_deslocamento():
    from app.schemas.auditoria import AuditoriaSaida, PaginaAuditoria

    pagina = PaginaAuditoria(
        itens=[AuditoriaSaida.model_validate(_registro())], total=1, limite=50, deslocamento=0
    )
    assert set(pagina.model_dump()) == {"itens", "total", "limite", "deslocamento"}
