FROM node:22.23.1-bookworm-slim AS web
WORKDIR /build
COPY package.json package-lock.json ./
RUN npm ci
COPY src ./src
COPY public ./public
COPY handoff ./handoff
COPY scripts/build-engine.mjs ./scripts/build-engine.mjs
COPY index.html tsconfig.json vite.config.ts ./
RUN npm run build && node scripts/build-engine.mjs

FROM public.ecr.aws/lambda/python:3.13@sha256:40dcef2531da40c0fae6d11ee28e12313af9723fc1f0f31c1728c22e5112ec3c AS lambda
RUN dnf upgrade -y --releasever=2023.12.20260928 && dnf install -y libstdc++ && dnf clean all
COPY --from=web /usr/local/bin/node /usr/local/bin/node
WORKDIR /var/task
COPY backend/requirements.lock ./backend/requirements.lock
RUN pip install --no-cache-dir -r backend/requirements.lock
COPY --from=web /build/dist ./dist
COPY --from=web /build/backend/engine.mjs ./backend/engine.mjs
COPY --from=web /build/node_modules/decimal.js ./node_modules/decimal.js
COPY backend/*.py ./backend/
USER 10001
CMD ["backend.lambda_handler.web"]

FROM python:3.13.9-slim-bookworm AS server
RUN apt-get update && apt-get install -y --no-install-recommends libstdc++6 ca-certificates && rm -rf /var/lib/apt/lists/*
COPY --from=web /usr/local/bin/node /usr/local/bin/node
WORKDIR /app
COPY backend/requirements.lock ./backend/requirements.lock
RUN pip install --no-cache-dir -r backend/requirements.lock && useradd --uid 10001 --create-home app
COPY --from=web /build/dist ./dist
COPY --from=web /build/backend/engine.mjs ./backend/engine.mjs
COPY --from=web /build/node_modules/decimal.js ./node_modules/decimal.js
COPY backend/*.py ./backend/
USER 10001
EXPOSE 5180
CMD ["python","-m","uvicorn","backend.app:create_app","--factory","--host","0.0.0.0","--port","5180","--no-access-log","--proxy-headers","--forwarded-allow-ips","*"]
