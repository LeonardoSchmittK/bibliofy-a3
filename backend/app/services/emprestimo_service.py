"""Regras de negócio de empréstimos, devoluções, renovações e bloqueios."""

from datetime import date, timedelta

from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import Bloqueio, Emprestimo, Livro, Pessoa
from app.schemas.emprestimo import EmprestimoCriar, EmprestimoSaida, StatusEmprestimo
from app.services.auditoria import registrar

DIAS_PRAZO_EMPRESTIMO = 25
DIAS_BLOQUEIO_ATRASO = 10
STATUS_ATIVOS = ("EMPRESTADO", "ATRASADO")
STATUS_FORA_DA_ESTANTE = (*STATUS_ATIVOS, "PERDIDO")


class EmprestimoNaoEncontradoError(Exception):
    pass


class PessoaNaoEncontradaError(Exception):
    pass


class LivroNaoEncontradoError(Exception):
    pass


class RegraEmprestimoError(Exception):
    pass


def _buscar_pessoa(db: Session, codigo: str, *, bloquear: bool = False) -> Pessoa:
    consulta = select(Pessoa).where(Pessoa.codigo == codigo)
    if bloquear:
        consulta = consulta.with_for_update()
    pessoa = db.scalars(consulta).one_or_none()
    if pessoa is None:
        raise PessoaNaoEncontradaError(codigo)
    return pessoa


def _buscar_livro(db: Session, codigo: str, *, bloquear: bool = False) -> Livro:
    consulta = select(Livro).where(Livro.codigo == codigo)
    if bloquear:
        consulta = consulta.with_for_update()
    livro = db.scalars(consulta).one_or_none()
    if livro is None:
        raise LivroNaoEncontradoError(codigo)
    return livro


def _buscar_emprestimo(db: Session, codigo: str, *, bloquear: bool = False) -> Emprestimo:
    consulta = select(Emprestimo).where(Emprestimo.codigo == codigo)
    if bloquear:
        consulta = consulta.with_for_update()
    emprestimo = db.scalars(consulta).one_or_none()
    if emprestimo is None:
        raise EmprestimoNaoEncontradoError(codigo)
    return emprestimo


def _quantidade_fora_da_estante(db: Session, livro_id: int) -> int:
    return db.scalar(
        select(func.count(Emprestimo.id)).where(
            Emprestimo.livro_id == livro_id,
            Emprestimo.status_atual.in_(STATUS_FORA_DA_ESTANTE),
        )
    ) or 0


def _bloqueio_ativo(db: Session, pessoa_id: int, hoje: date) -> Bloqueio | None:
    return db.scalars(
        select(Bloqueio)
        .where(
            Bloqueio.pessoa_id == pessoa_id,
            Bloqueio.inicio <= hoje,
            Bloqueio.fim_exclusivo > hoje,
        )
        .order_by(Bloqueio.fim_exclusivo.desc())
        .limit(1)
    ).first()


def _campos_bloqueio_por_emprestimo(
    db: Session, emprestimo_ids: set[int], hoje: date
) -> dict[int, tuple[date, date]]:
    if not emprestimo_ids:
        return {}
    bloqueios = db.scalars(
        select(Bloqueio).where(
            Bloqueio.emprestimo_id.in_(emprestimo_ids),
            Bloqueio.inicio <= hoje,
            Bloqueio.fim_exclusivo > hoje,
        )
    ).all()
    campos: dict[int, tuple[date, date]] = {}
    for bloqueio in bloqueios:
        campos[bloqueio.emprestimo_id] = (bloqueio.inicio, bloqueio.fim_exclusivo)
    return campos


def _status_atual(emprestimo: Emprestimo, hoje: date) -> StatusEmprestimo:
    # Sem cron configurado, a resposta calcula o atraso pelo vencimento no momento da consulta.
    if emprestimo.status_atual == "EMPRESTADO" and emprestimo.data_prevista < hoje:
        return "ATRASADO"
    return emprestimo.status_atual  # type: ignore[return-value]


