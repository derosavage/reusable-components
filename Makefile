.PHONY: install test lint run clean

install:
	pip install -r requirements.txt

test:
	python -m pytest tests/ -v --tb=short

test-coverage:
	python -m pytest tests/ -v --tb=short --cov=. --cov-report=term-missing

run-auth:
	python -m services.auth_service.app

run-gateway:
	python -m services.api_gateway.app

run-analytics:
	uvicorn services.analytics_service.app:app --host 0.0.0.0 --port 8002 --reload

run-data-factory:
	python -m services.data_factory.app

run-daraja:
	python -m services.daraja_service.app

run-llm:
	uvicorn services.llm_service.app:app --host 0.0.0.0 --port 8005 --reload

run-worker:
	celery -A worker.celery_app worker --loglevel=info

docker-build:
	docker compose build

docker-up:
	docker compose up -d

docker-down:
	docker compose down

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name '*.pyc' -delete
