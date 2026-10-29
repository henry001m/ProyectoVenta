.PHONY: install dev api web mobile test lint typecheck build migrate seed

install:
	python3 -m venv services/api/.venv || true
	services/api/.venv/bin/pip install -r services/api/requirements.txt
	yarn --cwd apps/web install
	cd apps/mobile && flutter pub get

dev:
	@echo "Run services separately: make api, make web, then cd apps/mobile && flutter run"

api:
	cd services/api && .venv/bin/python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

web:
	npm --prefix apps/web start

mobile:
	cd apps/mobile && flutter run

test:
	cd services/api && .venv/bin/python -m pytest
	npm --prefix apps/web test -- --watch=false
	cd apps/mobile && flutter test

lint:
	cd services/api && .venv/bin/python -m compileall app
	npm --prefix apps/web run lint
	cd apps/mobile && flutter analyze

typecheck:
	npm --prefix apps/web run typecheck
	cd services/api && .venv/bin/python -m compileall app

build:
	npm --prefix apps/web run build
	cd apps/mobile && flutter build apk --debug

migrate:
	cd services/api && .venv/bin/alembic upgrade head

seed:
	cd services/api && .venv/bin/python -m app.seed

