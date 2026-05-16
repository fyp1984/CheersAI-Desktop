# Deployment Guide

## Scope

This deployment flow covers the global plugin sharing and team model credential rollout for local Docker and Docker Swarm environments.

## Required Variables

- `ENCRYPTION_KEY`: AES-256-GCM key material for `team_model_config.api_key_enc`. Inject through runtime environment or Docker secret in shared environments.
- `PLUGIN_DIR`: Plugin installation directory inside containers. Default remains `/app/plugins`.
- `BACKEND_IMAGE` / `WEB_IMAGE`: Optional image overrides consumed by `docker/docker-compose.yaml`.

## Local Docker Rollout

1. Prepare `docker/.env` from `docker/.env.example`.
2. Set a non-empty `ENCRYPTION_KEY`.
3. Run:

```bash
chmod +x scripts/deploy-local.sh
./scripts/deploy-local.sh
```

4. The script builds versioned backend and web images, performs `docker compose -f docker/docker-compose.yaml up -d`, and appends the deployed version to `deployment.log`.

## Swarm / Harbor Rollout

1. Export deployment variables:

```bash
export ENCRYPTION_KEY='replace-with-runtime-secret'
export HARBOR_REGISTRY='harbor.local'
export HARBOR_PROJECT='cheersai'
export DEPLOY_MODE='swarm'
export STACK_NAME='cheersai'
```

2. If Harbor requires authentication, login before rollout:

```bash
docker login "${HARBOR_REGISTRY}"
```

3. Run the deployment script with an explicit version:

```bash
./scripts/deploy-local.sh 2.3.0
```

4. The script builds local images, tags and pushes `backend` / `web` images to Harbor, then executes:

```bash
docker stack deploy -c docker/docker-compose.yaml cheersai --with-registry-auth
```

5. The deployed version is appended to `deployment.log` for rollback reference.

## Rollback Reference

- Inspect the latest deployment records:

```bash
tail -n 20 deployment.log
```

- Re-run `scripts/deploy-local.sh <previous-version>` after restoring the matching image tags in Harbor or local Docker cache.
