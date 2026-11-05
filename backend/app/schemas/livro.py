"""Camada "View" do catálogo: schemas Pydantic de entrada e saída de livros.

Testes que devem passar: tests/livros/test_schemas.py.
"""

# TODO(#36) Passo a passo da implementação:
#   1. Tipo auxiliar `Isbn = Annotated[str, AfterValidator(normalizar_isbn)]` (app/core/isbn.py):
#      valida o formato e já entrega o ISBN só com dígitos. Como `normalizar_isbn` levanta
#      `ValueError`, o Pydantic o converte em erro de validação (422 na rota).
#   2. `Texto = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]`
#      para `nome`, `autor`, `editora` e `genero` (não aceitam vazio nem só espaços).
#   3. `LivroCriar(BaseModel)`: `isbn: Isbn`, `nome`, `autor`, `editora`, `genero: Texto`,
#      `data_lancamento: date`, `quantidade_total: int = Field(ge=0)` (inteiro estrito:
#      `strict=True` recusa 1.5 e "muitos"), `descricao: str | None = None`.
#      Sem `codigo` nem `arquivado` (campos extras são ignorados, que é o padrão do Pydantic).
#   4. `LivroAtualizar(BaseModel)`: os mesmos campos, todos opcionais (`= None`), com as mesmas
#      validações quando informados. Sem `codigo`, `arquivado` nem `quantidade_disponivel`.
#      A rota usa `dados.model_dump(exclude_unset=True)` para aplicar só o que foi enviado.
#   5. `Disponibilidade = Literal["DISPONIVEL", "EMPRESTADO", "INDISPONIVEL"]`.
#   6. `LivroSaida(BaseModel)` com `model_config = ConfigDict(from_attributes=True)` e os campos
#      `codigo`, `isbn`, `nome`, `autor`, `editora`, `genero`, `data_lancamento`, `descricao`,
#      `quantidade_total`, `quantidade_disponivel`, `disponibilidade: Disponibilidade`, `arquivado`.
#   7. `PreviaArquivamento(BaseModel)` com `emprestimos_ativos: int` (RF19).
#   8. Rodar `pytest tests/livros/test_schemas.py`.
