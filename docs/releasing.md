# Releasing

How to cut a release: versioning, pre-release checklist, tagging, GitHub Release, and optional PyPI. Before tagging, run `make check-full` from the repo root; see [tests-and-ci.md](tests-and-ci.md).

## Versioning

The project uses [Semantic Versioning](https://semver.org/spec/v2.0.0.html). Document the new version and release notes (e.g. in a release draft or commit message) before tagging.

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

## PyPI (optional)

If you publish packages to PyPI:

- Publish from a clean tag after the Release workflow has passed.
- Do not use API keys or tokens in the repo; use GitHub Secrets or OIDC for uploads in CI.
- The root `pyproject.toml` defines optional-dependencies and metadata (classifiers, readme, keywords); individual packages (e.g. `obligation-runtime-schemas`, `obligation-runtime-lean-gateway`) have their own `pyproject.toml` and must be built and published separately if you distribute them on PyPI.

See [CONTRIBUTING.md](../CONTRIBUTING.md) for the full check and branch expectations.

**See also:** [tests-and-ci.md](tests-and-ci.md), [CONTRIBUTING.md](../CONTRIBUTING.md).
