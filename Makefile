# Makefile — Executive_KPI_Dashboard (BI: Vizro/Dash + pandas + SQLite)
# En Windows/PowerShell sin `make`, usar los comandos equivalentes del README.
# Sobrescribir el intérprete:  make test PYTHON=.venv/Scripts/python.exe

PYTHON ?= python

.PHONY: help install install-dev run lint format test review clean

help:
	@echo "Targets: install install-dev run lint format test review clean"

install:
	$(PYTHON) -m pip install -r requirements.txt

install-dev: install
	$(PYTHON) -m pip install -r requirements-dev.txt

run:
	$(PYTHON) app.py

lint:
	$(PYTHON) -m ruff check .

format:
	$(PYTHON) -m ruff check --fix .
	$(PYTHON) -m black .

test:
	$(PYTHON) -m pytest

review:
	@echo "Ejecuta /dashboard_review en Claude Code (ver .claude/skills/dashboard_review)."

clean:
	-rm -rf .pytest_cache .ruff_cache __pycache__ */__pycache__ */*/__pycache__
