# syntax=docker.io/docker/dockerfile:1
# The Next.js frontend. Three stages: install the packages, build the site, then a small image
# that only holds the standalone server (next.config.js: output 'standalone').

# The Node release line to follow (BASE_IMAGE comes from compose.yaml, NEXT_BASE_IMAGE pins
# the exact tested image in versions.env on the server)
ARG BASE_IMAGE=node:24-alpine

FROM ${BASE_IMAGE} AS base
# no telemetry to Vercel from the build or the server
ENV NEXT_TELEMETRY_DISABLED=1

# Install the packages
FROM base AS deps
WORKDIR /app
COPY package.json package-lock.json* ./
# package-lock.json is the exact tested set, written by scripts/refresh_versions.py (not in git).
# Without it (a development build) npm resolves the newest versions package.json allows.
RUN if [ -f package-lock.json ]; then npm ci; else npm install; fi

# Build the site. The pages fetch nothing at build time, so no API needs to be running.
FROM base AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
RUN npm run build

# The server
FROM base AS runner
WORKDIR /app
ENV NODE_ENV=production

RUN addgroup --system --gid 1001 nodejs && adduser --system --uid 1001 nextjs

COPY --from=builder /app/public ./public
# the standalone output: server.js with only the node_modules it needs
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static
# the fetch and image caches are written here while the server runs (a volume in compose.yaml)
RUN mkdir -p .next/cache && chown nextjs:nodejs .next/cache

USER nextjs
EXPOSE 3000
ENV PORT=3000
ENV HOSTNAME="0.0.0.0"
CMD ["node", "server.js"]
