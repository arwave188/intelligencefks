.PHONY: setup compose-up compose-down index agent test train-sft train-dpo clean

# Variables
REPO ?= examples/repo_teste
TASK ?= "Corrigir soma errada"

# Setup local environment
setup:
	python -m venv .venv
	.venv/bin/pip install --upgrade pip
	.venv/bin/pip install -r requirements.txt
	@echo "Environment setup complete. Activate with: source .venv/bin/activate"

# Docker Compose commands
compose-up:
	docker compose up -d qdrant
	@echo "Qdrant started. Waiting for health check..."
	@sleep 10

compose-up-api:
	docker compose up -d qdrant api
	@echo "Qdrant and API started. API available at http://localhost:8000"

compose-down:
	docker compose down

compose-build:
	docker compose build

# Index repository
index:
	python -m scripts.index_repo --repo $(REPO) --rebuild

# Run agent
agent:
	python cli.py fix $(TASK) --repo $(REPO)

# Run tests
test:
	pytest tests/ -v --cov=. --cov-report=html

# Lint and format
lint:
	ruff check .
	mypy .

format:
	ruff format .

# Training commands
train-sft:
	python training/finetune_lora.py --train data/sft_train.jsonl --eval data/sft_eval.jsonl

train-dpo:
	python training/dpo_train.py --data data/dpo_train.jsonl

# Generate training data
generate-data:
	python training/sft_dataset.py --n 1000 --langs py,ts

# API commands
api:
	python cli.py api --host 0.0.0.0 --port 8000

api-dev:
	python cli.py api --host 0.0.0.0 --port 8000 --reload

# Status
status:
	python cli.py status

# Example commands
example:
	bash scripts/run_agent_example.sh

example-remote:
	bash scripts/run_agent_example.sh --remote

# Clean up
clean:
	rm -rf .venv/
	rm -rf .qdrant/
	rm -rf .runs/
	rm -rf out-lora/
	rm -rf out-dpo/
	rm -rf __pycache__/
	find . -name "*.pyc" -delete
	find . -name "*.pyo" -delete
	find . -name "*.bak" -delete

# Help
help:
	@echo "Available commands:"
	@echo "  setup          - Create virtual environment and install dependencies"
	@echo "  compose-up     - Start Qdrant with Docker Compose"
	@echo "  compose-up-api - Start Qdrant and API with Docker Compose"
	@echo "  compose-down   - Stop Docker Compose services"
	@echo "  index          - Index repository (REPO=path)"
	@echo "  agent          - Run agent (TASK='task description' REPO=path)"
	@echo "  api            - Start API server"
	@echo "  api-dev        - Start API server with auto-reload"
	@echo "  status         - Show system status"
	@echo "  example        - Run example task"
	@echo "  example-remote - Run example task via API"
	@echo "  test           - Run tests with coverage"
	@echo "  lint           - Run linting and type checking"
	@echo "  format         - Format code with ruff"
	@echo "  train-sft      - Train SFT model"
	@echo "  train-dpo      - Train DPO model"
	@echo "  generate-data  - Generate training data"
	@echo "  clean          - Clean up generated files"
