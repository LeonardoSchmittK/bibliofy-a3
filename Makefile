.PHONY: front back app run help

help:
	@echo "Comandos disponiveis:"
	@echo "  make front    -> Roda apenas o frontend (Vite)"
	@echo "  make back     -> Sobe o banco (Docker) e roda o backend (FastAPI)"
	@echo "  make run app  -> Roda front e back juntos"

front:
	cd frontend && npm run dev

back:
	cd backend && docker compose up -d && uv run uvicorn app.main:app --reload

app:
ifeq ($(OS),Windows_NT)
	start "Frontend" cmd /k "cd frontend && npm run dev" && start "Backend" cmd /k "cd backend && docker compose up -d && uv run uvicorn app.main:app --reload"
else
	$(MAKE) front & $(MAKE) back; wait
endif

run:
ifeq ($(filter-out run,$(MAKECMDGOALS)),app)
	$(MAKE) app
else
	@echo "Use 'make run app' para subir front e back, ou 'make front' para rodar so o front."
endif