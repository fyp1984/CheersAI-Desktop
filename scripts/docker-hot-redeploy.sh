#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DOCKER_DIR="${ROOT_DIR}/docker"

cd "${ROOT_DIR}"
git status --porcelain
git rev-parse HEAD

cd "${DOCKER_DIR}"
COMPOSE_FILES=(-f docker-compose.yaml -f docker-compose.override.yaml -f docker-compose.hot.yaml)

TS="$(date +%Y%m%d_%H%M%S)"
docker image inspect cheersai-api:local >/dev/null 2>&1 && docker tag cheersai-api:local "cheersai-api:local_prev_${TS}" || true
docker image inspect cheersai-web:local >/dev/null 2>&1 && docker tag cheersai-web:local "cheersai-web:local_prev_${TS}" || true
docker image inspect cheersai-web:hot >/dev/null 2>&1 && docker tag cheersai-web:hot "cheersai-web:hot_prev_${TS}" || true

CONSOLE_API_URL= APP_API_URL= SERVICE_API_URL= FILES_URL= MARKETPLACE_API_URL= MARKETPLACE_URL= \
  docker compose "${COMPOSE_FILES[@]}" build api web worker worker_beat
CONSOLE_API_URL= APP_API_URL= SERVICE_API_URL= FILES_URL= MARKETPLACE_API_URL= MARKETPLACE_URL= \
  docker compose "${COMPOSE_FILES[@]}" up -d --remove-orphans
CONSOLE_API_URL= APP_API_URL= SERVICE_API_URL= FILES_URL= MARKETPLACE_API_URL= MARKETPLACE_URL= \
  docker compose "${COMPOSE_FILES[@]}" restart nginx

for _ in $(seq 1 180); do
  code="$(curl -sS --max-time 5 -o /dev/null -w "%{http_code}" http://localhost/console/api/ping || true)"
  if [[ "${code}" == "200" ]]; then
    break
  fi
  sleep 1
done

for _ in $(seq 1 60); do
  code="$(curl -sS --max-time 120 -o /dev/null -w "%{http_code}" http://localhost/apps || true)"
  if [[ "${code}" =~ ^(200|301|302)$ ]]; then
    break
  fi
  sleep 1
done

for _ in $(seq 1 60); do
  code="$(curl -sS --max-time 120 -o /dev/null -w "%{http_code}" http://localhost:3000/apps || true)"
  if [[ "${code}" =~ ^(200|301|302)$ ]]; then
    break
  fi
  sleep 1
done

docker compose "${COMPOSE_FILES[@]}" ps
