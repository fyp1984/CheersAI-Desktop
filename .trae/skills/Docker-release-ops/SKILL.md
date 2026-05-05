---
name: "release-ops-flow"
description: "Standardizes multi-system release scripts, preflight checks, git-sync validation, rollout, monitoring, rollback, and local-docker separation. Invoke when designing or optimizing deployment workflows."
---

# Release Ops Flow

This skill standardizes reusable release and deployment workflows for server-side products, UAT environments, and local Docker helper flows.

## When to Invoke

Invoke this skill when:

- A product needs standardized deployment scripts.
- A repository needs push / build / release / monitor stages.
- You need preflight environment checks before release.
- You need Git-synced release rules so deployed code matches remote exactly.
- You need to separate cloud-server deployment scripts from local Docker scripts.
- You need a reusable structure for future systems or products.

Do not invoke when:

- The task is only a one-off shell command.
- The task is unrelated to deployment, monitoring, rollback, or release automation.

## Core Principles

1. One product, one directory.
2. One stage, one script.
3. Always provide a single entrypoint for operators.
4. Run preflight checks before build or deployment.
5. Ensure release code matches the remote Git branch exactly.
6. Separate server deployment from local Docker workflows.
7. Keep monitoring and rollback paths explicit.
8. Support a local-authoritative release mode when the user explicitly chooses to deploy the current local workspace.
9. For tool gateways, prefer one domain plus path prefixes over multiple throwaway subdomains.
10. Keep release changes scope-bounded; do not mix cleanup, experiments, or debug leftovers into deployment work.
11. Treat stateful local Docker volumes as data assets: preserve them by default and require an explicit user request before destructive cleanup.

## Desktop Dual-Repo Constitution

For all future `CheersAI-Desktop` work in this workspace, enforce the following hard rule:

1. All Desktop application code changes must be implemented in `/Users/FYP/Documents/WorkSpace/CheersAI/subproducts/CheersAI-Desktop/CheersAI-Desktop`.
2. `/Users/FYP/Documents/WorkSpace/CheersAI/subproducts/CheersAI-Desktop/CheersAI-Desktop-Uat` is a release mirror only; do not edit source files there.
3. Before a UAT rollout, `Desktop-Uat` may only sync from GitHub `origin/master`, then run the standard deploy flow.
4. If a bug is found in UAT, diagnose with logs and browser verification first; implement the actual fix back in the main Desktop repo, not in `Desktop-Uat`.

## Historical Failure Modes To Strictly Forbid

The following recurring failure modes are now prohibited in future ops and release tasks:

- **Over-cleaning during release**: do not bundle repo-wide style cleanup, import sorting, log-message rewrites, or unrelated refactors into a deployment task.
- **Debug-stage residue**: do not sync or publish temporary scripts, one-off repair helpers, screenshots, exported logs, or process notes unless they are explicitly approved as durable operator assets.
- **Requirement-boundary drift**: do not widen a release task into ad-hoc product refactoring, silent config redesign, or unrelated code hygiene work.
- **Automation-induced churn**: do not let formatter, linter, or code-action output redefine the release scope; keep only changes needed for the requested rollout, build health, or rollback safety.
- **State loss during local redeploy**: do not run destructive cleanup such as `docker compose down -v`, volume deletion, or project cleanup helpers like `make dev-clean` when the user expects existing local data, initialization state, or historical app data to survive.

If such changes are discovered, revert them before release, keep the deploy diff focused, and document any deferred ideas separately instead of shipping them opportunistically.

## Recommended Directory Layout

```text
scripts/
  <product>-uat/
    check-env.sh
    00-deploy-all.sh
    01-build.sh or 01-push-code.sh
    02-push.sh or 02-build-server.sh
    03-release.sh or 03-release-services.sh
    04-monitor.sh
    README.md
    deploy-*.sh
  deploy-docker-local/
    00-hot-redeploy.sh
    01-rollback.sh
    README.md
  infra/
    init-server.sh
```