def _para_saida(
    emprestimo: Emprestimo,
    pessoa: Pessoa,
    livro: Livro,
    hoje: date,
    bloqueios: dict[int, tuple[date, date]],
) -> EmprestimoSaida:
    inicio, fim = bloqueios.get(emprestimo.id, (None, None))
    return EmprestimoSaida(
        id=emprestimo.id,
        codigo=emprestimo.codigo,
        pessoa_codigo=pessoa.codigo,
        pessoa_nome=pessoa.nome,
        livro_codigo=livro.codigo,
        livro_nome=livro.nome,
        livro_isbn=livro.isbn,
        data_emprestimo=emprestimo.data_emprestimo,
        data_prevista=emprestimo.data_prevista,
        data_devolucao=emprestimo.data_devolucao,
        renovado=emprestimo.renovado,
        status_atual=_status_atual(emprestimo, hoje),
        bloqueio_inicio=inicio,
        bloqueio_fim_exclusivo=fim,
    )


def criar_emprestimo(
    db: Session, dados: EmprestimoCriar, responsavel: Pessoa, *, hoje: date | None = None
) -> EmprestimoSaida:
    hoje = hoje or date.today()
    pessoa = _buscar_pessoa(db, dados.pessoa_codigo, bloquear=True)
    if not pessoa.ativo:
        raise RegraEmprestimoError("O leitor está inativo")
    if pessoa.papel != "LEITOR":
        raise RegraEmprestimoError("Empréstimos só podem ser registrados para leitores")

    bloqueio = _bloqueio_ativo(db, pessoa.id, hoje)
    if bloqueio:
        ultimo_dia = bloqueio.fim_exclusivo - timedelta(days=1)
        raise RegraEmprestimoError(f"Leitor impedido de emprestar até {ultimo_dia.isoformat()}")

    emprestimo_ativo = db.scalars(
        select(Emprestimo.id).where(
            Emprestimo.pessoa_id == pessoa.id,
            Emprestimo.status_atual.in_(STATUS_ATIVOS),
        )
    ).first()
    if emprestimo_ativo:
        raise RegraEmprestimoError("O leitor já possui um empréstimo em andamento")

    livro = _buscar_livro(db, dados.livro_codigo, bloquear=True)
    if livro.arquivado:
        raise RegraEmprestimoError("Livro arquivado não pode ser emprestado")
    if _quantidade_fora_da_estante(db, livro.id) >= livro.quantidade_total:
        raise RegraEmprestimoError("Não há exemplares disponíveis deste livro")

    emprestimo = Emprestimo(
        pessoa_id=pessoa.id,
        livro_id=livro.id,
        data_emprestimo=hoje,
        data_prevista=hoje + timedelta(days=DIAS_PRAZO_EMPRESTIMO),
    )
    try:
        with db.begin_nested():
            db.add(emprestimo)
            db.flush()
    except IntegrityError as exc:
        raise RegraEmprestimoError("O empréstimo conflitou com outra operação") from exc

    registrar(
        db,
        responsavel=responsavel,
        acao="EMPRESTIMO",
        entidade="EMPRESTIMO",
        entidade_id=emprestimo.id,
        dados={
            "pessoa_codigo": pessoa.codigo,
            "livro_codigo": livro.codigo,
            "data_prevista": emprestimo.data_prevista,
        },
    )
    db.commit()
    db.refresh(emprestimo)
    return _para_saida(emprestimo, pessoa, livro, hoje, {})


def _consultar_linhas(db: Session, codigo: str | None = None):
    consulta = (
        select(Emprestimo, Pessoa, Livro)
        .join(Pessoa, Pessoa.id == Emprestimo.pessoa_id)
        .join(Livro, Livro.id == Emprestimo.livro_id)
    )
    if codigo is not None:
        consulta = consulta.where(Emprestimo.codigo == codigo)
    return db.execute(consulta)


