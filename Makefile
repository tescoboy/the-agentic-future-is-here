.PHONY: install start dev test lint fmt clean smoke

# Default port
PORT ?= 8000

install:
	python3 -m venv venv
	venv/bin/pip install -r requirements.txt

start:
	@echo "Checking for processes on port $(PORT)..."
	@if lsof -ti tcp:$(PORT) > /dev/null 2>&1; then \
		PID=$$(lsof -ti tcp:$(PORT)); \
		echo "Killing process on port $(PORT) (PID $$PID)"; \
		kill -9 $$PID; \
		sleep 1; \
	fi
	venv/bin/uvicorn app.main:app --host 0.0.0.0 --port $(PORT)

dev:
	venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload --reload-exclude "reference/*" --reload-exclude "data/*"

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