For multi-tool gateways, extend the product directory with:

```text
scripts/
  tools-uat/
    env.sh
    check-env.sh
    00-deploy-all.sh
    01-build.sh
    02-push.sh
    03-release.sh
    04-monitor.sh
    bootstrap-<deploy-user>.sh
    prepare-<dependency>.sh
    deploy-tools.sh
    README.md
```

## Stage Responsibilities

### check-env.sh

Purpose:

- Validate source directory exists.
- Validate Git repository status.
- Validate required toolchain and SSH connectivity.
- Validate expected remote staging or application directories.

Requirements:

- Exit non-zero on blocking failures.
- Print summary with error and warning counts.
- Keep environment paths configurable via variables.

### 00-deploy-all.sh

Purpose:

- Provide the operator-facing one-click release entry.

Standard order:

```bash
check-env.sh
01-*.sh
02-*.sh
03-*.sh
04-*.sh
```

### 01/02 Build and Push Stages

Rules:

- If release artifacts are built locally, build before push.
- If code is synced first and built on the server, push before build.
- Use explicit stage numbering to reflect the real order for that product.
- If the user says the current local version is authoritative, allow a controlled bypass such as `RELEASE_SOURCE_MODE=local` and document the risk.

### 03 Release Stage

Purpose:

- Trigger remote service restart, remote deploy script, or release action.
- Keep rollback or service-management entrypoints explicit.

### 04 Monitor Stage

Purpose:

- Run post-release health checks.
- Attempt limited recovery only when appropriate.
- Exit non-zero if the system remains unhealthy.

## Git Sync Requirements

Before build or push:

1. Confirm the local path is a Git repository.
2. Confirm the working tree is clean.
3. Fetch remote changes for the current branch.
4. Reject release if local branch is ahead of origin.
5. Fast-forward pull if local branch is behind origin.
6. Print the commit SHA being released.

Exception:

- If the user explicitly requests deployment from the local working tree, keep the Git validation visible, but allow a deliberate override instead of forcing fast-forward sync.

Reference logic:

```bash
git -C "${repo}" rev-parse --git-dir
git -C "${repo}" diff --quiet
git -C "${repo}" diff --cached --quiet
git -C "${repo}" fetch --prune origin "${branch}"
git -C "${repo}" rev-list --count "origin/${branch}..HEAD"
git -C "${repo}" rev-list --count "HEAD..origin/${branch}"
git -C "${repo}" pull --ff-only origin "${branch}"
git -C "${repo}" rev-parse --short HEAD
```

## Preflight Checklist Template

Add one more preflight gate before release:

- confirm the deployment diff does not include broad cleanup, debug residue, or unrelated file churn
- confirm every changed file contributes directly to rollout, runtime health, monitoring, or rollback

Check at least:

- Source directory exists
- Git repository valid
- Current branch and commit visible
- Required source files exist
- Required commands exist
- SSH connectivity works
- Remote staging directory available
- Runtime dependencies exist, such as MongoDB, Redis, PostgreSQL, or Java
- Domain DNS and SSL readiness are checked
- Reverse-proxy read permissions are checked for static roots under `/home/<user>`
- For stateful local Docker stacks, confirm which bind-mounted or named volumes hold the active data before rebuild
- For local redeploys, confirm whether preserving existing initialization data is mandatory

## CheersAI-Desktop Local Docker Baseline

Use this product-specific baseline when the repository is `CheersAI-Desktop` and the task is to rebuild or publish the local Docker application on the same machine.

### Validated baseline

This baseline is now grounded in a verified local recovery path:

- Local Docker can be rebuilt without deleting stateful volumes.
- Local PostgreSQL can be repaired by restoring a valid Desktop business datasource.
- `http://localhost/signin` and `http://localhost/apps` load normally after service recovery.
- `http://localhost/console/api/account/profile` returning `401` is the expected unauthenticated state and confirms the API and Nginx chain are healthy.
- The Desktop application can use a restored business database with non-zero `apps` and `installed_apps`.

