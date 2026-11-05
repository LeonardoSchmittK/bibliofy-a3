"""Núcleo de segurança: hash de senha (Argon2id) e JWT.

Testes que devem passar: tests/auth/test_security.py (e tests/auth/test_config_jwt.py).
Requisitos: SEC02 (senhas) e SEC03 (autenticação e sessão), issue #13.
"""

# TODO(#35) Passo a passo da implementação:
#
#  Hash de senha (SEC02)
#   1. Importar `PasswordHash` de `pwdlib` e criar um hasher único do módulo:
#      `_hasher = PasswordHash.recommended()`  (Argon2id, configuração padrão da biblioteca,
#      salt gerado por ela; NÃO definir memória/iterações/paralelismo no braço).
#   2. `hash_senha(senha: str) -> str`: devolve `_hasher.hash(senha)`.
#   3. `verificar_senha(senha: str, senha_hash: str) -> bool`: devolve `_hasher.verify(...)`,
#      mas capturando as exceções do pwdlib (hash inválido/desconhecido) e retornando False.
#      Nunca levantar exceção para a rota, nunca logar a senha nem o hash.
#
#  JWT (SEC03)
#   4. Criar `class TokenInvalidoError(Exception)`, usada para qualquer token recusado.
#   5. `criar_token_acesso(pessoa: Pessoa) -> str`:
#        - payload SOMENTE com `sub` (= `pessoa.codigo`), `iat` (agora, UTC) e `exp`
#          (`iat` + `settings.jwt_expire_minutes`, no máximo 15 min). Sem e-mail, papel etc. (LGPD);
#        - assinar com `jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)`.
#   6. `decodificar_token(token: str) -> dict`:
#        - `jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm],
#          options={"require": ["sub", "exp", "iat"]})`;
#        - a lista de algoritmos é FIXA: nunca aceitar "none" nem outro algoritmo;
#        - capturar `jwt.PyJWTError` (expirado, assinatura inválida, malformado, claim ausente)
#          e relançar como `TokenInvalidoError`.
#   7. Ler as configurações via `get_settings()` (app/core/config.py, ver TODO lá).
#   8. Rodar `pytest tests/auth/test_security.py tests/auth/test_config_jwt.py`.
