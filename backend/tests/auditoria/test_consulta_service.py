"""Camada "Service": consulta da auditoria (`app/services/auditoria_consulta.py`)."""

from datetime import timedelta

import pytest

from tests.auditoria.conftest import AGORA

pytestmark = pytest.mark.integracao


def _consulta():
    from app.services import auditoria_consulta

    return auditoria_consulta


def test_lista_do_mais_recente_para_o_mais_antigo(db_session, cria_registro):
    antigo = cria_registro(minutos_atras=30)
    recente = cria_registro(minutos_atras=1)
    meio = cria_registro(minutos_atras=10)

    registros, total = _consulta().listar_auditoria(db_session)

    assert [r.id for r in registros] == [recente.id, meio.id, antigo.id]
    assert total == 3


def test_desempata_pelo_id_quando_o_horario_e_igual(db_session, cria_registro):
    primeiro = cria_registro(minutos_atras=5)
    segundo = cria_registro(minutos_atras=5)

    registros, _ = _consulta().listar_auditoria(db_session)

    assert [r.id for r in registros] == [segundo.id, primeiro.id]


def test_filtra_por_entidade_e_entidade_id(db_session, cria_registro):
    alvo = cria_registro(entidade="LIVRO", entidade_id=7)
    cria_registro(entidade="LIVRO", entidade_id=8)
    cria_registro(entidade="PESSOA", entidade_id=7)

    registros, total = _consulta().listar_auditoria(db_session, entidade="LIVRO", entidade_id=7)

    assert [r.id for r in registros] == [alvo.id]
    assert total == 1


def test_filtra_por_acao(db_session, cria_registro):
    alvo = cria_registro(acao="ARQUIVAMENTO")
    cria_registro(acao="CADASTRO")

    registros, _ = _consulta().listar_auditoria(db_session, acao="ARQUIVAMENTO")

    assert [r.id for r in registros] == [alvo.id]


def test_filtra_por_responsavel_pelo_codigo(db_session, cria_registro, cria_usuario):
    outro = cria_usuario(papel="BIBLIOTECARIO")
    alvo = cria_registro(responsavel=outro)
    cria_registro()

    registros, _ = _consulta().listar_auditoria(db_session, responsavel_codigo=outro.codigo)

    assert [r.id for r in registros] == [alvo.id]


def test_filtra_por_periodo_inclui_de_e_exclui_ate(db_session, cria_registro):
    antes = cria_registro(minutos_atras=60)
    no_inicio = cria_registro(minutos_atras=30)
    dentro = cria_registro(minutos_atras=20)
    no_fim = cria_registro(minutos_atras=10)

    registros, _ = _consulta().listar_auditoria(
        db_session, de=AGORA - timedelta(minutes=30), ate=AGORA - timedelta(minutes=10)
    )

    ids = {r.id for r in registros}
    assert ids == {no_inicio.id, dentro.id}
    assert antes.id not in ids and no_fim.id not in ids


def test_filtros_combinam_com_e(db_session, cria_registro):
    alvo = cria_registro(entidade="LIVRO", acao="ALTERACAO", entidade_id=1)
    cria_registro(entidade="LIVRO", acao="CADASTRO", entidade_id=1)
    cria_registro(entidade="PESSOA", acao="ALTERACAO", entidade_id=1)

    registros, _ = _consulta().listar_auditoria(
        db_session, entidade="LIVRO", acao="ALTERACAO", entidade_id=1
    )

    assert [r.id for r in registros] == [alvo.id]


def test_paginacao_devolve_o_total_sem_limite(db_session, cria_registro):
    for minutos in range(5):
        cria_registro(minutos_atras=minutos)

    pagina, total = _consulta().listar_auditoria(db_session, limite=2, deslocamento=2)

    assert len(pagina) == 2
    assert total == 5


def test_limite_padrao_e_50(db_session, cria_registro):
    for minutos in range(55):
        cria_registro(minutos_atras=minutos)

    registros, total = _consulta().listar_auditoria(db_session)

    assert (len(registros), total) == (50, 55)


@pytest.mark.parametrize("limite", [0, -1, 201])
def test_limite_fora_de_1_a_200_e_recusado(db_session, limite):
    with pytest.raises(ValueError):
        _consulta().listar_auditoria(db_session, limite=limite)


def test_deslocamento_negativo_e_recusado(db_session):
    with pytest.raises(ValueError):
        _consulta().listar_auditoria(db_session, deslocamento=-1)


def test_periodo_invertido_e_recusado(db_session):
    with pytest.raises(ValueError):
        _consulta().listar_auditoria(db_session, de=AGORA, ate=AGORA - timedelta(days=1))


def test_registro_carrega_o_responsavel(db_session, cria_registro, bibliotecario):
    cria_registro()
    registros, _ = _consulta().listar_auditoria(db_session)
    assert registros[0].responsavel.codigo == bibliotecario.codigo


def test_obter_registro_por_id(db_session, cria_registro):
    registro = cria_registro()
    assert _consulta().obter_registro(db_session, registro.id).id == registro.id


def test_obter_registro_inexistente_levanta_erro(db_session):
    with pytest.raises(_consulta().RegistroNaoEncontradoError):
        _consulta().obter_registro(db_session, 999_999)


def test_consultar_nao_gera_novos_registros(db_session, cria_registro):
    cria_registro()
    _consulta().listar_auditoria(db_session)
    _, total = _consulta().listar_auditoria(db_session)
    assert total == 1