### Canonical entrypoints

- Primary full-stack compose file: `docker/docker-compose.yaml`
- Optional web-only override: `docker/docker-compose.local-full.yaml`
- Environment file: `docker/.env`
- Middleware-only developer stack: `docker/docker-compose.middleware.yaml`
- Local deploy skill root: `.trae/skills/release-ops-flow`

### Validated local environment paths

The following paths and files were validated during the local Docker acceptance run on this machine and should be treated as the current Desktop local-development baseline:

- Repository root: `/Users/FYP/Documents/WorkSpace/CheersAI/subproducts/CheersAI-Desktop/CheersAI-Desktop`
- Skill root after rename: `/Users/FYP/Documents/WorkSpace/CheersAI/subproducts/CheersAI-Desktop/CheersAI-Desktop/.trae/skills/Docker-release-ops`
- Primary skill document: `/Users/FYP/Documents/WorkSpace/CheersAI/subproducts/CheersAI-Desktop/CheersAI-Desktop/.trae/skills/Docker-release-ops/SKILL.md`
- Compose file: `/Users/FYP/Documents/WorkSpace/CheersAI/subproducts/CheersAI-Desktop/CheersAI-Desktop/docker/docker-compose.yaml`
- Optional local-full override: `/Users/FYP/Documents/WorkSpace/CheersAI/subproducts/CheersAI-Desktop/CheersAI-Desktop/docker/docker-compose.local-full.yaml`
- Middleware compose file: `/Users/FYP/Documents/WorkSpace/CheersAI/subproducts/CheersAI-Desktop/CheersAI-Desktop/docker/docker-compose.middleware.yaml`
- Active env file: `/Users/FYP/Documents/WorkSpace/CheersAI/subproducts/CheersAI-Desktop/CheersAI-Desktop/docker/.env`
- Active PostgreSQL bind mount root: `/Users/FYP/Documents/WorkSpace/CheersAI/subproducts/CheersAI-Desktop/CheersAI-Desktop/docker/volumes/db/data`
- Active PostgreSQL data directory: `/Users/FYP/Documents/WorkSpace/CheersAI/subproducts/CheersAI-Desktop/CheersAI-Desktop/docker/volumes/db/data/pgdata`
- Redis data directory: `/Users/FYP/Documents/WorkSpace/CheersAI/subproducts/CheersAI-Desktop/CheersAI-Desktop/docker/volumes/redis/data`
- App storage directory: `/Users/FYP/Documents/WorkSpace/CheersAI/subproducts/CheersAI-Desktop/CheersAI-Desktop/docker/volumes/app/storage`
- Latest validated PostgreSQL backup created during acceptance: `/Users/FYP/Documents/WorkSpace/CheersAI/subproducts/CheersAI-Desktop/CheersAI-Desktop/docker/volumes/db/data.backup-20260505-100510`
- Temporary local deploy log directory used in acceptance: `/tmp/docker-release-ops-logs`
- Temporary deploy audit file used in acceptance: `/tmp/docker-release-ops-logs/audit.log`
- Temporary remote import dump path used during data recovery: `/tmp/desktop-db-sync/desktop-uat.dump`

### Validated local env values

The currently verified Desktop local Docker runtime uses these `docker/.env` keys:

- `DB_TYPE=postgresql`
- `DB_HOST=db_postgres`
- `DB_PORT=5432`
- `DB_USERNAME=postgres`
- `DB_DATABASE=dify`
- `PGDATA=/var/lib/postgresql/data/pgdata`
- `POSTGRES_IMAGE=postgres:15-alpine`
- `API_MIGRATION_ENABLED=false`
- `WORKER_MIGRATION_ENABLED=false`
- `WORKER_BEAT_MIGRATION_ENABLED=false`

Rules:

