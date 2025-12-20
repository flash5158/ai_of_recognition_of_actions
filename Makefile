# Makefile with common development commands
.PHONY: up down logs export-onnx shell build

up:
	docker compose up --build -d

down:
	docker compose down

logs:
	docker compose logs -f --tail=200 app milvus

export-onnx:
	# run ONNX export inside the app container (or run locally in venv)
	docker compose exec app python detectors/export_onnx.py

frontend-up:
	# build and run frontend only
	docker compose build frontend && docker compose up -d frontend

frontend-logs:
	docker compose logs -f --tail=200 frontend

shell:
	docker compose exec app /bin/bash

build:
	docker compose build --no-cache app
