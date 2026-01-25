# Makefile for FortiEscrow

.PHONY: help install test coverage lint clean docs

help:
	@echo "FortiEscrow - Available commands:"
	@echo "  make install       - Install dependencies"
	@echo "  make test          - Run all tests"
	@echo "  make test-security - Run security tests only"
	@echo "  make coverage      - Generate coverage report"
	@echo "  make lint          - Run code linting"
	@echo "  make clean         - Clean build artifacts"
	@echo "  make docs          - Build documentation"

install:
	pip install -r requirements.txt

test:
	python -m pytest tests/ -v

test-security:
	python -m pytest tests/security/ -v

coverage:
	python -m pytest tests/ --cov=contracts/ --cov-report=html

lint:
	python -m pylint contracts/
	python -m bandit -r contracts/

clean:
	rm -rf build/ dist/ *.egg-info
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name '*.pyc' -delete
	rm -rf .coverage htmlcov/

docs:
	@echo "Documentation is in /docs folder"
	@echo "Start with: README.md or docs/README.md"
