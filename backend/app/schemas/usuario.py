"""Camada "View": schemas de usuário (Pessoa). A senha e o hash nunca saem pela API.

Testes que devem passar: tests/auth/test_schemas.py.
Requisitos: SEC01 (papel nunca vem do cliente), SEC02 (sem senha/hash em respostas e logs).
"""

# TODO(#35) Passo a passo da implementação:
#   1. Dependência de e-mail: `EmailStr` exige o pacote `email-validator`. Adicionar em
#      pyproject.toml (`uv add email-validator`) ou, se preferirem evitar a dependência, validar o
#      e-mail com `Field(pattern=...)`. Os testes recusam "ana", "ana@", "@escola.edu".
#   2. `UsuarioCriar(BaseModel)`: `nome`, `matricula` e `email` (strings não vazias,
#      `Field(min_length=1)`), `telefone: str | None = None` e `senha: SecretStr` (não vazia).
#      Sem campo `papel` (campos extras são ignorados, que é o padrão do Pydantic):
#      o cliente nunca escolhe o papel. `SecretStr` impede a senha de aparecer em repr/logs.
#   3. `UsuarioSaida(BaseModel)`: `model_config = ConfigDict(from_attributes=True)` e os campos
#      `codigo`, `matricula`, `nome`, `email`, `telefone`, `papel`, `ativo`.
#      NUNCA incluir `senha` nem `senha_hash`.
#   4. `UsuarioAtualizar(BaseModel)`: `nome`, `matricula`, `email`, `telefone`, todos opcionais.
#      Sem `papel`, `senha` nem `ativo` (papel muda só em `PapelAlterar`).
#   5. `PapelAlterar(BaseModel)`: `papel: Literal["LEITOR", "BIBLIOTECARIO"]`.
#   6. Rodar `pytest tests/auth/test_schemas.py`.