- Read `DB_PASSWORD` from `docker/.env`; do not duplicate secrets into scripts or logs unless the operator explicitly asks.
- Keep `PGDATA` pointed to `/var/lib/postgresql/data/pgdata`; this path is required for the current bind-mounted Desktop business datasource.
- Treat `CERTBOT_EMAIL` and `CERTBOT_DOMAIN` warnings as non-blocking for local acceptance when HTTPS automation is not being exercised.

### Core deployment objective

When this skill is triggered for local Docker deployment, it must produce or follow a workflow that:

1. Builds and publishes `web`, `api`, `worker`, `worker_beat`, and `nginx` into the local Docker environment.
2. Preserves the active Desktop PostgreSQL, Redis, and storage data by default.
3. Runs pre-deploy and post-deploy health checks.
4. Verifies database connectivity and business-table counts.
5. Records structured logs and an operator audit trail.
6. Falls back to a stable local state when deployment or runtime validation fails.

### Dependency inventory

Required runtime and operator dependencies:

- Docker Desktop with Compose V2
- Local repository at `/Users/FYP/Documents/WorkSpace/CheersAI/subproducts/CheersAI-Desktop/CheersAI-Desktop`
- Compose services: `db_postgres`, `redis`, `sandbox`, `plugin_daemon`, `api`, `worker`, `worker_beat`, `web`, `nginx`
- Valid `docker/.env`
- Reachable local ports: `80`, `443`, `3000`, `5001`, `5003`, `5432`, `6379`, `8194`
- PostgreSQL client access inside the `db_postgres` container
- Enough Docker memory for `web` production image build

Optional but recommended:

- SSH access to UAT when local data recovery may require importing a verified remote business dump
- A local log directory such as `logs/deploy-docker-local/`

### Execution parameters

The local Docker deploy flow should support at least these parameters:

- `REPO_ROOT`: Desktop main repository root
- `COMPOSE_FILE`: defaults to `docker/docker-compose.yaml`
- `ENV_FILE`: defaults to `docker/.env`
- `DEPLOY_LOG_DIR`: defaults to `logs/deploy-docker-local`
- `DEPLOY_AUDIT_FILE`: defaults to `logs/deploy-docker-local/audit.log`
- `ROLLBACK_DB_DIR`: timestamped backup path under `docker/volumes/db/data`
- `HEALTH_RETRY_COUNT`: retry count for post-deploy checks
- `HEALTH_RETRY_INTERVAL`: retry interval in seconds
- `EXPECTED_MIN_DIFY_SETUPS`: defaults to `1` when the stack should remain initialized
- `EXPECTED_MIN_ACCOUNTS`: defaults to `1` when login history should survive
- `EXPECTED_MIN_TENANTS`: defaults to `1` when workspace state should survive
- `EXPECT_APPS_DATA`: `0` or `1`, used to require non-zero `apps` and `installed_apps`
- `RELEASE_SOURCE_MODE`: `git` or `local`

### Data safety rules

- Treat `docker/volumes/db/data` as the primary PostgreSQL data directory unless the operator proves the stack is using a different source.
- Treat `docker/volumes/redis/data` and `docker/volumes/app/storage` as persistent local state that should survive routine rebuilds.
- Before any risky local redeploy, back up the active PostgreSQL directory to a timestamped sibling such as `docker/volumes/db/data.backup-<timestamp>`.
- Do not use `make dev-clean` for local release or hot redeploy work. In this repository it deletes local database, redis, plugin, vector, and storage data.
- Do not use `docker compose down -v` unless the user explicitly requests data reset.
- If a remote business dump is imported for recovery, keep the previous local PGDATA backup until browser verification is complete.
- If temporary inspection containers or scratch databases are created during diagnosis, remove only those temporary assets after validation; do not remove the active `db_postgres` container or its data volume.

### Logging and audit requirements

Every local Docker deployment run should emit:

