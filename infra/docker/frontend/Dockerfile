# Yarn workspace dev server (`packages/frontend`). Build context: repo root `.`
FROM node:20-bookworm-slim

RUN corepack enable && corepack prepare yarn@1.22.22 --activate

WORKDIR /workspace

COPY package.json yarn.lock ./
COPY packages/frontend/package.json ./packages/frontend/
COPY packages/backend/package.json ./packages/backend/

ENV YARN_NETWORK_TIMEOUT=600000
RUN yarn install --frozen-lockfile

COPY turbo.json ./
COPY packages/frontend ./packages/frontend

WORKDIR /workspace/packages/frontend

EXPOSE 3800

# Browser hits Vite on the host; Vite proxies /api → backend service inside the compose network.
ENV VITE_DEV_PROXY_TARGET=http://backend:3801

CMD ["yarn", "dev", "--host", "0.0.0.0"]
