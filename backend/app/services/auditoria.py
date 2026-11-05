"""Registro básico de auditoria (RNF10 / SEC05), gravado na mesma transação da operação.

Testes que devem passar: as verificações de `Auditoria` em tests/auth/test_rotas_usuarios.py.
"""

# TODO(#35) Passo a passo da implementação:
#   1. `registrar(db, *, responsavel, acao, entidade, entidade_id, dados=None) -> Auditoria`:
#      cria `Auditoria(responsavel_id=responsavel.id, ...)`, faz `db.add(...)` e `db.flush()`.
#      NÃO fazer commit aqui: o registro precisa entrar na mesma transação da operação auditada.
#   2. Valores aceitos pelo banco (CHECK em database/schema.sql): ações CADASTRO, ALTERACAO,
#      ARQUIVAMENTO, EMPRESTIMO, RENOVACAO, DEVOLUCAO, PERDA, BLOQUEIO; entidades PESSOA, LIVRO,
#      EMPRESTIMO, BLOQUEIO.
#   3. Sanitizar `dados` antes de gravar: remover (em qualquer nível) as chaves `senha`,
#      `senha_hash` e `access_token`. Nunca guardar senha, hash ou token na auditoria.
#   4. Cadastro de usuário: acao="CADASTRO", entidade="PESSOA", dados com os campos cadastrais.
#      Mudança de papel: acao="ALTERACAO", entidade="PESSOA", dados={"papel": {"antes", "depois"}}.
