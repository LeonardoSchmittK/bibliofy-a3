# Testes

`pytest` usa, por padrão, um PostgreSQL 17 descartável via testcontainers (precisa de Docker).

`DATABASE_URL` é o banco da aplicação. `TEST_DATABASE_URL` é opcional e vale apenas para os testes. A suíte apaga e recria o schema `public` do banco de teste, então ele precisa ser descartável, ter nome `test`, `test_*` ou `*_test` e não pode ser o mesmo destino de `DATABASE_URL` ou `Settings.database_url`.

Com um container próprio:

docker run --rm -d -p 55432:5432 -e POSTGRES_USER=bibliofy -e POSTGRES_PASSWORD=teste -e POSTGRES_DB=bibliofy_test postgres:17
TEST_DATABASE_URL=postgresql+psycopg://bibliofy:teste@localhost:55432/bibliofy_test pytest

Destino fora dessas regras é recusado com `DestinoNaoAutorizadoError` antes de qualquer comando destrutivo.
