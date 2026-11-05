"""Camada "Controller": rotas /livros (CRUD pelo Bibliotecário; Leitor só consulta).

Testes que devem passar: tests/livros/test_rotas_livros.py.
Depende da issue #35 (autenticação): dependências `usuario_autenticado` e `exige_bibliotecario`
em app/api/deps.py e o serviço de auditoria em app/services/auditoria.py.
"""

# TODO(#36) Passo a passo da implementação:
#   1. `router = APIRouter(prefix="/livros", tags=["livros"])`.
#   2. `POST /` (201, `response_model=LivroSaida`): `Depends(exige_bibliotecario)`; corpo
#      `LivroCriar`; chama `livro_service.criar_livro`. `LivroDuplicadoError` -> 409 com
#      `{"motivo": "ISBN_DUPLICADO"}`.
#   3. `GET /` (`list[LivroSaida]`): `Depends(usuario_autenticado)`; query params opcionais
#      `nome`, `autor`, `isbn`, `genero`, `codigo` e `arquivados: bool = False`.
#      `arquivados=true` só vale para BIBLIOTECARIO; para o LEITOR é ignorado (RF19: arquivado
#      nunca aparece no catálogo do leitor).
#   4. `GET /{codigo}` (`LivroSaida`): `Depends(usuario_autenticado)`; `LivroNaoEncontradoError`
#      -> 404. Para o LEITOR, livro arquivado também é 404; o BIBLIOTECARIO enxerga arquivado.
#   5. `PATCH /{codigo}`: `Depends(exige_bibliotecario)`; corpo `LivroAtualizar`;
#      404 se não existir; `LivroDuplicadoError` -> 409 `ISBN_DUPLICADO`;
#      `QuantidadeInsuficienteError` -> 409 `{"motivo": "QUANTIDADE_INSUFICIENTE"}`.
#   6. `POST /{codigo}/arquivar` (200, `LivroSaida`): `Depends(exige_bibliotecario)`; 404 se não
#      existir. Não apaga nada (RF04) e não altera empréstimos em andamento (RF19).
#   7. `GET /{codigo}/previa-arquivamento` (`PreviaArquivamento`): `Depends(exige_bibliotecario)`;
#      devolve `{"emprestimos_ativos": n}` para o aviso antes de confirmar o arquivamento;
#      não altera nada; 404 se não existir.
#   8. Ordem das rotas: declarar as rotas fixas (`/{codigo}/arquivar`, `/{codigo}/previa-...`)
#      sem conflito com `/{codigo}`; o FastAPI diferencia pelo método e pelo caminho completo.
#   9. Registrar o router em `app/main.py`: `app.include_router(livros.router)`.
#  10. Rodar `pytest tests/livros/test_rotas_livros.py`.
