"""Regras de cadastro, consulta e papéis dos usuários (SEC01, SEC04).

Testes que devem passar: tests/auth/test_rotas_usuarios.py.
"""
from operator import or_

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security import hash_senha
from app.models import Pessoa
from app.schemas.usuario import UsuarioAtualizar, UsuarioCriar
from app.services import auditoria

# TODO(#35) Passo a passo da implementação:
#   1. `criar_usuario(db, dados: UsuarioCriar, operador: Pessoa) -> Pessoa`:
#        - papel SEMPRE "LEITOR" (definido aqui, no servidor) e `ativo=True`;
#        - `senha_hash = hash_senha(dados.senha.get_secret_value())`;
#        - e-mail ou matrícula repetidos (`IntegrityError`) viram erro de conflito -> 409
#          (fazer `db.rollback()` do savepoint ou checar antes);
#        - chamar `auditoria.registrar(CADASTRO / PESSOA)` e só então `db.commit()`;
#        - não devolver token nem alterar a sessão do operador.
#   2. `listar_usuarios(db, solicitante: Pessoa, nome=None, matricula=None, papel=None)`:
#        - se o solicitante for LEITOR, filtrar SEMPRE por `Pessoa.id == solicitante.id`,
#          qualquer que seja o filtro enviado (vale para listas e pesquisas);
#        - BIBLIOTECARIO vê todos e pode filtrar.
#   3. `obter_usuario(db, solicitante, codigo)`:
#        - LEITOR só acessa o próprio `codigo`; outro código -> `PermissionError` (403);
#        - BIBLIOTECARIO: se não existir -> não encontrado (404).
#   4. `atualizar_usuario(db, operador, codigo, dados: UsuarioAtualizar)`: edita só campos
#      cadastrais, nunca papel/senha; auditar ALTERACAO com antes/depois.
#   5. `alterar_papel(db, operador, codigo, papel)`: operação separada da edição cadastral;
#      404 se não existir; auditar ALTERACAO com dados={"papel": {"antes", "depois"}}.
#   6. Primeiro bibliotecário (SEC01): criado "na mão", fora da API. Criar um script
#      `backend/scripts/criar_bibliotecario.py` (pede nome, matrícula, e-mail e senha pelo terminal,
#      usa `hash_senha`) e documentar no README. Não há testes automatizados para ele.

_CAMPOS_CADASTRAIS = ("nome", "matricula", "email", "telefone")


class ConflitoError(Exception):
    """E-mail ou matrícula já cadastrados (-> 409)."""


class UsuarioNaoEncontradoError(Exception):
    """Usuário inexistente (-> 404)."""


def _dados_cadastrais(pessoa: Pessoa) -> dict:
    return {campo: getattr(pessoa, campo) for campo in _CAMPOS_CADASTRAIS}


def _existe_duplicado(
        db: Session, *, email: str | None, matricula: str | None, ignorar_id: int | None = None
) -> bool:
    condicoes = []
    if email is not None:
        condicoes.append(func.lower(Pessoa.email) == email.lower())
    if matricula is not None:
        condicoes.append(Pessoa.matricula == matricula)
    if not condicoes:
        return False
    consulta = select(Pessoa.id).where(or_(*condicoes))
    if ignorar_id is not None:
        consulta = consulta.where(Pessoa.id == ignorar_id)
    return db.scalars(consulta.limit(1)).first() is not None


def _buscar_por_codigo(db: Session, codigo: str) -> Pessoa:
    pessoa: Pessoa | None = db.scalars(select(Pessoa).where(Pessoa.codigo == codigo)).first()
    if pessoa is None:
        raise UsuarioNaoEncontradoError
    return pessoa


def criar_usuario(db: Session, dados: UsuarioCriar, operador: Pessoa) -> Pessoa:
    if _existe_duplicado(db, email=dados.email, matricula=dados.matricula):
        raise ConflitoError
    pessoa = Pessoa(
        nome=dados.nome,
        matricula=dados.matricula,
        email=dados.email,
        telefone=dados.telefone,
        senha_hash=hash_senha(dados.senha.get_secret_value()),
        papel="LEITOR",
        ativo=True,
    )
    try:
        with db.begin_nested():
            db.add(pessoa)
            db.flush()
    except IntegrityError:
        raise ConflitoError from None
    auditoria.registrar(
        db,
        responsavel=operador,
        acao="CADASTRO",
        entidade="PESSOA",
        entidade_id=pessoa.id,
        dados=_dados_cadastrais(pessoa),
    )
    db.commit()
    return pessoa

def listar_usuarios(
    db: Session,
    solicitante: Pessoa,
    nome: str | None = None,
    matricula: str | None = None,
    papel: str | None = None,
) -> list[Pessoa]:
    consulta = select(Pessoa).order_by(Pessoa.id)
    if solicitante.papel != "BIBLIOTECARIO":
        consulta = consulta.where(Pessoa.id == solicitante.id)
    if nome:
        consulta = consulta.where(Pessoa.nome.ilike(f"%{nome}%"))
    if matricula:
        consulta = consulta.where(Pessoa.matricula == matricula)
    if papel:
        consulta = consulta.where(Pessoa.papel == papel)
    return list(db.scalars(consulta).all())

def obter_usuario(db: Session, solicitante: Pessoa, codigo: str) -> Pessoa:
    if solicitante.papel != "BIBLIOTECARIO" and solicitante.codigo != codigo:
        raise PermissionError
    return _buscar_por_codigo(db, codigo)

def atualizar_usuario(
    db: Session,
    operador: Pessoa,
    codigo: str,
    dados: UsuarioAtualizar
) -> Pessoa:
    pessoa = _buscar_por_codigo(db, codigo)
    mudancas = dados.model_dump(exclude_unset=True)
    mudancas = {k: v for k, v in mudancas.items() if v is not None or k == "telefone"}
    mudancas = {k: v for k, v in mudancas.items() if getattr(pessoa, k) != v}
    if not mudancas:
        return pessoa

    if _existe_duplicado(
        db, email=mudancas.get("email"), matricula=mudancas.get("matricula"), ignorar_id=pessoa.id
    ):
        raise ConflitoError

    antes = {campo: getattr(pessoa, campo) for campo in mudancas}
    try:
        with db.begin_nested():
            for campo, valor in mudancas.items():
                setattr(pessoa, campo, valor)
            db.flush()
    except IntegrityError:
        raise ConflitoError from None
    auditoria.registrar(
        db,
        responsavel=operador,
        acao="ALTERACAO",
        entidade="PESSOA",
        entidade_id=pessoa.id,
        dados={"antes": antes, "depois": mudancas},
    )
    db.commit()
    return pessoa

def alterar_papel(db: Session, operador: Pessoa, codigo: str, papel: str) -> Pessoa:
    pessoa = _buscar_por_codigo(db, codigo)
    anterior = pessoa.papel
    pessoa.papel = papel
    db.flush()
    auditoria.registrar(
        db,
        responsavel=operador,
        acao="ALTERACAO",
        entidade="PESSOA",
        entidade_id=pessoa.id,
        dados={"papel": {"antes": anterior, "depois": papel}},
    )
    db.commit()
    return pessoa