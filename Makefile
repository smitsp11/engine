.PHONY: test test-update install run help

help:
	@echo "Agent Engine - Available Commands:"
	@echo "  make install    - Install dependencies"
	@echo "  make run        - Start the API server"
	@echo "  make test       - Run all tests"
	@echo "  make test-update - Run tests and update snapshots"

install:
	pip install -r requirements.txt

run:
	uvicorn api.app:app --host 0.0.0.0 --port 8000 --reload

test:
	python tests/run_all_tests.py

test-update:
	python tests/run_all_tests.py --update-snapshots

