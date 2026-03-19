# Migration to @lean-langchain/sdk

As of **v1.0.0**, the TypeScript SDK is published as **`@lean-langchain/sdk`**.

## Install

```bash
npm install @lean-langchain/sdk
```

## Replacing legacy package names

Remove legacy package references and add the scoped package. Import paths stay the same if you use the default export:

```ts
import { ObligationRuntimeClient } from "@lean-langchain/sdk";
```

Legacy package names are no longer published on new major lines. Pin to the pre-1.0 line only if you must stay on the old API surface until you migrate.
