# Contributing to Obligation Runtime

Thank you for your interest in contributing. This document covers setup, the full check, and how to submit changes.

## Setup

1. **Clone and install.** From the repository root, use a single Python interpreter for install and all commands (e.g. an activated venv). If your venv has no pip, run `python -m ensurepip` first.

   ```bash
   make install-dev-full
   ```

   See [README.md](README.md) Quick start and [docs/running.md](docs/running.md) for details.

2. **Environment.** Copy [.env.example](.env.example) to `.env` if you need local overrides. Never commit `.env` or real secrets. For the Review UI, copy `apps/review-ui/.env.example` to `apps/review-ui/.env.local` and set `NEXT_PUBLIC_GATEWAY_URL`.

3. **Demos (optional).** To run the core or full demo, start the Gateway (`uvicorn obligation_runtime_lean_gateway.api.app:app` from repo root), then `make demo-core` or `make demo-full`. See [docs/demos/README.md](docs/demos/README.md).

## Before you submit

Run the full check from the repo root with the same Python you used for install:

```bash
make check-full
```

This runs lint (Ruff), typecheck (Mypy), schema tests, unit tests, integration tests, regression tests, and schema export. Optionally run `make typecheck` separately. See [docs/tests-and-ci.md](docs/tests-and-ci.md) for CI configuration (branch, Postgres service, optional jobs).

## Branch and pull requests

- Target the default branch (`main` or `master`). Create a feature branch from it.
- Ensure the full check passes locally. CI will run the same check on push/PR.
- Maintainers may request changes before merge. Keep PRs focused; link issues if applicable.

## Code style

- **Python:** Ruff and Black (see root [pyproject.toml](pyproject.toml): line-length 100, target Python 3.12). Mypy is run in the full check; strictness and overrides are in the root `pyproject.toml`.
- **Public API:** Prefer the stable imports listed in [docs/integrate.md](docs/integrate.md) (Public API table) so reusers and type-checkers see a consistent surface.

## Plugins and extensions

- **Policy packs (plugin contract v1):** Custom YAML packs can be loaded by name or path. Contract, schema, and versioning are documented in [docs/architecture/plugin-contract.md](docs/architecture/plugin-contract.md). Use `load_pack_from_path(path)` or `load_pack(name)`; set `OBR_POLICY_PACK` to a pack name or absolute path.
- **Starter templates:** [examples/integrations/](examples/integrations/README.md) — MCP tool builder, LangGraph embed, policy pack extension. Use these as copy-paste bases for your integration.

## Optional tooling

- **Dependabot:** The repo may have a Dependabot config for dependency updates. Review and run the full check after upgrading.
- **Versioning:** Releases are tagged (e.g. `v0.1.0`). See [CHANGELOG.md](CHANGELOG.md) and, if present, [docs/releasing.md](docs/releasing.md) for release and versioning policy.

## Code of conduct

By participating in this project, you agree to uphold our [Code of Conduct](CODE_OF_CONDUCT.md).

**See also:** [README.md](README.md), [docs/tests-and-ci.md](docs/tests-and-ci.md), [docs/integrate.md](docs/integrate.md), [docs/releasing.md](docs/releasing.md), [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).