- A timestamped stage log, for example `logs/deploy-docker-local/2026-05-05-094400-deploy.log`
- A machine-readable audit line per stage, appended to `logs/deploy-docker-local/audit.log`
- The released Git branch and commit SHA
- The active compose file and env file path
- The detected PostgreSQL datasource root
- Pre-deploy business-table counts
- Post-deploy business-table counts
- Health-check results for `signin`, `apps`, API health, and database connectivity
- Rollback status if recovery was triggered

Recommended audit format:

```text
<timestamp> stage=<name> status=<ok|warn|fail> repo=<path> branch=<branch> sha=<sha> details="<summary>"
```

Validated acceptance log example on this machine:

```text
2026-05-05 10:04:56 stage=preflight status=start repo=/Users/FYP/Documents/WorkSpace/CheersAI/subproducts/CheersAI-Desktop/CheersAI-Desktop details='begin local docker acceptance'
2026-05-05 10:05:14 stage=backup status=ok backup=docker/volumes/db/data.backup-20260505-100510 details='postgres bind mount backup created'
2026-05-05 10:05:44 stage=deploy status=ok details='docker compose up -d --build api web worker worker_beat nginx succeeded'
```

### Pre-deploy checklist

Before any local Docker deployment, the skill should require the operator flow to validate:

- Repository exists and is the Desktop main repo, not `Desktop-Uat`
- Compose file exists
- `docker/.env` exists and points to the intended `DB_HOST`, `DB_PORT`, `DB_DATABASE`, `DB_USERNAME`, and `PGDATA`
- `docker compose ps` can inspect the current stack
- Active PostgreSQL datasource path is identified
- Current `dify_setups`, `accounts`, `tenants`, `apps`, and `installed_apps` counts are captured
- Current diff does not include unrelated cleanup or debug residue
- Docker daemon is reachable
- Disk space is sufficient for a new `web` build and PostgreSQL backup

Reference check:

```bash
docker compose -f docker/docker-compose.yaml ps
docker compose -f docker/docker-compose.yaml exec -T db_postgres \
  psql -U postgres -d dify -Atqc \
  "select count(*) from dify_setups;
   select count(*) from accounts;
   select count(*) from tenants;
   select count(*) from apps;
   select count(*) from installed_apps;"
```

### Standard execution stages

The reusable local Docker deployment flow should be structured as:

```text
check-env
01-preflight-and-backup
02-build-and-redeploy
03-health-verify
04-rollback-if-needed
05-audit-and-summary
```

### 01 Preflight and backup

Purpose:

- Capture current runtime state.
- Back up the active PostgreSQL directory.
- Record current service status and business-table counts.

Standard actions:

```bash
STAMP="$(date +%Y%m%d-%H%M%S)"
BACKUP_DIR="docker/volumes/db/data.backup-${STAMP}"
docker compose -f docker/docker-compose.yaml ps
cp -a docker/volumes/db/data "${BACKUP_DIR}"
```

If the active datasource is a named volume or a verified alternate path, record that explicitly in the audit log before continuing.

### 02 Build and redeploy

Purpose:

- Rebuild and restart local application services without deleting state.

Standard actions:

```bash
git -C "${repo}" fetch --prune origin "${branch}"
git -C "${repo}" checkout "${branch}"
git -C "${repo}" reset --hard "origin/${branch}"
docker compose -f docker/docker-compose.yaml up -d --build api web worker worker_beat nginx
docker compose -f docker/docker-compose.yaml ps
```

Rules:

- Prefer `up -d --build` over `down && up` so bind-mounted data directories remain attached.
- Do not stop `db_postgres`, `redis`, `sandbox`, or `plugin_daemon` unless diagnosis requires it.
- If the `web` build fails because Docker Desktop memory is exhausted, `docker compose stop api web worker worker_beat nginx`, then rerun `up -d --build`; do not delete volumes as a shortcut.
- If the user explicitly chooses `RELEASE_SOURCE_MODE=local`, skip Git fast-forward enforcement but still log the local SHA and dirty status.

### 03 Health verification

Purpose:

- Ensure the local Docker deployment is actually usable.

