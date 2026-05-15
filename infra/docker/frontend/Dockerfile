# Yarn workspace dev server (`packages/frontend`). Build context: repo root `.`
FROM node:20-bookworm-slim

# Node 20 ships a `/usr/local/bin/yarn` stub/corepack shim that often fails during `docker build` (exit 127).
# Replace it with Yarn classic 1.x for this Yarn v1 workspace + lockfile.
RUN rm -f /usr/local/bin/yarn /usr/local/bin/yarnpkg \
    && npm install -g yarn@1.22.22

WORKDIR /workspace

COPY package.json yarn.lock ./
COPY packages/frontend/package.json ./packages/frontend/
COPY packages/backend/package.json ./packages/backend/

ENV YARN_NETWORK_TIMEOUT=600000
# Workspace `backend` declares `install: uv sync` — not available in this Node-only image; skip lifecycle scripts here.
RUN yarn install --frozen-lockfile --ignore-scripts

COPY turbo.json ./
COPY packages/frontend ./packages/frontend

WORKDIR /workspace/packages/frontend

EXPOSE 3800

# Browser hits Vite on the host; Vite proxies /api → backend service inside the compose network.
ENV VITE_DEV_PROXY_TARGET=http://backend:3801

CMD ["yarn", "dev", "--host", "0.0.0.0"]
