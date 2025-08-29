.PHONY: install start dev test lint fmt clean smoke

# Default port
PORT ?= 8000

install:
	pip install -r requirements.txt

start:
	@echo "Starting FastAPI application on port $(PORT)..."
	uvicorn app.main:app --host 0.0.0.0 --port $(PORT)

dev:
	uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload --reload-exclude "reference/*" --reload-exclude "data/*"

test:
	venv/bin/pytest tests/

lint:
	@echo "Linting configuration will be added in later phases"

fmt:
	@echo "Formatting configuration will be added in later phases"

clean:
	rm -rf __pycache__ .pytest_cache
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true

smoke:
	./scripts/smoke.sh http://localhost:8000
