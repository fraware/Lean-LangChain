# @lean-langchain/sdk

Official TypeScript SDK for **Lean-LangChain Gateway**.

## Install

```bash
npm install @lean-langchain/sdk
```

## Usage

```ts
import { ObligationRuntimeClient } from "@lean-langchain/sdk";

const client = new ObligationRuntimeClient({ baseUrl: "http://localhost:8000" });
```

Types are generated from the gateway OpenAPI snapshot at `../../contracts/openapi/lean-gateway.json` (`npm run generate:types`). Run `npm run build` before publish. In the Lean-LangChain monorepo, `make verify-openapi-sdk-contract` (part of `make check-full`) regenerates the snapshot and types and fails if the tree is dirty, keeping Python schemas, Gateway, and TS types in sync.

## Migrating from legacy package names

See [MIGRATION.md](MIGRATION.md). Legacy package stopped at 0.1.x; use this scoped package for 1.x and later.
