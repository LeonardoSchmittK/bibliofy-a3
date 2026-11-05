"""Camada "Controller": rotas /auth (login, usuário atual e logout).

Testes que devem passar: tests/auth/test_rotas_auth.py.
"""

# TODO(#35) Passo a passo da implementação:
#   1. `router = APIRouter(prefix="/auth", tags=["auth"])`.
#   2. `POST /login` (`response_model=TokenSaida`):
#        - receber `form: OAuth2PasswordRequestForm = Depends()` (`username` = e-mail);
#        - `pessoa = auth_service.autenticar(db, form.username, form.password)`;
#        - `None` -> HTTP 401, mensagem genérica ("Credenciais inválidas"), igual para senha
#          errada, e-mail inexistente e conta inativa, com `WWW-Authenticate: Bearer`;
#        - sucesso -> `TokenSaida(access_token=auth_service.emitir_token(pessoa))`;
#        - não logar senha nem token.
#   3. `GET /me` (`response_model=UsuarioSaida`): `Depends(usuario_autenticado)`; devolve o
#      usuário do TOKEN (ignora qualquer id/código vindo do cliente).
#   4. `POST /logout` (`status_code=204`): exige `usuario_autenticado` e não faz nada no
#      servidor. Sem refresh token nem tabela de sessões (SEC03): o front descarta o token em
#      memória e uma cópia continua válida até expirar. Registrar essa decisão num comentário.
#   5. Registrar o router em `app/main.py` (`app.include_router(auth.router)`).
#   6. Rodar `pytest tests/auth/test_rotas_auth.py`.
