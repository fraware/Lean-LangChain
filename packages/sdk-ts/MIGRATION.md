# Migration from obligation-runtime-sdk-ts

As of **v1.0.0**, the TypeScript SDK is published as **`@lean-langchain/sdk`**.

## Install

```bash
npm install @lean-langchain/sdk
```

## Replacing the legacy package

Remove `obligation-runtime-sdk-ts` and add the scoped package. Import paths stay the same if you use the default export:

```ts
import { ObligationRuntimeClient } from "@lean-langchain/sdk";
```

The legacy package name is no longer published on new major lines. Pin to `obligation-runtime-sdk-ts@0.1.x` only if you must stay on the pre-1.0 API until you migrate.
