.PHONY: lint format typecheck test test-schemas test-integration export-schemas

lint:
	ruff check .

format:
	black .
	ruff check --fix .

typecheck:
	mypy apps packages tests

test:
	pytest

test-schemas:
	pytest tests/unit/test_schema_roundtrip.py tests/unit/test_hash_stability.py

export-schemas:
	python scripts/export_json_schemas.py

test-integration:
	pytest tests/integration
