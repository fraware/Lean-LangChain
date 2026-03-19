# Naming: Lean-LangChain and Obligation Runtime

## Public name

**Lean-LangChain** is the repository and product name used in documentation, README, and community-facing material.

## Python packages (PyPI)

The installable distribution is **obligation-runtime** (meta-package). Import paths use the `obligation_runtime_*` prefix (e.g. `obligation_runtime_schemas`, `obligation_runtime_policy`). That prefix is stable for integrators and should not be renamed casually.

## TypeScript SDK (npm)

The published package is **`@lean-langchain/sdk`** (from `packages/sdk-ts`, semver 1.x+).

The legacy name **obligation-runtime-sdk-ts** applied through **0.1.x** only. New work should use:

```bash
npm install @lean-langchain/sdk
```

See [packages/sdk-ts/MIGRATION.md](../../packages/sdk-ts/MIGRATION.md) and [releasing.md](../releasing.md).

## Summary

| Surface            | Name                      |
|--------------------|---------------------------|
| Repo / docs        | Lean-LangChain            |
| PyPI root          | obligation-runtime        |
| Python imports     | obligation_runtime_*      |
| npm (current)      | @lean-langchain/sdk       |
