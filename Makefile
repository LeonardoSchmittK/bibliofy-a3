.PHONY: front front-test front-coverage back app run help

help:
	@echo "Comandos disponiveis:"
	@echo "  make front    -> Roda apenas o frontend (Vite)"
	@echo "  make front-test -> Roda os testes unitarios e de integracao do frontend"
	@echo "  make front-coverage -> Roda os testes do frontend com cobertura"
	@echo "  make back     -> Sobe o banco (Docker) e roda o backend (FastAPI)"
	@echo "  make run app  -> Roda front e back juntos"

front:
	cd frontend && npm run dev

front-test:
	cd frontend && npm test

front-coverage:
	cd frontend && npm run test:coverage

back:
	cd backend && docker compose stop api && docker compose up -d db && uv run uvicorn app.main:app --reload

# Git Bash also sets OS=Windows_NT; use cmd only for a native Windows shell.
ifeq ($(OS),Windows_NT)
ifeq ($(strip $(MSYSTEM)),)
ifeq ($(findstring sh,$(SHELL)),)
APP_ON_WINDOWS_CMD := 1
endif
endif
endif

ifeq ($(APP_ON_WINDOWS_CMD),1)
app:
	start "Frontend" cmd /k "cd frontend && npm run dev" && start "Backend" cmd /k "cd backend && docker compose stop api && docker compose up -d db && uv run uvicorn app.main:app --reload"
else
app:
	$(MAKE) -j2 front back
endif

run:
ifeq ($(filter-out run,$(MAKECMDGOALS)),app)
	$(MAKE) app
else
	@echo "Use 'make run app' para subir front e back, ou 'make front' para rodar so o front."
endif