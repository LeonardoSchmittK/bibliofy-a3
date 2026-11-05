"""Regras de cadastro, consulta e papéis dos usuários (SEC01, SEC04).

Testes que devem passar: tests/auth/test_rotas_usuarios.py.
"""

# TODO(#35) Passo a passo da implementação:
#   1. `criar_usuario(db, dados: UsuarioCriar, operador: Pessoa) -> Pessoa`:
#        - papel SEMPRE "LEITOR" (definido aqui, no servidor) e `ativo=True`;
#        - `senha_hash = hash_senha(dados.senha.get_secret_value())`;
#        - e-mail ou matrícula repetidos (`IntegrityError`) viram erro de conflito -> 409
#          (fazer `db.rollback()` do savepoint ou checar antes);
#        - chamar `auditoria.registrar(CADASTRO / PESSOA)` e só então `db.commit()`;
#        - não devolver token nem alterar a sessão do operador.
#   2. `listar_usuarios(db, solicitante: Pessoa, nome=None, matricula=None, papel=None)`:
#        - se o solicitante for LEITOR, filtrar SEMPRE por `Pessoa.id == solicitante.id`,
#          qualquer que seja o filtro enviado (vale para listas e pesquisas);
#        - BIBLIOTECARIO vê todos e pode filtrar.
#   3. `obter_usuario(db, solicitante, codigo)`:
#        - LEITOR só acessa o próprio `codigo`; outro código -> `PermissionError` (403);
#        - BIBLIOTECARIO: se não existir -> não encontrado (404).
#   4. `atualizar_usuario(db, operador, codigo, dados: UsuarioAtualizar)`: edita só campos
#      cadastrais, nunca papel/senha; auditar ALTERACAO com antes/depois.
#   5. `alterar_papel(db, operador, codigo, papel)`: operação separada da edição cadastral;
#      404 se não existir; auditar ALTERACAO com dados={"papel": {"antes", "depois"}}.
#   6. Primeiro bibliotecário (SEC01): criado "na mão", fora da API. Criar um script
#      `backend/scripts/criar_bibliotecario.py` (pede nome, matrícula, e-mail e senha pelo terminal,
#      usa `hash_senha`) e documentar no README. Não há testes automatizados para ele.
