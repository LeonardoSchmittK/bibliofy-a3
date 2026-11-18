"""Camada "View" do MVC: schemas Pydantic de entrada e saída (unitário, sem DB).

Contrato:
- app.schemas.auth.TokenSaida:       access_token, token_type (padrão "bearer")
- app.schemas.usuario.UsuarioCriar:  nome, matricula, email, telefone?, senha (SecretStr);
                                     sem campo `papel`
- app.schemas.usuario.UsuarioSaida:  codigo, matricula, nome, email, telefone, papel, ativo
- app.schemas.usuario.UsuarioAtualizar: campos cadastrais opcionais, sem `papel` e sem `senha`
- app.schemas.usuario.PapelAlterar:  papel in {"LEITOR", "BIBLIOTECARIO"}
"""

import pytest
from pydantic import ValidationError

from app.models import Pessoa
from tests.auth.conftest import SENHA


def _entrada(**kw) -> dict:
    base = dict(
        nome="Ana Souza", matricula="2026001", email="ana@escola.edu",
        telefone="48999990000", senha=SENHA,
    )  # fmt: skip
    return {**base, **kw}


# --- UsuarioCriar (entrada do cadastro) ------------------------------------------------------


def test_usuario_criar_valido():
    from app.schemas.usuario import UsuarioCriar

    dados = UsuarioCriar(**_entrada())

    assert dados.email == "ana@escola.edu"
    assert dados.senha.get_secret_value() == SENHA


def test_usuario_criar_nao_deixa_o_cliente_escolher_o_papel():
    from app.schemas.usuario import UsuarioCriar

    assert "papel" not in UsuarioCriar.model_fields
    assert not hasattr(UsuarioCriar(**_entrada(papel="BIBLIOTECARIO")), "papel")


def test_usuario_criar_nao_expoe_a_senha_em_repr_nem_em_dump_json():
    from app.schemas.usuario import UsuarioCriar

    dados = UsuarioCriar(**_entrada())

    assert SENHA not in repr(dados)
    assert SENHA not in str(dados)
    assert SENHA not in dados.model_dump_json()


def test_usuario_criar_telefone_e_opcional():
    from app.schemas.usuario import UsuarioCriar

    dados = _entrada()
    del dados["telefone"]
    assert UsuarioCriar(**dados).telefone is None


@pytest.mark.parametrize("campo", ["nome", "matricula", "email", "senha"])
@pytest.mark.parametrize("valor", [None, ""], ids=["ausente", "vazio"])
def test_usuario_criar_campos_obrigatorios(campo, valor):
    from app.schemas.usuario import UsuarioCriar

    dados = _entrada()
    if valor is None:
        del dados[campo]
    else:
        dados[campo] = valor

    with pytest.raises(ValidationError):
        UsuarioCriar(**dados)


@pytest.mark.parametrize("email", ["ana", "ana@", "@escola.edu", "ana escola.edu"])
def test_usuario_criar_email_invalido(email):
    from app.schemas.usuario import UsuarioCriar

    with pytest.raises(ValidationError):
        UsuarioCriar(**_entrada(email=email))


# --- UsuarioSaida (resposta) -----------------------------------------------------------------


def test_usuario_saida_nunca_tem_senha_nem_hash():
    from app.schemas.usuario import UsuarioSaida

    assert not {"senha", "senha_hash"} & set(UsuarioSaida.model_fields)


def test_usuario_saida_a_partir_do_model_nao_vaza_o_hash():
    from app.schemas.usuario import UsuarioSaida

    pessoa = Pessoa(
        id=1, codigo="cus_00000001", matricula="2026001", nome="Ana", email="ana@escola.edu",
        telefone=None, senha_hash="$argon2id$v=19$segredo", papel="LEITOR", ativo=True,
    )  # fmt: skip

    saida = UsuarioSaida.model_validate(pessoa, from_attributes=True)

    assert saida.model_dump() == {
        "codigo": "cus_00000001", "matricula": "2026001", "nome": "Ana",
        "email": "ana@escola.edu", "telefone": None, "papel": "LEITOR", "ativo": True,
    }  # fmt: skip
    assert "argon2" not in saida.model_dump_json()


# --- UsuarioAtualizar / PapelAlterar ---------------------------------------------------------


def test_usuario_atualizar_nao_aceita_papel_nem_senha():
    from app.schemas.usuario import UsuarioAtualizar

    assert not {"papel", "senha", "senha_hash", "ativo"} & set(UsuarioAtualizar.model_fields)


@pytest.mark.parametrize("papel", ["LEITOR", "BIBLIOTECARIO"])
def test_papel_alterar_aceita_os_dois_papeis(papel):
    from app.schemas.usuario import PapelAlterar

    assert PapelAlterar(papel=papel).papel == papel


@pytest.mark.parametrize("papel", ["ADMIN", "leitor", "", None])
def test_papel_alterar_recusa_papel_desconhecido(papel):
    from app.schemas.usuario import PapelAlterar

    with pytest.raises(ValidationError):
        PapelAlterar(papel=papel)


# --- TokenSaida ------------------------------------------------------------------------------


def test_token_saida_e_bearer_por_padrao():
    from app.schemas.auth import TokenSaida

    saida = TokenSaida(access_token="abc.def.ghi")

    assert saida.model_dump() == {"access_token": "abc.def.ghi", "token_type": "bearer"}