Minimum required checks after redeploy:

- `docker compose ps` shows `api`, `web`, `worker`, `worker_beat`, `nginx`, `db_postgres`, `redis`, `sandbox`, and `plugin_daemon` healthy or running as expected
- `http://localhost:5001/health` returns `200`
- `http://localhost/signin` loads instead of redirecting to `/install`
- `http://localhost/console/api/account/profile` returns either `200` or `401`, but not `500` or `502`
- `http://localhost/apps` returns HTML and does not fail at the gateway layer
- PostgreSQL business counts meet expectations
- If `EXPECT_APPS_DATA=1`, both `apps` and `installed_apps` are non-zero

Reference checks:

```bash
python3 - <<'PY'
import urllib.request
for url in [
    'http://localhost:5001/health',
    'http://localhost/signin',
    'http://localhost/console/api/account/profile',
    'http://localhost/apps',
]:
    try:
        with urllib.request.urlopen(url, timeout=15) as r:
            print(url, r.status, r.getheader('content-type'))
    except Exception as e:
        print(url, 'ERROR', e)
PY

docker compose -f docker/docker-compose.yaml exec -T db_postgres \
  psql -U postgres -d dify -Atqc \
  "select count(*) from dify_setups;
   select count(*) from accounts;
   select count(*) from tenants;
   select count(*) from apps;
   select count(*) from installed_apps;"
```

Validated pre-deploy business counts on this machine:

```text
dify_setups=1
accounts=13
tenants=12
apps=37
installed_apps=54
```

Browser acceptance is strongly recommended when a human-facing page must be confirmed:

- re-login if needed
- verify `/apps` does not stick on global loading
- verify cards are visible when restored `apps` data is expected
- verify the current workspace matches the restored app `tenant_id`

Validated browser acceptance result on this machine:

- Existing local session could enter `/apps` and open Agent details successfully.
- After logout, visiting `/apps` redirected to `/signin` as expected.
- `/signin` rendered the SSO login page normally.
- `/account/profile` returned `401` in unauthenticated state, which matched the expected health signal.

### 04 Rollback and error handling

Purpose:

- Recover to the last stable local state automatically when the new deployment is unhealthy.

Rollback triggers:

- `docker compose up -d --build` exits non-zero
- API health endpoint stays unhealthy after retries
- `account/profile` returns `500` or `502` after retries
- PostgreSQL business counts regress below the pre-deploy baseline unexpectedly
- Browser verification shows `/install` or a permanent global loading failure caused by the new deployment

Rollback strategy:

1. Stop only affected application services: `api`, `worker`, `worker_beat`, `web`, `nginx`
2. Restore the most recent PostgreSQL backup directory if the failure is datasource-related
3. Restart `db_postgres`
4. Restart `api`, `worker`, `worker_beat`, `web`, `nginx`
5. Re-run health verification
6. Record the rollback as `fail->rollback->recovered` or `fail->rollback->failed`

Reference rollback sequence:

```bash
docker compose -f docker/docker-compose.yaml stop api worker worker_beat web nginx
mv docker/volumes/db/data docker/volumes/db/data.failed-"${STAMP}"
cp -a "${BACKUP_DIR}" docker/volumes/db/data
docker compose -f docker/docker-compose.yaml up -d db_postgres
docker compose -f docker/docker-compose.yaml up -d api worker worker_beat web nginx
```

Error-handling rules:

- Stop immediately on irreversible schema or restore errors.
- Do not continue to browser acceptance if API health or PostgreSQL counts are already wrong.
- If `pg_restore` succeeds in a scratch database but not in the target business database, preserve both logs and do not overwrite the last good backup.
- If the API is healthy directly on `:5001` but `localhost` still returns `502`, restart `nginx`; stale upstream IP resolution is a known failure mode.

### 05 Remote data recovery path

Use this path only when local historical Desktop data exists but does not contain real `apps` rows.

Verified source of truth:

