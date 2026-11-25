"""SEC02/SEC03: núcleo de segurança, hash de senha e JWT (unitário, sem DB).

Contrato de `app.core.security`:
- hash_senha(senha) -> str            (Argon2id via pwdlib, configuração padrão)
- verificar_senha(senha, hash) -> bool (nunca levanta exceção; hash inválido => False)
- criar_token_acesso(pessoa) -> str    (JWT assinado: sub, iat, exp)
- decodificar_token(token) -> dict     (levanta TokenInvalidoError para qualquer problema)
- TokenInvalidoError
"""

from datetime import timedelta

import jwt
import pytest
import time_machine

from app.models import Pessoa
from tests.auth.conftest import AGORA, SENHA


def _pessoa() -> Pessoa:
    return Pessoa(codigo="cus_00000001", papel="LEITOR", ativo=True)


# --- hash de senha ---------------------------------------------------------------------------


def test_hash_usa_argon2id():
    from app.core.security import hash_senha

    assert hash_senha(SENHA).startswith("$argon2id$")


def test_hash_nao_contem_a_senha():
    from app.core.security import hash_senha

    assert SENHA not in hash_senha(SENHA)


def test_hash_tem_salt_proprio_a_cada_chamada():
    from app.core.security import hash_senha

    assert hash_senha(SENHA) != hash_senha(SENHA)


def test_hash_cabe_na_coluna_senha_hash():
    from app.core.security import hash_senha

    limite = Pessoa.__table__.c.senha_hash.type.length
    assert len(hash_senha(SENHA)) <= limite


@pytest.mark.parametrize(
    "tentativa, esperado",
    [(SENHA, True), ("senha-errada", False), (SENHA.upper(), False), ("", False)],
    ids=["correta", "errada", "caixa_diferente", "vazia"],
)
def test_verificar_senha(tentativa, esperado):
    from app.core.security import hash_senha, verificar_senha

    assert verificar_senha(tentativa, hash_senha(SENHA)) is esperado


@pytest.mark.parametrize("hash_invalido", ["", "texto-puro", SENHA, "$argon2id$quebrado"])
def test_verificar_senha_com_hash_invalido_apenas_recusa(hash_invalido):
    from app.core.security import verificar_senha

    assert verificar_senha(SENHA, hash_invalido) is False


# --- emissão do token ------------------------------------------------------------------------


def test_token_traz_somente_identificacao_e_validade():
    from app.core.config import get_settings
    from app.core.security import criar_token_acesso

    token = criar_token_acesso(_pessoa())

    cabecalho = jwt.get_unverified_header(token)
    claims = jwt.decode(token, get_settings().jwt_secret, algorithms=["HS256"])
    assert cabecalho["alg"] == "HS256"
    assert set(claims) == {"sub", "iat", "exp"}  # sem e-mail, papel ou qualquer dado pessoal
    assert claims["sub"] == "cus_00000001"


def test_token_expira_em_no_maximo_15_minutos():
    from app.core.config import get_settings
    from app.core.security import criar_token_acesso

    claims = jwt.decode(
        criar_token_acesso(_pessoa()), get_settings().jwt_secret, algorithms=["HS256"]
    )

    assert timedelta(0) < timedelta(seconds=claims["exp"] - claims["iat"]) <= timedelta(minutes=15)
    assert claims["iat"] == int(AGORA.timestamp())


# --- validação do token ----------------------------------------------------------------------


def test_decodificar_token_valido():
    from app.core.security import criar_token_acesso, decodificar_token

    assert decodificar_token(criar_token_acesso(_pessoa()))["sub"] == "cus_00000001"


def test_token_ainda_vale_aos_14_minutos_e_expira_depois_dos_15():
    from app.core.security import TokenInvalidoError, criar_token_acesso, decodificar_token

    token = criar_token_acesso(_pessoa())

    with time_machine.travel(AGORA + timedelta(minutes=14), tick=False):
        assert decodificar_token(token)["sub"] == "cus_00000001"
    with time_machine.travel(AGORA + timedelta(minutes=15, seconds=1), tick=False):
        with pytest.raises(TokenInvalidoError):
            decodificar_token(token)


def test_token_adulterado_e_recusado(emite_token, adultera):
    from app.core.security import TokenInvalidoError, decodificar_token

    token = adultera(emite_token(_pessoa()), sub="cus_00000099")

    with pytest.raises(TokenInvalidoError):
        decodificar_token(token)


def test_token_assinado_com_outra_chave_e_recusado(emite_token):
    from app.core.security import TokenInvalidoError, decodificar_token

    with pytest.raises(TokenInvalidoError):
        decodificar_token(emite_token(_pessoa(), segredo="chave-de-outro-sistema-0123456789abc"))


def test_token_sem_assinatura_alg_none_e_recusado():
    from app.core.security import TokenInvalidoError, decodificar_token

    sem_assinatura = jwt.encode(
        {"sub": "cus_00000001", "exp": AGORA + timedelta(hours=1)}, None, "none"
    )

    with pytest.raises(TokenInvalidoError):
        decodificar_token(sem_assinatura)


def test_token_assinado_com_outro_algoritmo_e_recusado(emite_token):
    from app.core.security import TokenInvalidoError, decodificar_token

    token = emite_token(_pessoa(), algoritmo="HS512")

    with pytest.raises(TokenInvalidoError):
        decodificar_token(token)


@pytest.mark.parametrize("ausente", ["sub", "exp", "iat"])
def test_token_sem_claim_obrigatoria_e_recusado(ausente):
    from app.core.config import get_settings
    from app.core.security import TokenInvalidoError, decodificar_token

    claims = {"sub": "cus_00000001", "iat": AGORA, "exp": AGORA + timedelta(minutes=5)}
    del claims[ausente]
    token = jwt.encode(claims, get_settings().jwt_secret, algorithm="HS256")

    with pytest.raises(TokenInvalidoError):
        decodificar_token(token)


@pytest.mark.parametrize("lixo", ["", "abc", "a.b.c", "Bearer x"])
def test_texto_que_nao_e_jwt_e_recusado(lixo):
    from app.core.security import TokenInvalidoError, decodificar_token

    with pytest.raises(TokenInvalidoError):
        decodificar_token(lixo)
