.PHONY: setup test lint format run clean

setup:
	pip install -e .[dev]

format:
	python -m isort .
	python -m black .

lint:
	python -m pylint *.py
	python -m mypy *.py

test:
	python -m pytest

run:
	python main.py

clean:
	rm -rf __pycache__ .pytest_cache .mypy_cache
