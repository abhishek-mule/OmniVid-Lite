.PHONY: help install dev dev-frontend dev-backend worker test test-smoke lint format clean docker-up docker-down frontend-install frontend-dev

help:
	@echo "Available commands:"
	@echo "  make install         - Install all dependencies"
	@echo "  make dev             - Run full development stack"
	@echo "  make dev-backend     - Run backend development server"
	@echo "  make dev-frontend    - Run frontend development server"
	@echo "  make worker          - Run background worker"
	@echo "  make test            - Run all tests"
	@echo "  make test-smoke      - Run smoke tests (render, status, download)"
	@echo "  make lint            - Run linters"
	@echo "  make format          - Format code"
	@echo "  make clean           - Clean temporary files"
	@echo "  make docker-up       - Start Docker containers"
	@echo "  make docker-down     - Stop Docker containers"
	@echo "  make frontend-install - Install frontend dependencies"

install:
	pip install -r requirements.txt
	npm install --prefix remotion_engine/

frontend-install:
	cd frontend && npm install

dev:
	@echo "Starting full development stack..."
	@echo "Backend: http://localhost:8000"
	@echo "Frontend: http://localhost:3000"
	@echo "API Docs: http://localhost:8000/docs"
	@echo ""
	@echo "Run 'make worker' in another terminal for background processing"
	make -j2 dev-backend dev-frontend

dev-backend:
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

dev-frontend:
	cd frontend && npm start

worker:
	python -m app.worker

test:
	pytest tests/ -v --cov=app --cov-report=html

test-smoke:
	pytest tests/test_api.py::test_render_success tests/test_api.py::test_status_success tests/test_api.py::test_download_job_not_ready -v

lint:
	flake8 app/
	mypy app/

format:
	black app/
	isort app/

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	rm -rf .pytest_cache
	rm -rf htmlcov
	rm -rf .coverage

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

docker-logs:
	docker-compose logs -f