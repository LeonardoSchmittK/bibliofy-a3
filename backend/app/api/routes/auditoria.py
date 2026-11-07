"""Camada "Controller": rotas /auditoria (somente leitura, só Bibliotecário).

Testes que devem passar: tests/auditoria/test_rotas_auditoria.py.
Depende da issue #35: dependência `exige_bibliotecario` em app/api/deps.py.
"""

# TODO(auditoria) Passo a passo da implementação:
#   1. `router = APIRouter(prefix="/auditoria", tags=["auditoria"],
#      dependencies=[Depends(exige_bibliotecario)])` (401 sem login, 403 para o Leitor).
#   2. `GET /` (`response_model=PaginaAuditoria`): query params opcionais `entidade` e `acao`
#      (tipos `Literal`, valor fora do domínio -> 422), `entidade_id: int`, `responsavel: str`
#      (código da pessoa), `de` / `ate: datetime`, `limite: int = Query(50, ge=1, le=200)`,
#      `deslocamento: int = Query(0, ge=0)`. `de > ate` -> 422 (`ValueError` do serviço vira
#      `HTTPException(422)`). Chama `auditoria_consulta.listar_auditoria` e monta
#      `PaginaAuditoria(itens=..., total=..., limite=..., deslocamento=...)`.
#   3. `GET /{registro_id}` (`AuditoriaSaida`): `RegistroNaoEncontradoError` -> 404.
#   4. NÃO criar POST/PUT/PATCH/DELETE: o log é imutável, e a ausência devolve 405 sozinha.
#   5. Registrar o router em app/main.py (`app.include_router(auditoria.router)`).