- UAT host: `desktop@121.41.195.46`
- Business database: `desktop`
- Verified UAT counts at time of discovery included non-zero `apps` and `installed_apps`.

Recommended recovery flow:

```bash
ssh desktop@121.41.195.46 \
  "sudo -n -u postgres pg_dump -d desktop --format=custom --no-owner --no-privileges" \
  > /tmp/desktop-db-sync/desktop-uat.dump

docker cp /tmp/desktop-db-sync/desktop-uat.dump docker-db_postgres-1:/tmp/desktop-uat.dump
docker compose -f docker/docker-compose.yaml exec -T db_postgres \
  pg_restore -U postgres -d dify --clean --if-exists --no-owner --no-privileges /tmp/desktop-uat.dump
```

Safety rules:

- First restore into a scratch database such as `desktoptmp` and validate `apps` counts before touching the active `dify` database.
- Preserve the pre-import local PGDATA backup until post-login verification succeeds.
- Treat temporary import files under `/tmp/desktop-db-sync` as operator artifacts; they may be deleted after acceptance if no longer needed.

### Post-deploy acceptance checks

Validate all of the following after deploy or recovery:

- `docker compose -f docker/docker-compose.yaml ps` shows `api`, `web`, `worker`, `worker_beat`, `nginx`, `db_postgres`, `redis`, `sandbox`, and `plugin_daemon` healthy or running as expected
- `http://localhost/signin` loads instead of redirecting to `/install`
- `http://localhost/console/api/account/profile` returns `200` or `401`, not `500` or `502`
- PostgreSQL business counts are non-zero when the environment is expected to stay initialized, for example `dify_setups`, `accounts`, and `tenants`
- If historical application data is expected, also validate `apps` and `installed_apps`
- If Desktop SSO shared workspaces depend on Redis `desktop:sso:group-tenant:*`, confirm the group hash still points to the intended shared tenant after rebuild
- If a user suddenly lands in an empty workspace while shared assets still exist, inspect Redis group mapping before changing code
- If the operator can log in, verify `/apps` renders real cards instead of an empty state

Validation standard:

- `Pass`: service health green, DB counts expected, browser can reach signin or app pages without gateway failure
- `Warn`: unauthenticated `401` on profile but all services are healthy and browser access is normal
- `Fail`: `500/502`, `/install`, broken DB counts, or restore/build failure without rollback success

Reference check:

```bash
docker exec docker-db_postgres-1 psql -U postgres -d dify -Atqc \
  "select count(*) from dify_setups;
   select count(*) from accounts;
   select count(*) from tenants;
   select count(*) from apps;
   select count(*) from installed_apps;"
```

### Redis group-to-tenant repair

Use this when a Desktop SSO user lands in the wrong workspace after local Docker rebuild and shared resources disappear even though database records still exist.

```bash
docker exec docker-redis-1 redis-cli --scan --pattern 'desktop:sso:group-tenant:*'
docker exec docker-redis-1 redis-cli get "<group-hash-key>"
docker exec docker-db_postgres-1 psql -U postgres -d dify -P pager=off -c \
  "select id,name,status from tenants where id in ('<candidate-tenant-id-1>','<candidate-tenant-id-2>');"
docker exec docker-redis-1 redis-cli set "<group-hash-key>" "<correct-shared-tenant-id>"
docker exec docker-db_postgres-1 psql -U postgres -d dify -c \
  "update tenant_account_joins
      set current = (tenant_id='<correct-shared-tenant-id>')
    where account_id='<account-id>';"
```

Repair notes:

- Prefer fixing the Redis group mapping before changing application code when the problem is isolated to a wrong shared-tenant target.
- Re-login the affected user after repair and verify `/apps` or `/datasets` before declaring success.
- If the latest source already contains SSO tag sync fixes, rebuild `api` and `web` as part of the same repair so runtime code and local source stay aligned.

### Troubleshooting signals

