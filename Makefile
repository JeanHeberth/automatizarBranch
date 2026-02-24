.PHONY: help install test lint format clean run dev

help:
	@echo "🚀 AutomizarBranch - Comandos disponíveis"
	@echo ""
	@echo "make install      - Instala dependências"
	@echo "make test         - Executa testes"
	@echo "make test-cov     - Testes com cobertura"
	@echo "make lint         - Verifica código (flake8)"
	@echo "make format       - Formata código (black)"
	@echo "make format-check - Verifica formatação"
	@echo "make clean        - Remove arquivos temporários"
	@echo "make run          - Executa aplicação"
	@echo "make dev          - Executa em modo desenvolvimento"
	@echo "make all          - Install + Lint + Test"

install:
	pip install -r requirements.txt
	@echo "✅ Dependências instaladas"

test:
	pytest tests/ -v

test-cov:
	pytest tests/ -v --cov=. --cov-report=html --cov-report=term
	@echo "📊 Relatório de cobertura: htmlcov/index.html"

lint:
	flake8 . --count --select=E9,F63,F7,F82 --show-source
	flake8 . --count --exit-zero --max-complexity=10 --max-line-length=127

format:
	black . --line-length=127

format-check:
	black . --check --diff --line-length=127

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache htmlcov .coverage dist build *.egg-info 2>/dev/null || true
	@echo "🧹 Projeto limpo"

run:
	python main.py

dev:
	DEBUG=1 python main.py

all: clean install lint test
	@echo "✅ Tudo pronto!"

