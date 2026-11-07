"""Camada "Service" do catálogo: regras de negócio de livros (RF01-RF04, RF14, RF18, RF19).

Testes que devem passar: tests/livros/test_livro_service.py.
"""

from typing import Any

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.isbn import normalizar_isbn
from app.models import Auditoria, Emprestimo, Livro, Pessoa
from app.schemas.livro import LivroAtualizar, LivroCriar, LivroSaida

STATUS_FORA_DA_ESTANTE = ("EMPRESTADO", "ATRASADO", "PERDIDO")
STATUS_ATIVOS = ("EMPRESTADO", "ATRASADO")

CAMPOS_AUDITADOS = (
    "isbn", "nome", "autor", "editora", "genero", "data_lancamento", "quantidade_total",
    "descricao",
)  # fmt: skip


class LivroNaoEncontradoError(Exception):
    pass

class LivroDuplicadoError(Exception):
    pass

class QuantidadeInsuficienteError(Exception):
    pass


def calcular_disponibilidade(
    quantidade_total: int, emprestados: int, arquivado: bool
) -> tuple[int, str]:
    disponiveis = max(quantidade_total - emprestados, 0)
    if arquivado or quantidade_total == 0:
        return disponiveis, "INDISPONIVEL"
    if disponiveis == 0:
        return disponiveis, "EMPRESTADO"
    return disponiveis, "DISPONIVEL"


# --- helpers ---------------------------------------------------------------------------------
def _contar(db: Session, livro_id: int, status: tuple[str, ...]) -> int:
    return db.scalar(
        select(func.count(Emprestimo.id)).where(
            Emprestimo.livro_id == livro_id, Emprestimo.status_atual.in_(status)
        )
    )


def _para_saida(db: Session, livro: Livro) -> LivroSaida:
    emprestados = _contar(db, livro.id, STATUS_FORA_DA_ESTANTE)
    disponiveis, status = calcular_disponibilidade(
        livro.quantidade_total, emprestados, livro.arquivado
    )
    return LivroSaida(
        codigo=livro.codigo,
        isbn=livro.isbn,
        nome=livro.nome,
        autor=livro.autor,
        editora=livro.editora,
        genero=livro.genero,
        data_lancamento=livro.data_lancamento,
        descricao=livro.descricao,
        quantidade_total=livro.quantidade_total,
        quantidade_disponivel=disponiveis,
        disponibilidade=status,
        arquivado=livro.arquivado,
    )


def _buscar(db: Session, codigo: str, *, incluir_arquivados: bool = True) -> Livro:
    livro = db.scalars(select(Livro).where(Livro.codigo == codigo)).one_or_none()
    if livro is None or (livro.arquivado and not incluir_arquivados):
        raise LivroNaoEncontradoError(codigo)
    return livro


def _isbn_em_uso(db: Session, isbn: str, ignorar_id: int | None = None) -> bool:
    consulta = select(Livro.id).where(Livro.isbn == isbn)
    if ignorar_id is not None:
        consulta = consulta.where(Livro.id != ignorar_id)
    return db.scalars(consulta).first() is not None


def _auditar(
    db: Session, responsavel: Pessoa, acao: str, livro: Livro, dados: dict[str, Any] | None = None
) -> None:
    # TODO(#35): trocar por `auditoria.registrar(...)` quando app/services/auditoria.py existir.
    db.add(
        Auditoria(
            responsavel_id=responsavel.id,
            acao=acao,
            entidade="LIVRO",
            entidade_id=livro.id,
            dados=dados,
        )
    )


def _json(valor: Any) -> Any:
    return valor.isoformat() if hasattr(valor, "isoformat") else valor


# --- operações -------------------------------------------------------------------------------
def criar_livro(db: Session, dados: LivroCriar, responsavel: Pessoa) -> LivroSaida:
    if _isbn_em_uso(db, dados.isbn):
        raise LivroDuplicadoError(dados.isbn)

    livro = Livro(**dados.model_dump())
    db.add(livro)
    try:
        db.flush()
    except IntegrityError as exc:
        db.rollback()
        raise LivroDuplicadoError(dados.isbn) from exc
    db.refresh(livro)  # traz o `codigo` gerado pelo banco

    _auditar(db, responsavel, "CADASTRO", livro)
    db.commit()
    return _para_saida(db, livro)


def listar_livros(
    db: Session,
    *,
    nome: str | None = None,
    autor: str | None = None,
    isbn: str | None = None,
    genero: str | None = None,
    codigo: str | None = None,
    incluir_arquivados: bool = False,
) -> list[LivroSaida]:
    consulta = select(Livro).order_by(Livro.nome, Livro.id)

    if nome:
        consulta = consulta.where(Livro.nome.ilike(f"%{nome}%"))
    if autor:
        consulta = consulta.where(Livro.autor.ilike(f"%{autor}%"))
    if genero:
        consulta = consulta.where(Livro.genero.ilike(f"%{genero}%"))
    if codigo:
        consulta = consulta.where(Livro.codigo == codigo)
    if isbn:
        try:
            consulta = consulta.where(Livro.isbn == normalizar_isbn(isbn))
        except ValueError:
            return []
    if not incluir_arquivados:
        consulta = consulta.where(Livro.arquivado.is_(False))

    return [_para_saida(db, livro) for livro in db.scalars(consulta)]


def obter_livro(db: Session, codigo: str, *, incluir_arquivados: bool = False) -> LivroSaida:
    return _para_saida(db, _buscar(db, codigo, incluir_arquivados=incluir_arquivados))


def atualizar_livro(
    db: Session, codigo: str, dados: LivroAtualizar, responsavel: Pessoa
) -> LivroSaida:
    livro = _buscar(db, codigo)
    mudancas = dados.model_dump(exclude_unset=True)

    if "isbn" in mudancas and _isbn_em_uso(db, mudancas["isbn"], ignorar_id=livro.id):
        raise LivroDuplicadoError(mudancas["isbn"])

    nova_qtd = mudancas.get("quantidade_total")
    if nova_qtd is not None and nova_qtd < _contar(db, livro.id, STATUS_ATIVOS):
        raise QuantidadeInsuficienteError(codigo)

    antes: dict[str, Any] = {}
    depois: dict[str, Any] = {}
    for campo, valor in mudancas.items():
        if campo not in CAMPOS_AUDITADOS:
            continue
        atual = getattr(livro, campo)
        if atual != valor:
            antes[campo] = _json(atual)
            depois[campo] = _json(valor)
            setattr(livro, campo, valor)

    if depois:
        _auditar(db, responsavel, "ALTERACAO", livro, {"antes": antes, "depois": depois})
    db.commit()
    return _para_saida(db, livro)


def contar_emprestimos_ativos(db: Session, codigo: str) -> int:
    livro = _buscar(db, codigo)
    return _contar(db, livro.id, STATUS_ATIVOS)


def arquivar_livro(db: Session, codigo: str, responsavel: Pessoa) -> LivroSaida:
    livro = _buscar(db, codigo)
    livro.arquivado = True
    _auditar(db, responsavel, "ARQUIVAMENTO", livro)
    db.commit()
    return _para_saida(db, livro)
