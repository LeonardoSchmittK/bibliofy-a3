"""Camada "Controller": rotas /usuarios (cadastro, consulta, edição e papel).

Testes que devem passar: tests/auth/test_rotas_usuarios.py.
"""

# TODO(#35) Passo a passo da implementação:
#   1. `router = APIRouter(prefix="/usuarios", tags=["usuarios"])`.
#   2. `POST /` (201, `response_model=UsuarioSaida`): `Depends(exige_bibliotecario)`;
#      corpo `UsuarioCriar`; chama `usuario_service.criar_usuario`; e-mail/matrícula repetidos
#      -> 409. Não devolve token e não mexe na sessão de quem cadastra.
#   3. `GET /` (`list[UsuarioSaida]`): `Depends(usuario_autenticado)`; query params opcionais
#      `nome`, `matricula`, `papel`; o filtro por identidade do LEITOR é aplicado no service.
#   4. `GET /{codigo}`: `Depends(usuario_autenticado)`; LEITOR só o próprio (senão 403);
#      BIBLIOTECARIO recebe 404 se o código não existir.
#   5. `PATCH /{codigo}`: `Depends(exige_bibliotecario)`; corpo `UsuarioAtualizar`
#      (campo `papel` no corpo é ignorado ou recusado com 422, mas nunca aplicado).
#   6. `PUT /{codigo}/papel`: `Depends(exige_bibliotecario)`; corpo `PapelAlterar`;
#      404 se o usuário não existir; 422 para papel desconhecido.
#   7. Toda rota usa uma das duas dependências de `app/api/deps.py`; nenhuma rota de usuário é
#      pública. Quem decide permissão é o servidor, independentemente do front.
#   8. Registrar o router em `app/main.py` (`app.include_router(usuarios.router)`).
#   9. Rodar `pytest tests/auth/test_rotas_usuarios.py`.
