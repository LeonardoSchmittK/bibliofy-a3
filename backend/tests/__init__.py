import os

# A chave do JWT não tem valor padrão no código (SEC02): sem isto, importar `app.main`
# nos testes falharia assim que `Settings` passar a exigir `JWT_SECRET`.
os.environ.setdefault("JWT_SECRET", "segredo-somente-para-testes-0123456789abcdef")
