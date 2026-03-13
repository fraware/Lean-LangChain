# Obligation Runtime Review UI — production image
# Build from repo root: docker build -f infra/docker/review-ui.Dockerfile -t obligation-review-ui:latest .
# Set Gateway URL at build time: docker build --build-arg NEXT_PUBLIC_GATEWAY_URL=https://gateway.example.com -f infra/docker/review-ui.Dockerfile -t obligation-review-ui:latest .

FROM node:20-alpine AS builder

WORKDIR /app

# Copy package files and install deps
COPY apps/review-ui/package.json ./
COPY apps/review-ui/package-lock.json* ./
RUN npm ci 2>/dev/null || npm install

# Copy app source (from repo root context)
COPY apps/review-ui/ ./

# Build-time env for Next.js public URL (baked into client bundle)
ARG NEXT_PUBLIC_GATEWAY_URL=http://localhost:8000
ENV NEXT_PUBLIC_GATEWAY_URL=$NEXT_PUBLIC_GATEWAY_URL

RUN npm run build
# Standalone does not include .next/static or public; copy them in so server.js can serve them
RUN cp -r /app/.next/static /app/.next/standalone/.next/ && (cp -r /app/public /app/.next/standalone/ 2>/dev/null || true)

# --- Runtime: minimal serve ---
FROM node:20-alpine AS runtime

WORKDIR /app

RUN addgroup -g 1000 -S obr && adduser -u 1000 -S obr -G obr

COPY --from=builder /app/.next/standalone ./

USER obr

EXPOSE 3000

ENV NODE_ENV=production
ENV HOSTNAME=0.0.0.0
ENV PORT=3000

CMD ["node", "server.js"]