- If `http://localhost` or `http://localhost/signin` lands on `/install`, the local stack is attached to an empty or wrong database directory.
- If `/apps` shows an empty state but the database contains application rows, verify that the logged-in account's current workspace matches the `tenant_id` of those apps.
- If the database contains the expected apps but the wrong workspace is current, fix the workspace membership or current-tenant selection before changing application code.
- If `db_postgres` keeps trying `initdb` against a non-empty directory, verify that `.env` points `PGDATA` to the real subdirectory that contains `PG_VERSION`, commonly `/var/lib/postgresql/data/pgdata`.
- If direct API access on `http://localhost:5001` is healthy but `http://localhost/console/api/account/profile` still returns `502`, restart `nginx`; the reverse proxy may still point to a stale container IP.
- If every local historical PostgreSQL candidate has `apps=0`, classify the machine as lacking a valid local Desktop business backup and switch to the remote UAT export path instead.
- If a restored business database still produces an empty `/apps`, inspect Redis `desktop:sso:group-tenant:*` mapping and the current workspace before assuming the import failed.

### Common operator FAQ

Q: Which services must be rebuilt for a normal local Docker deployment?

- Rebuild `api`, `web`, `worker`, `worker_beat`, and `nginx`.
- Keep `db_postgres`, `redis`, `sandbox`, and `plugin_daemon` as persistent dependencies unless diagnosis requires targeted intervention.

Q: What proves the database connection is valid?

- `db_postgres` is healthy.
- `http://localhost:5001/health` is `200`.
- `account/profile` is `200` or `401`.
- PostgreSQL counts for `dify_setups`, `accounts`, and `tenants` are non-zero.

Q: When is rollback mandatory?

- When build or restore fails.
- When API or gateway health degrades after deploy.
- When expected business counts disappear.
- When the browser lands on `/install` unexpectedly.

Q: When can temporary invalid database containers be removed?

- Only after the active `db_postgres` container and the restored business database are verified healthy.
- Temporary inspection containers or scratch databases may be removed; the active `db_postgres` container must not be deleted.

## Cloud vs Local Docker Separation

Server-release scripts should stay inside product directories.

Local-only Docker scripts should move to:

```text
scripts/deploy-docker-local/
```

Typical local Docker scripts:

- hot redeploy
- image rollback
- local compose health validation

Rule:

- Never mix local Docker helper scripts with cloud UAT release scripts in the same product directory unless they are proxied intentionally.

## Gateway Pattern

Use a gateway pattern when several lightweight tools share one host:

- One public domain, many path prefixes, for example `/ts/`, `/survey/`, `/rm/`
- Static tools served directly by Nginx
- Dynamic tools proxied to loopback ports
- One operator-facing README and one monitoring entrypoint
- One deploy user and one application root such as `/home/cheersai/apps/tools`

When adopting this pattern, validate:

- Path-base compatibility in frontend builds
- Route fallback behavior for SPA assets
- Nginx worker permission to traverse parent directories
- Cloud-layer or ICP restrictions if Host-header testing differs from on-box testing

## Naming Conventions

- Directory: `<product>-uat`
- Preflight: `check-env.sh`
- Unified entry: `00-deploy-all.sh`
- Ordered stages: `01-*`, `02-*`, `03-*`, `04-*`
- Local Docker helpers: `00-hot-redeploy.sh`, `01-rollback.sh`

## Validation Checklist

- [ ] Script names reflect execution order
- [ ] README matches actual entrypoints
- [ ] Preflight exits correctly on blocking failures
- [ ] Build/push scripts enforce Git sync
- [ ] Release stage targets the correct remote path
- [ ] Monitor stage verifies health
- [ ] Local Docker scripts are isolated from server release scripts
- [ ] All shell scripts pass `bash -n`

## Output Template

When finishing a deployment-structure task, summarize with:

1. Product directories created or updated
2. One-click entrypoints added or changed
3. Preflight coverage added
4. Git-sync enforcement added
5. Local Docker separation result
6. Validation commands run
7. Remaining operational risks
