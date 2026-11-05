"""Camada "View" da autenticação: schemas de entrada/saída do login.

Testes que devem passar: tests/auth/test_schemas.py (TokenSaida).
"""

# TODO(#35) Passo a passo da implementação:
#   1. Criar `class TokenSaida(BaseModel)` com `access_token: str` e `token_type: str = "bearer"`.
#   2. Usá-la como `response_model` do `POST /auth/login` (app/api/routes/auth.py).
#   3. O login recebe formulário OAuth2 (`OAuth2PasswordRequestForm`), por isso não há schema de
#      entrada: `username` = e-mail e `password` = senha.
#   4. Rodar `pytest tests/auth/test_schemas.py -k token`.
