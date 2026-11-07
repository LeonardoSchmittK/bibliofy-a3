"""Fixtures dos testes do catálogo de livros (issue #36; wiki RF01-RF04, RF14, RF18, RF19).

Depende do contrato de autenticação da issue #35 (token JWT HS256 com `sub` = `pessoa.codigo`,
chave em `get_settings().jwt_secret`, dependências `usuario_autenticado` / `exige_bibliotecario`).
Os tokens são gerados aqui com PyJWT, sem usar código de `app/`.

Contrato das rotas (ajustar aqui e nos TODOs de `app/` se o time decidir outro):

- `POST /livros`, `GET /livros`, `GET /livros/{codigo}`, `PATCH /livros/{codigo}`,
  `POST /livros/{codigo}/arquivar`, `GET /livros/{codigo}/previa-arquivamento`.
- Só o Bibliotecário escreve; o Leitor apenas consulta (GET) livros do catálogo.
- 401 sem autenticação válida, 403 sem permissão, 404 inexistente (ou arquivado, para o Leitor),
  409 para regra de negócio (`{"motivo": "..."}`), 422 para payload inválido.
"""

from datetime import UTC, date, datetime, timedelta
from itertools import count

import jwt
import pytest
import time_machine

from app.models import Emprestimo, Livro, Pessoa

AGORA = datetime(2026, 3, 10, 12, 0, tzinfo=UTC)
HOJE = AGORA.date()
_seq = count(1)


@pytest.fixture(autouse=True)
def _relogio_congelado():
    with time_machine.travel(AGORA, tick=False):
        yield


# --- dados -----------------------------------------------------------------------------------


def payload_livro(**kw) -> dict:
    return {
        "isbn": "978-3-16-148410-0", "nome": "Dom Casmurro", "autor": "Machado de Assis",
        "editora": "Garnier", "genero": "Romance", "data_lancamento": "1899-01-01",
        "quantidade_total": 3, "descricao": "Clássico da literatura brasileira",
        **kw,
    }  # fmt: skip


@pytest.fixture
def cria_usuario(db_session):
    def _cria(*, papel="LEITOR", ativo=True, **kw) -> Pessoa:
        n = next(_seq)
        campos = dict(
            matricula=f"mat{n}", nome=f"Usuario {n}", email=f"usuario{n}@escola.edu",
            senha_hash="hash-que-nao-e-usado-aqui", papel=papel, ativo=ativo,
        )  # fmt: skip
        pessoa = Pessoa(**{**campos, **kw})
        db_session.add(pessoa)
        db_session.flush()
        return pessoa

    return _cria


@pytest.fixture
def bibliotecario(cria_usuario):
    return cria_usuario(papel="BIBLIOTECARIO", nome="Bia Bibliotecária")


@pytest.fixture
def leitor(cria_usuario):
    return cria_usuario(nome="Lia Leitora")


@pytest.fixture
def cria_livro(db_session):
    def _cria(**kw) -> Livro:
        n = next(_seq)
        campos = dict(
            isbn=f"978{n:010d}", nome=f"Livro {n}", autor="Autor", editora="Editora",
            genero="Romance", data_lancamento=date(2020, 1, 1), quantidade_total=1,
        )  # fmt: skip
        livro = Livro(**{**campos, **kw})
        db_session.add(livro)
        db_session.flush()
        return livro

    return _cria


@pytest.fixture
def cria_emprestimo(db_session, cria_usuario):
    def _cria(livro: Livro, pessoa: Pessoa | None = None, **kw) -> Emprestimo:
        pessoa = pessoa or cria_usuario()
        campos = dict(
            pessoa_id=pessoa.id, livro_id=livro.id,
            data_emprestimo=HOJE, data_prevista=HOJE + timedelta(days=25),
        )  # fmt: skip
        emprestimo = Emprestimo(**{**campos, **kw})
        db_session.add(emprestimo)
        db_session.flush()
        return emprestimo

    return _cria


@pytest.fixture
def devolvido():
    """Argumentos para um empréstimo já devolvido."""
    return dict(status_atual="DEVOLVIDO", data_devolucao=HOJE)


# --- autenticação (contrato da issue #35) ----------------------------------------------------


@pytest.fixture
def cabecalho():
    def _cabecalho(pessoa: Pessoa) -> dict[str, str]:
        from app.core.config import get_settings

        token = jwt.encode(
            {"sub": pessoa.codigo, "iat": AGORA, "exp": AGORA + timedelta(minutes=15)},
            get_settings().jwt_secret,  # ainda não existe: fica vermelho
            algorithm="HS256",
        )
        return {"Authorization": f"Bearer {token}"}

    return _cabecalho


@pytest.fixture
def api(db_client, bibliotecario, cabecalho):
    """Cliente autenticado como bibliotecário. Para o leitor: `headers=cabecalho(leitor)`."""
    db_client.headers.update(cabecalho(bibliotecario))
    return db_client
