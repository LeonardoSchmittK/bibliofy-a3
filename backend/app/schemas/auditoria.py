"""Camada "Model/View": schemas de saída da auditoria.

Testes que devem passar: tests/auditoria/test_schemas.py.
"""

# TODO(auditoria) Passo a passo da implementação:
#   1. `ResponsavelSaida(BaseModel)`: só `codigo` e `nome` (nunca e-mail, senha_hash ou id interno).
#   2. `AuditoriaSaida(BaseModel)` com `model_config = ConfigDict(from_attributes=True)`:
#      `id: int`, `acao: Literal[...]` e `entidade: Literal[...]` (valores de ACOES/ENTIDADES em
#      app/services/auditoria.py), `entidade_id: int`, `responsavel: ResponsavelSaida`,
#      `dados: dict | None`, `criado_em: datetime`. Não expor `responsavel_id`.
#   3. `PaginaAuditoria(BaseModel)`: `itens: list[AuditoriaSaida]`, `total`, `limite`,
#      `deslocamento` (inteiros).
#   4. Rodar `pytest tests/auditoria/test_schemas.py`.