def listar_emprestimos(
    db: Session,
    *,
    solicitante: Pessoa,
    status_atual: str | None = None,
    busca: str | None = None,
    data_inicio: date | None = None,
    data_fim: date | None = None,
    hoje: date | None = None,
) -> list[EmprestimoSaida]:
    hoje = hoje or date.today()
    consulta = (
        select(Emprestimo, Pessoa, Livro)
        .join(Pessoa, Pessoa.id == Emprestimo.pessoa_id)
        .join(Livro, Livro.id == Emprestimo.livro_id)
        .order_by(Emprestimo.data_emprestimo.desc(), Emprestimo.id.desc())
    )
    if solicitante.papel != "BIBLIOTECARIO":
        consulta = consulta.where(Emprestimo.pessoa_id == solicitante.id)
    if status_atual == "ATRASADO":
        consulta = consulta.where(
            or_(
                Emprestimo.status_atual == "ATRASADO",
                (Emprestimo.status_atual == "EMPRESTADO") & (Emprestimo.data_prevista < hoje),
            )
        )
    elif status_atual == "EMPRESTADO":
        consulta = consulta.where(
            Emprestimo.status_atual == "EMPRESTADO", Emprestimo.data_prevista >= hoje
        )
    elif status_atual:
        consulta = consulta.where(Emprestimo.status_atual == status_atual)
    if data_inicio:
        consulta = consulta.where(Emprestimo.data_emprestimo >= data_inicio)
    if data_fim:
        consulta = consulta.where(Emprestimo.data_emprestimo <= data_fim)
    if busca:
        termo = f"%{busca.strip()}%"
        consulta = consulta.where(
            or_(
                Emprestimo.codigo.ilike(termo),
                Pessoa.nome.ilike(termo),
                Pessoa.codigo.ilike(termo),
                Livro.nome.ilike(termo),
                Livro.codigo.ilike(termo),
                Livro.isbn.ilike(termo),
            )
        )

    linhas = list(db.execute(consulta))
    bloqueios = _campos_bloqueio_por_emprestimo(
        db, {emprestimo.id for emprestimo, _, _ in linhas}, hoje
    )
    return [
        _para_saida(emprestimo, pessoa, livro, hoje, bloqueios)
        for emprestimo, pessoa, livro in linhas
    ]


def obter_emprestimo(
    db: Session, codigo: str, solicitante: Pessoa, *, hoje: date | None = None
) -> EmprestimoSaida:
    hoje = hoje or date.today()
    linha = _consultar_linhas(db, codigo).first()
    if linha is None:
        raise EmprestimoNaoEncontradoError(codigo)
    emprestimo, pessoa, livro = linha
    if solicitante.papel != "BIBLIOTECARIO" and solicitante.id != pessoa.id:
        raise PermissionError
    bloqueios = _campos_bloqueio_por_emprestimo(db, {emprestimo.id}, hoje)
    return _para_saida(emprestimo, pessoa, livro, hoje, bloqueios)


