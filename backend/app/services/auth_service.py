"""Regras do login (SEC03): quem pode entrar e como o token é emitido.

Testes que devem passar: tests/auth/test_rotas_auth.py (login).
"""

# TODO(#35) Passo a passo da implementação:
#   1. `autenticar(db: Session, email: str, senha: str) -> Pessoa | None`:
#        a. buscar a pessoa por e-mail sem diferenciar maiúsculas
#           (`func.lower(Pessoa.email) == email.lower()`, casa com o índice uq_pessoa_email);
#        b. se não existir, chamar `verificar_senha(senha, _HASH_FALSO)` mesmo assim, para o
#           tempo de resposta não revelar se a conta existe (`_HASH_FALSO = hash_senha(...)`
#           calculado uma vez no módulo);
#        c. se existir: conferir `verificar_senha(senha, pessoa.senha_hash)` e `pessoa.ativo`;
#        d. devolver a `Pessoa` só se tudo passar; em qualquer falha devolver `None`
#           (o controller transforma em 401 genérico, sem dizer o motivo).
#   2. `emitir_token(pessoa: Pessoa) -> str`: delega para `core.security.criar_token_acesso`.
#   3. Penalidade por atraso NÃO impede login nem consulta (só impede novos empréstimos):
#      não consultar a tabela `bloqueio` aqui.
#   4. Não registrar senha, hash nem token em log (nem em DEBUG).
#   5. Rodar `pytest tests/auth/test_rotas_auth.py -k login`.
