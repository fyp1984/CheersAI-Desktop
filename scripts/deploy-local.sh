#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
COMPOSE_FILE="${COMPOSE_FILE:-${ROOT_DIR}/docker/docker-compose.yaml}"
DEPLOY_LOG="${ROOT_DIR}/deployment.log"
DEPLOY_MODE="${DEPLOY_MODE:-compose}"
STACK_NAME="${STACK_NAME:-cheersai}"
VERSION="${1:-$(date -u +%Y%m%d%H%M%S)}"

LOCAL_BACKEND_IMAGE="cheersai/backend:${VERSION}"
LOCAL_WEB_IMAGE="cheersai/web:${VERSION}"
TARGET_BACKEND_IMAGE="${LOCAL_BACKEND_IMAGE}"
TARGET_WEB_IMAGE="${LOCAL_WEB_IMAGE}"

if [[ -n "${HARBOR_REGISTRY:-}" ]]; then
  HARBOR_PROJECT="${HARBOR_PROJECT:-cheersai}"
  TARGET_BACKEND_IMAGE="${HARBOR_REGISTRY}/${HARBOR_PROJECT}/backend:${VERSION}"
  TARGET_WEB_IMAGE="${HARBOR_REGISTRY}/${HARBOR_PROJECT}/web:${VERSION}"
fi

echo "[deploy-local] building backend image ${LOCAL_BACKEND_IMAGE}"
docker build -t "${LOCAL_BACKEND_IMAGE}" -f "${ROOT_DIR}/api/Dockerfile.local" "${ROOT_DIR}/api"

echo "[deploy-local] building web image ${LOCAL_WEB_IMAGE}"
docker build -t "${LOCAL_WEB_IMAGE}" -f "${ROOT_DIR}/web/Dockerfile" --target production "${ROOT_DIR}/web"

if [[ "${TARGET_BACKEND_IMAGE}" != "${LOCAL_BACKEND_IMAGE}" ]]; then
  echo "[deploy-local] tagging and pushing Harbor images"
  docker tag "${LOCAL_BACKEND_IMAGE}" "${TARGET_BACKEND_IMAGE}"
  docker tag "${LOCAL_WEB_IMAGE}" "${TARGET_WEB_IMAGE}"
  docker push "${TARGET_BACKEND_IMAGE}"
  docker push "${TARGET_WEB_IMAGE}"
fi

export BACKEND_IMAGE="${TARGET_BACKEND_IMAGE}"
export WEB_IMAGE="${TARGET_WEB_IMAGE}"

if [[ "${DEPLOY_MODE}" == "swarm" ]]; then
  echo "[deploy-local] deploying stack ${STACK_NAME} with ${COMPOSE_FILE}"
  docker stack deploy -c "${COMPOSE_FILE}" "${STACK_NAME}" --with-registry-auth
else
  echo "[deploy-local] running docker compose rollout with ${COMPOSE_FILE}"
  docker compose -f "${COMPOSE_FILE}" up -d
fi

mkdir -p "$(dirname "${DEPLOY_LOG}")"
printf '%s version=%s backend=%s web=%s mode=%s\n' \
  "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  "${VERSION}" \
  "${TARGET_BACKEND_IMAGE}" \
  "${TARGET_WEB_IMAGE}" \
  "${DEPLOY_MODE}" >> "${DEPLOY_LOG}"

echo "[deploy-local] deployment recorded in ${DEPLOY_LOG}"