def devolver_emprestimo(
    db: Session, codigo: str, responsavel: Pessoa, *, hoje: date | None = None
) -> EmprestimoSaida:
    hoje = hoje or date.today()
    emprestimo = _buscar_emprestimo(db, codigo, bloquear=True)
    if emprestimo.status_atual not in STATUS_ATIVOS:
        raise RegraEmprestimoError("Este empréstimo já foi encerrado")
    pessoa = _buscar_pessoa_por_id(db, emprestimo.pessoa_id)
    livro = _buscar_livro_por_id(db, emprestimo.livro_id)

    atrasado = hoje > emprestimo.data_prevista
    emprestimo.data_devolucao = hoje
    emprestimo.status_atual = "DEVOLVIDO_COM_ATRASO" if atrasado else "DEVOLVIDO"
    dados_auditoria: dict[str, object] = {
        "pessoa_codigo": pessoa.codigo,
        "livro_codigo": livro.codigo,
        "data_devolucao": hoje,
        "atrasado": atrasado,
    }
    if atrasado:
        ultimo_fim = db.scalar(
            select(func.max(Bloqueio.fim_exclusivo)).where(
                Bloqueio.pessoa_id == pessoa.id,
                Bloqueio.fim_exclusivo > hoje,
            )
        )
        inicio = max(hoje, ultimo_fim) if ultimo_fim else hoje
        fim_exclusivo = inicio + timedelta(days=DIAS_BLOQUEIO_ATRASO)
        bloqueio = Bloqueio(
            pessoa_id=pessoa.id,
            emprestimo_id=emprestimo.id,
            inicio=inicio,
            fim_exclusivo=fim_exclusivo,
            motivo="Devolução após a data prevista",
        )
        db.add(bloqueio)
        db.flush()
        registrar(
            db,
            responsavel=responsavel,
            acao="BLOQUEIO",
            entidade="BLOQUEIO",
            entidade_id=bloqueio.id,
            dados={
                "emprestimo_codigo": emprestimo.codigo,
                "inicio": inicio,
                "fim_exclusivo": fim_exclusivo,
            },
        )
        dados_auditoria["bloqueio_fim_exclusivo"] = fim_exclusivo

    registrar(
        db,
        responsavel=responsavel,
        acao="DEVOLUCAO",
        entidade="EMPRESTIMO",
        entidade_id=emprestimo.id,
        dados=dados_auditoria,
    )
    db.commit()
    db.refresh(emprestimo)
    bloqueios = _campos_bloqueio_por_emprestimo(db, {emprestimo.id}, hoje)
    return _para_saida(emprestimo, pessoa, livro, hoje, bloqueios)


def _buscar_pessoa_por_id(db: Session, pessoa_id: int) -> Pessoa:
    pessoa = db.get(Pessoa, pessoa_id)
    if pessoa is None:
        raise PessoaNaoEncontradaError(str(pessoa_id))
    return pessoa


def _buscar_livro_por_id(db: Session, livro_id: int) -> Livro:
    livro = db.get(Livro, livro_id)
    if livro is None:
        raise LivroNaoEncontradoError(str(livro_id))
    return livro


def renovar_emprestimo(
    db: Session,
    codigo: str,
    solicitante: Pessoa,
    *,
    hoje: date | None = None,
) -> EmprestimoSaida:
    hoje = hoje or date.today()
    emprestimo = _buscar_emprestimo(db, codigo, bloquear=True)
    pessoa = _buscar_pessoa_por_id(db, emprestimo.pessoa_id)
    if solicitante.papel != "BIBLIOTECARIO" and solicitante.id != pessoa.id:
        raise PermissionError
    if emprestimo.status_atual not in STATUS_ATIVOS:
        raise RegraEmprestimoError("Empréstimo encerrado não pode ser renovado")
    if emprestimo.renovado:
        raise RegraEmprestimoError("Este empréstimo já foi renovado")
    if emprestimo.data_prevista < hoje:
        raise RegraEmprestimoError("Empréstimo atrasado não pode ser renovado")

    data_anterior = emprestimo.data_prevista
    emprestimo.data_prevista += timedelta(days=DIAS_PRAZO_EMPRESTIMO)
    emprestimo.renovado = True
    registrar(
        db,
        responsavel=solicitante,
        acao="RENOVACAO",
        entidade="EMPRESTIMO",
        entidade_id=emprestimo.id,
        dados={
            "data_prevista_antes": data_anterior,
            "data_prevista_depois": emprestimo.data_prevista,
        },
    )
    db.commit()
    db.refresh(emprestimo)
    livro = _buscar_livro_por_id(db, emprestimo.livro_id)
    bloqueios = _campos_bloqueio_por_emprestimo(db, {emprestimo.id}, hoje)
    return _para_saida(emprestimo, pessoa, livro, hoje, bloqueios)
