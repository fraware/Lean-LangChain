.PHONY: lint format typecheck test test-schemas test-integration test-regressions export-schemas install-dev install-dev-full check check-full demo-scenario-1 demo-scenario-2 demo-scenario-3 demo-scenario-4 demo-scenario-5 demo-hero demo-hero-ui install-lean4checker test-fresh test-axiom-producer test-tracer-e2e benchmark benchmark-report

# Use python -m pip so install and gates use the same interpreter (e.g. .venv or conda)
install-dev:
	python -m pip install -e packages/schemas -e apps/lean-gateway

install-dev-full:
	python -m pip install -e packages/schemas -e packages/evals -e packages/telemetry -e packages/protocol -e packages/policy -e packages/sdk-py -e packages/tools -e apps/lean-gateway -e apps/orchestrator

lint:
	ruff check .

format:
	black .
	ruff check --fix .

typecheck:
	mypy packages/schemas apps/lean-gateway apps/orchestrator

test:
	pytest tests/unit

test-schemas:
	pytest tests/unit/test_schema_roundtrip.py tests/unit/test_hash_stability.py tests/unit/test_schema_export.py

# Requires project installed for active Python (make install-dev-full uses python -m pip so same interpreter is used)
export-schemas:
	python scripts/export_json_schemas.py

test-integration:
	pytest tests/integration

test-regressions:
	pytest tests/regressions -v

check: lint test-schemas test test-integration export-schemas

check-full: lint typecheck test-schemas test test-integration test-regressions export-schemas

demo-scenario-1:
	python scripts/demos/run_demo_scenario_1.py
demo-scenario-2:
	python scripts/demos/run_demo_scenario_2.py
demo-scenario-3:
	python scripts/demos/run_demo_scenario_3.py
demo-scenario-4:
	python scripts/demos/run_demo_scenario_4.py
demo-scenario-5:
	python scripts/demos/run_demo_scenario_5.py

demo-hero:
	python scripts/demos/run_hero_demo.py
demo-hero-ui:
	python scripts/demos/run_hero_demo.py --ui-resume

test-langsmith:
	pytest tests/unit/test_langsmith.py tests/integration/test_langsmith_fixed_corpus.py -v

install-lean4checker:
	python scripts/setup/install_lean4checker.py

test-fresh:
	OBR_USE_REAL_FRESH_CHECKER=1 pytest tests/integration/test_acceptance_lane.py::test_acceptance_lane_real_fresh_checker -v

# Run axiom producer test in lean-mini when lake is in PATH (skips otherwise)
test-axiom-producer:
	pytest tests/unit/test_axiom_producer_lean.py -v

# Tracer E2E: emit span and assert received by InMemorySpanExporter (requires obligation-runtime-telemetry[otlp])
test-tracer-e2e:
	pytest tests/integration/test_tracer_e2e_otlp.py -v

# Run benchmark from repo root with project env active (e.g. base conda or source .venv/bin/activate)
benchmark:
	python scripts/run_benchmark.py

benchmark-report:
	python scripts/run_benchmark.py --workload 5 --output docs/benchmark_report.json
