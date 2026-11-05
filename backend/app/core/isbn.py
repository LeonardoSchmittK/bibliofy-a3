"""Validação e normalização de ISBN (RF01 e RF02 da wiki citam a "regex de validação do ISBN").

Testes que devem passar: tests/livros/test_isbn.py.
"""

# TODO(#36) Passo a passo da implementação:
#   1. Definir as regex compiladas do módulo (sobre o texto já sem hífens/espaços):
#        - ISBN-10: `^\d{9}[\dX]$`  (o X só vale como último caractere);
#        - ISBN-13: `^97[89]\d{10}$` (prefixo 978 ou 979; sem X).
#   2. `normalizar_isbn(texto: str) -> str`:
#        - `strip()`, remover hífens e espaços (`re.sub(r"[\s-]", "", texto)`), `upper()`;
#        - se não casar com nenhuma das regex, levantar `ValueError("ISBN inválido")`;
#        - devolver só dígitos (e o `X` final do ISBN-10), que cabem em `livro.isbn` (VARCHAR(20)).
#   3. `isbn_valido(texto: str) -> bool`: chama `normalizar_isbn` e devolve False no `ValueError`.
#   4. Decisão do time: os testes validam só o FORMATO, como a wiki pede (regex). Se quiserem
#      conferir também o dígito verificador, é uma regra nova: combinar antes e atualizar os testes.
#   5. Gravar sempre o ISBN normalizado no banco: assim "978-3-16-148410-0" e "9783161484100"
#      são o mesmo livro e a restrição UNIQUE (`uq_livro_isbn`) pega a duplicidade.
#   6. Rodar `pytest tests/livros/test_isbn.py`.
