.PHONY: train dev test help

help:
	@echo "DealCheck Commands:"
	@echo "  make train    - Download data, generate synthetic chats, train Model A & B, evaluate"
	@echo "  make dev      - Start FastAPI backend and Vite frontend"
	@echo "  make test     - Run pytest backend test suite"

train:
	python train.py

dev:
	python run_dev.py

test:
	pytest backend/tests
