"""Camada "Service": consulta do log de auditoria (RNF10). Só leitura.

Testes que devem passar: tests/auditoria/test_consulta_service.py e, para a escrita,
tests/auditoria/test_registrar.py (que exercita app/services/auditoria.py).
"""

# TODO(auditoria) Passo a passo da implementação:
#   0. Pré-requisito: `app/services/auditoria.py` nasce na issue #35 com `registrar`. Esta issue
#      o COMPLETA (o arquivo não existe nesta branch; integrar depois do merge da #35):
#        - constantes `ACOES` e `ENTIDADES` (tuplas) iguais aos CHECK de database/schema.sql;
#        - `class AuditoriaInvalidaError(ValueError)`;
#        - `sanitizar_dados(dados) -> dict | None`: cópia (sem mutar a entrada) sem as chaves
#          `senha`, `senha_hash` e `access_token` em qualquer nível (dicts e listas); valores
#          não JSON (date, datetime, Decimal) viram `str`; `None` continua `None`;
#        - `registrar(...)`: validar `acao` e `entidade` contra as constantes (senão
#          `AuditoriaInvalidaError`, sem gravar nada), usar `sanitizar_dados`, `db.add` +
#          `db.flush()`, NUNCA `db.commit()` (mesma transação da operação auditada).
#   1. `class RegistroNaoEncontradoError(Exception)`; a rota converte em 404.
#   2. `listar_auditoria(db, *, entidade=None, entidade_id=None, acao=None,
#      responsavel_codigo=None, de=None, ate=None, limite=50, deslocamento=0)
#      -> tuple[list[Auditoria], int]` (registros da página, total sem paginação):
#        - validar: `1 <= limite <= 200`, `deslocamento >= 0`, `de <= ate` (senão `ValueError`);
#        - filtros combinados com E; `responsavel_codigo` faz join com `Pessoa.codigo`;
#        - período: `criado_em >= de` e `criado_em < ate` (início inclusivo, fim exclusivo);
#        - ordem: `criado_em DESC, id DESC`; carregar o responsável junto
#          (`selectinload(Auditoria.responsavel)`) para evitar N+1;
#        - total: `select(func.count())` com os mesmos filtros.
#   3. `obter_registro(db, registro_id) -> Auditoria`: `RegistroNaoEncontradoError` se não existir.
#   4. Consultar NÃO gera registro de auditoria.
#   5. Rodar `pytest tests/auditoria`.
