# Review UI

**Purpose:** Next.js app for human approval: view review payloads, Approve/Reject, and **Resume run**. **Audience:** operators and integrators. Consumes the Obligation Runtime Gateway API.

## Development

```bash
npm install
npm run dev
```

Set the Gateway base URL so the UI can call the API. Copy `apps/review-ui/.env.example` to `.env.local` and set `NEXT_PUBLIC_GATEWAY_URL` (e.g. `http://localhost:8000`). See the main repo [docs/running.md](../../docs/running.md) for full environment variables.

## Production build and deploy

- **Standalone output:** `next.config.ts` sets `output: "standalone"` for container and minimal-server deploys.
- **Docker:** From repo root, build with the Gateway URL at build time: `docker build --build-arg NEXT_PUBLIC_GATEWAY_URL=https://your-gateway.example.com -f infra/docker/review-ui.Dockerfile -t obligation-review-ui:latest .` Run with `docker run -p 3000:3000 obligation-review-ui:latest`.
- **Static or host:** Run `npm run build` in `apps/review-ui` with `NEXT_PUBLIC_GATEWAY_URL` set, then `npm run start` (or serve the standalone output). See [docs/deployment.md](../../docs/deployment.md).

**See also:** [docs/running.md](../../docs/running.md), [docs/deployment.md](../../docs/deployment.md), [docs/architecture/review-surface.md](../../docs/architecture/review-surface.md), [README.md](../../README.md).
