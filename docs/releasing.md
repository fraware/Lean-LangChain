# Releasing

How to cut a release: versioning, compatibility policy, pre-release checklist, tagging, GitHub Release, and artifact publication. Before tagging, run `make check-full` from the repo root; see [tests-and-ci.md](tests-and-ci.md).

## Versioning

The project uses [Semantic Versioning](https://semver.org/spec/v2.0.0.html). Document the new version and release notes (e.g. in a release draft or commit message) before tagging.

## Compatibility policy

- **Pre-1.0:** Minor versions may add features or fix bugs; patch versions are backward-compatible fixes. Breaking changes to the public API (Gateway HTTP, MCP tool list, SDK method names, operation catalog) are avoided in patch releases and called out in release notes for minor releases.
- **Public API surface:** Gateway routes under `/v1`, MCP tool names `obligation/*`, Python SDK (`ObligationRuntimeClient` methods), and TypeScript SDK (built client methods) are kept in parity; see [tests/contract/](../tests/contract/) and the operation catalog. Breaking changes to these surfaces require a minor (or major) version bump and release notes.
- **Plugin contract:** Policy pack plugin contract v1 (see [docs/architecture/plugin-contract.md](architecture/plugin-contract.md)) is stable; new optional fields may be added with defaults.
- **Release notes:** Tag and GitHub Release descriptions should list user-facing changes and any breaking or compatibility notes so adopters can decide when to upgrade.

## Pre-release checklist

1. Run the full check from repo root with the same Python used in CI: `make check-full` and `make typecheck`.
2. Bump version in root `pyproject.toml` and in any package `pyproject.toml` files you ship (e.g. `packages/schemas`, `apps/lean-gateway`) to match the release.

## Tagging

Create an annotated tag (e.g. for 0.1.0):

```bash
git tag -a v0.1.0 -m "Release v0.1.0"
git push origin v0.1.0
```

The **Release** workflow (`.github/workflows/release.yml`) runs on push of tags matching `v*` and executes the full check (lint, typecheck, tests, Postgres path). Ensure the workflow passes before considering the tag the official release.

## GitHub Release

Optionally create a GitHub Release from the tag. Use your release notes (e.g. from a changelog or commit history) as the release description.

## Artifact publication

**Python (PyPI):** Individual packages (e.g. `obligation-runtime-schemas`, `obligation-runtime-sdk`, `obligation-runtime-lean-gateway`, `obligation-runtime-orchestrator`) have their own `pyproject.toml`. Publish from a clean tag after the Release workflow has passed. Do not store API keys in the repo; use GitHub Secrets or OIDC for uploads in CI. Build and publish each package separately (e.g. `pip install build && python -m build packages/schemas` then upload).

**TypeScript (npm):** Publish from `packages/sdk-ts` as **`@lean-langchain/sdk`** (`npm publish --access public` after `npm run build`). Version 1.0+ uses the scoped name only; legacy **obligation-runtime-sdk-ts** 0.1.x is frozen. See [packages/sdk-ts/MIGRATION.md](../packages/sdk-ts/MIGRATION.md) and [naming.md](architecture/naming.md).

**Containers (OCI):** Gateway and worker images can be built from `infra/docker/`; tag images with the release version (e.g. `v0.1.0`) for traceability. Document the image names and any registry in the release notes.

**Visibility:** Release workflow runs on tags `v*`; passing the workflow is the gate for considering a tag the official release. Publish release notes (GitHub Release body or CHANGELOG) so adopters see compatibility and breaking changes.

See [CONTRIBUTING.md](../CONTRIBUTING.md) for the full check and branch expectations.

**See also:** [tests-and-ci.md](tests-and-ci.md), [CONTRIBUTING.md](../CONTRIBUTING.md), [architecture/plugin-contract.md](architecture/plugin-contract.md).
