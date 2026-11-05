"""Camada "Service" do catálogo: regras de negócio de livros (RF01-RF04, RF14, RF18, RF19).

Testes que devem passar: tests/livros/test_livro_service.py.
"""

# TODO(#36) Passo a passo da implementação:
#   1. Exceções do módulo: `LivroNaoEncontradoError`, `LivroDuplicadoError` (ISBN repetido) e
#      `QuantidadeInsuficienteError`. A rota as converte em 404, 409 e 409.
#   2. `calcular_disponibilidade(quantidade_total, emprestados, arquivado)`
#      -> `(disponiveis, status)`, função pura (RF14):
#        - `disponiveis = quantidade_total - emprestados` (no mínimo 0 na exibição);
#        - arquivado OU `quantidade_total == 0` -> "INDISPONIVEL";
#        - `disponiveis == 0` -> "EMPRESTADO"; senão -> "DISPONIVEL".
#   3. "Emprestados" = empréstimos com status EMPRESTADO, ATRASADO ou PERDIDO (o exemplar
#      perdido não volta). É exatamente o que a view `vw_livro_disponibilidade` já calcula
#      (`quantidade_disponivel`): reaproveitar a view (`select(text(...))`/tabela mapeada) ou
#      repetir a contagem com `func.count` + `outerjoin`, e usar `calcular_disponibilidade`.
#   4. `criar_livro(db, dados: LivroCriar, responsavel: Pessoa) -> LivroSaida`:
#        - `Livro(**dados.model_dump())` (o ISBN já vem normalizado do schema);
#        - ISBN repetido (`IntegrityError` em `uq_livro_isbn`, ou checagem prévia) ->
#          `LivroDuplicadoError`;
#        - `auditoria.registrar(CADASTRO / LIVRO)` (app/services/auditoria.py, ver issue #35) e
#          `db.commit()` na mesma transação.
#   5. `listar_livros(db, *, nome, autor, isbn, genero, codigo, incluir_arquivados=False)`:
#        - `nome`, `autor`, `genero`: `ilike(f"%{valor}%")` (parcial, sem diferenciar caixa);
#        - `isbn`: `normalizar_isbn(valor)` e igualdade (se o texto não for ISBN válido, devolver
#          lista vazia em vez de erro); `codigo`: igualdade (filtro estilo Stripe, RF18);
#        - sem `incluir_arquivados`, filtrar `arquivado = FALSE` (RF19: sai do catálogo).
#   6. `obter_livro(db, codigo, *, incluir_arquivados=False) -> LivroSaida`: não encontrado (ou
#      arquivado sem `incluir_arquivados`) -> `LivroNaoEncontradoError`.
#   7. `atualizar_livro(db, codigo, dados: LivroAtualizar, responsavel) -> LivroSaida`:
#        - aplica só `dados.model_dump(exclude_unset=True)`;
#        - ISBN de OUTRO livro -> `LivroDuplicadoError` (manter o próprio ISBN é permitido);
#        - `quantidade_total` menor que os empréstimos ativos -> `QuantidadeInsuficienteError`
#          (regra proposta: o time confirma antes de manter);
#        - auditar ALTERACAO com `dados={"antes": {...}, "depois": {...}}` só dos campos mudados;
#        - NÃO mexer em empréstimos: eles referenciam o livro por `livro_id`, então o histórico
#          reflete os novos dados sozinho.
#   8. `contar_emprestimos_ativos(db, codigo) -> int`: só EMPRESTADO e ATRASADO (PERDIDO e
#      devolvidos não contam), para o aviso do RF19.
#   9. `arquivar_livro(db, codigo, responsavel) -> LivroSaida`: `arquivado = True`, sem apagar
#      nada e sem tocar nos empréstimos em andamento (RF04/RF19); auditar ARQUIVAMENTO.
#  10. Rodar `pytest tests/livros/test_livro_service.py`.
