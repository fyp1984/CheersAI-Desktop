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

### Canonical entrypoints

- Primary full-stack compose file: `docker/docker-compose.yaml`
- Optional web-only override: `docker/docker-compose.local-full.yaml`
- Environment file: `docker/.env`
- Middleware-only developer stack: `docker/docker-compose.middleware.yaml`

### Data safety rules

- Treat `docker/volumes/db/data` as the primary PostgreSQL data directory unless the operator proves the stack is using a different source.
- Treat `docker/volumes/redis/data` and `docker/volumes/app/storage` as persistent local state that should survive routine rebuilds.
- Before any risky local redeploy, back up the active PostgreSQL directory to a timestamped sibling such as `docker/volumes/db/data.backup-<timestamp>`.
- Do not use `make dev-clean` for local release or hot redeploy work. In this repository it deletes local database, redis, plugin, vector, and storage data.
- Do not use `docker compose down -v` unless the user explicitly requests data reset.

### Safe rebuild sequence

Use this order when the user wants the latest local code rebuilt without deleting data:

```bash
git -C "${repo}" fetch --prune origin "${branch}"
git -C "${repo}" checkout "${branch}"
git -C "${repo}" reset --hard "origin/${branch}"
docker compose -f docker/docker-compose.yaml up -d --build api web worker worker_beat nginx
docker compose -f docker/docker-compose.yaml ps
```

Prefer `up -d --build` over `down && up` so bind-mounted data directories remain attached. If the `web` image build fails because Docker Desktop memory is exhausted, stop containers first with `docker compose stop`, then rebuild. Do not delete volumes as a shortcut for build recovery.

### Post-deploy acceptance checks

Validate all of the following after rebuild:

- `docker compose -f docker/docker-compose.yaml ps` shows `api`, `web`, `worker`, `worker_beat`, `nginx`, `db_postgres`, `redis`, `sandbox`, and `plugin_daemon` healthy or running as expected
- `http://localhost/signin` loads instead of redirecting to `/install`
- PostgreSQL business counts are non-zero when the environment is expected to stay initialized, for example `dify_setups`, `accounts`, and `tenants`
- If historical application data is expected, also validate `apps` and `installed_apps`
- If Desktop SSO shared workspaces depend on Redis `desktop:sso:group-tenant:*`, confirm the group hash still points to the intended shared tenant after rebuild
- If a user suddenly lands in an empty workspace while shared assets still exist, inspect Redis group mapping before changing code

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
