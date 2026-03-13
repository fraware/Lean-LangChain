# Tests

**Purpose:** Test layout, how to run them, and environment-dependent skips. **Audience:** contributors and CI. Tests validate the Obligation Runtime workflow, use cases, and LangChain / LangSmith / LangGraph integrations. For a full mapping of test files to workflow steps, see **docs/workflow.md** (section "Tests: mapping to workflow and integrations").

## Layout

- **unit/** — Unit tests for policy, batch combine, axiom audit, axiom producer (`test_axiom_producer_lean.py` when lake in PATH), Gateway production assertions, LangSmith helpers (create_dataset, run_experiment, compare_runs, trace_to_dataset), and production tracer (OTLP, LangSmith mocks).
- **integration/** — Integration tests against the Gateway (TestClient or live): acceptance lane, graph runtime (LangGraph patch-admissibility), tools (LangChain toolset), MCP session affinity, review/resume flow, LangSmith fixed-corpus experiment, tracer E2E.
- **regressions/** — Golden-case regression suite; fixtures in `packages/evals/obligation_runtime_evals/fixtures.py` and `tests/regressions/fixtures/`.

## Running

From repo root:

- `pytest tests/` — all tests
- `pytest tests/unit/` — unit only
- `pytest tests/integration/` — integration only
- `make test` / CI — see `docs/tests-and-ci.md` for full check and optional jobs (langsmith, telemetry-e2e, etc.)

## Test skips (environment-dependent)

Some tests skip when required tooling or services are unavailable. This is intentional so the main CI job passes without Lean, Docker, or a live Postgres on the runner unless the optional CI job provides them.

| Cause | Tests that skip | How to run them |
|-------|-----------------|-----------------|
| **Postgres** | `test_checkpointer_postgres.py`, `test_review_store_postgres.py`, and any test that uses `@pytest.mark.skipif(not database_url)` | Set `DATABASE_URL` (and `CHECKPOINTER=postgres`, `REVIEW_STORE=postgres` where needed). CI main job runs with a Postgres service. |
| **Lean / LSP** | Acceptance-lane tests that need real `lake` or LSP; axiom producer (`test_axiom_producer_lean.py`) | Set `OBR_USE_LEAN_LSP=1` or `OBR_USE_REAL_FRESH_CHECKER=1` and have `lean` / `lake` / `lean4checker` in PATH. Axiom producer test runs when `lake` is in PATH and skips when build fails. See `docs/ci.md` (lean, fresh jobs); `make test-axiom-producer`. |
| **Docker** | Container runner and microVM tests in acceptance lane and worker isolation | Set `OBR_WORKER_RUNNER=container` (or `microvm`) and have Docker in PATH. See `docs/tests-and-ci.md` (container job). |
| **OTLP / tracer E2E** | `test_tracer_e2e_otlp.py` | Requires `obligation-runtime-telemetry[otlp]`. Local: `make test-tracer-e2e`. CI **telemetry-e2e** job runs it with continue-on-error. |
| **MCP stdio** | `test_mcp_server_stdio.py` | Skips when MCP server or stdio transport not available in env. |

`make check-full` runs with no optional env; expect roughly a dozen integration skips. With Postgres (as in CI), checkpointer and review-store tests run; with Lean/Docker in optional CI jobs, additional acceptance and worker tests run.

## Key integration tests

| Test file | What it validates |
|-----------|-------------------|
| test_graph_runtime.py | LangGraph graph: full run to terminal, reviewer-gated block, protected path needs_review, review payload patch_metadata |
| test_tools.py | LangChain tools: open_environment → create_session → apply_patch → check_interactive → batch_verify |
| test_acceptance_lane.py | Gateway acceptance lane: batch-verify result shape, evidence flags, strict acceptance (when env set) |
| test_langsmith_fixed_corpus.py | LangSmith: create_dataset + run_experiment with patch_admissibility runnable on regression corpus |
| test_review_resume_flow.py | Review API: resume endpoint and error handling |
| test_interrupt_resume.py | Interrupt/resume with MemorySaver; protected path → needs_review → approve → finalize |
| test_checkpointer_postgres.py | Postgres checkpointer: invoke then resume; resume after interrupt to accepted |
| test_full_demo.py | Full demo scenarios at graph level: valid proof edit accepted, sorry/false-theorem rejected, protected approve/reject, fixture existence; real lake build for demo patches when lake in PATH |
| test_full_demo_script.py | Full demo script: --help, gateway unreachable skips, -v and --ui-resume flags |

Integration tests use shared fixtures from `tests/conftest.py` and `tests/integration/conftest.py` (`gateway_app`, `gateway_client`, `gateway_tc`, `sdk_client`, `obr_graph`).

**See also:** [docs/workflow.md](../docs/workflow.md), [docs/tests-and-ci.md](../docs/tests-and-ci.md), [docs/running.md](../docs/running.md).
