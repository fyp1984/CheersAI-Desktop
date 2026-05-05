---
name: "desktop-local-uat-debug"
description: "Standardizes local Desktop Docker debugging against UAT Nexus, SSO, and FileBay. Invoke when validating localhost signup, approval, SSO login, or UAT data flow."
---

# Desktop Local UAT Debug

This skill standardizes local debugging and acceptance for `http://localhost` when the local Desktop stack must use UAT Nexus, UAT SSO, and UAT FileBay as the real backend chain.

## When to Invoke

Invoke this skill when:

- The user asks to debug or validate local Desktop against UAT services.
- The task involves `localhost` signup, SSO login, or approval flow.
- You need to verify that local submission writes into UAT Nexus.
- You need to confirm UAT Nexus approval triggers UAT SSO and UAT FileBay provisioning.
- You need to deploy the Desktop repo into local Docker while keeping server-side dependencies on UAT.

Do not invoke when:

- The task is only about UAT server deployment without local `localhost`.
- The task is only about frontend styling or non-integration UI work.

## Core Rule

Local Desktop debugging is valid only if this real chain is preserved:

1. User submits from local `http://localhost/signup/`
2. Request reaches UAT Nexus
3. UAT Nexus approval activates the user
4. UAT Nexus provisions UAT SSO and UAT FileBay
5. User logs into local Desktop through UAT SSO

Never replace this with a local-only mock, local database shortcut, or local fallback write path.

Additional repository rule:

1. Local Desktop code fixes must be implemented in `/Users/FYP/Documents/WorkSpace/CheersAI/subproducts/CheersAI-Desktop/CheersAI-Desktop`.
2. Do not patch `/Users/FYP/Documents/WorkSpace/CheersAI/subproducts/CheersAI-Desktop/CheersAI-Desktop-Uat` during debugging; use it only for GitHub `origin/master` sync and UAT release verification.

## Required Local Configuration

Validate these before testing:

- `NEXT_PUBLIC_DESKTOP_SSO_LOGIN_URL` points to `https://uat-sso.cheersai.cloud`
- `NEXUS_API_BASE_URL` points to `https://uat-nexus.cheersai.cloud`
- `FILEBAY_BASE_URL` points to `https://uat-filebay.cheersai.cloud`
- `SSO_PROVISION_*` values target the UAT SSO application and owner
- `NGINX_WEB_UPSTREAM` points to containerized `web:3000` for full local Docker mode
- Local nginx keeps the exact route for `/api/nexus/beta-applications/apply`

## Local Docker Expectations

For local full-Docker acceptance:

- `api`, `worker`, `worker_beat`, `web`, and `nginx` run in Docker
- `web` must not depend on host `3001`
- If local production build is too heavy, use a verified local cached production image for `web`
- After recreate, verify `/signin`, `/signup`, and `/apps` all return `200`
- Rebuild with `docker compose -f docker/docker-compose.yaml up -d --build api web worker worker_beat nginx`
- Preserve existing local data by default; do not use `docker compose down -v` or `make dev-clean` unless the user explicitly asks to reset the environment

## Local Data Preservation

When the local Docker stack has already been initialized or contains historical app data:

- Back up `docker/volumes/db/data` before any risky data switch or recovery action
- Keep `docker/volumes/redis/data` and `docker/volumes/app/storage` intact during normal rebuilds
- Treat `/install` after redeploy as evidence that the stack is attached to an empty or wrong database source, not as proof that code deploy succeeded
- Treat `/apps` empty state with non-zero `apps` rows as a workspace-context issue before assuming a frontend bug

## Data Source Scan Order

When local Docker starts but the user lands on `/install`, or login succeeds but `/apps` cannot show historical agents, do not assume the latest bind-mounted PostgreSQL directory is the real business source.

Use this exact scan order:

1. Read the runtime datasource from the running `api` container:
   - `DB_HOST`
   - `DB_PORT`
   - `DB_DATABASE`
   - `DB_USERNAME`
   - `PGDATA`
2. Query the currently connected PostgreSQL and record:
   - `count(*) from dify_setups`
   - `count(*) from accounts`
   - `count(*) from tenants`
   - `count(*) from apps`
   - `count(*) from installed_apps`
3. Enumerate all local PostgreSQL candidates on the machine:
   - bind-mounted directories such as `docker/volumes/db/data`
   - sibling historical directories such as `bak/docker/volumes/db/data`
   - historical project directories such as other local Dify/Desktop repos
   - Docker named volumes such as `*_postgres_data`
4. For every PostgreSQL candidate, identify its major version from `PG_VERSION` before mounting it:
   - PostgreSQL 15 data must be inspected with a PostgreSQL 15 container
   - PostgreSQL 16 data must be inspected with a PostgreSQL 16 container
5. A candidate is considered a valid local Desktop business source only if all checks pass:
   - the database is initialized: `dify_setups > 0`
   - it contains Desktop/Dify business tables: `accounts`, `tenants`, `apps`, `installed_apps`
   - it contains historical app data: `apps > 0` or `installed_apps > 0`
   - after binding the stack to that source, local login reaches `/apps`
6. If a candidate is initialized but `apps = 0`, treat it as an incomplete source, not the final answer.
7. If a candidate contains non-Desktop schemas such as `nexus` and has no Dify business tables, classify it as another product's database and exclude it.
8. If no candidate passes the business-data check, conclude that the machine currently has no valid local Desktop business datasource and that a restore/import step is required before Docker acceptance can succeed.

## Current Known Local Cases

The following patterns have already been observed locally and should be recognized quickly:

- `docker/volumes/db/data` can contain a migrated but effectively empty Dify database:
  - `dify_setups = 0`
  - `accounts > 0`
  - `apps = 0`
  - this source will drive Desktop into `/install`
- `bak/docker/volumes/db/data` or other historical PG15 directories can contain an initialized Dify database with users but still no app data:
  - `dify_setups > 0`
  - `apps = 0`
  - this source is closer to valid than the current empty bind mount, but still cannot satisfy the "show published agents" requirement
- Docker named volume `docker_postgres_data` can be a PostgreSQL 16 historical volume for another product:
  - if inspected with a PostgreSQL 15 container, it will fail to start due to version mismatch
  - if inspected with the matching PostgreSQL 16 container and only exposes `cheersai` / `nexus` tables instead of Dify tables, it is not the Desktop datasource
- Docker named volume `cheersaidesktop_postgres_data` can be an old initialized Dify database with no app records:
  - usable for login history checks
  - not sufficient for validating published-agent visibility

## Switching Rules

When the currently mounted datasource is wrong:

- Do not use `docker compose down -v`
- Do not overwrite a candidate source before proving it contains valid business data
- Prefer temporary read-only style verification first:
  - clone the candidate data directory or volume to a temporary inspection container
  - verify version, database names, business tables, and row counts
- After a candidate is proven valid, then update the local Docker datasource binding
- If the only discovered valid business source is a Docker named volume with a different PostgreSQL major version than the current compose file, align the PostgreSQL image major version before switching the stack to that source
- If no candidate has `apps > 0`, stop treating the issue as "wrong current binding only" and classify it as "missing local business backup"

## Standard Validation Flow

### 1. Preflight

- Check `docker/.env`
- Check running containers with `docker compose ps`
- Confirm `localhost` pages return `200`
- Confirm nginx routes `/api/nexus/beta-applications/apply` correctly
- If the environment is expected to remain initialized, verify `dify_setups`, `accounts`, and `tenants` in PostgreSQL before rebuild
- If historical apps are expected, verify `apps` and `installed_apps` counts before and after rebuild
- If `/install` appears, immediately perform the full datasource scan order above instead of rebuilding repeatedly against the same bind mount
- If a named volume candidate uses a different PostgreSQL major version than compose, inspect it with a matching temporary container before any switch

### 2. Submission Validation

- Submit a fresh email from local `/signup`
- Verify the record appears in UAT Nexus search results
- Confirm initial user status is `inactive`

### 3. Approval Validation

- Approve or activate through UAT Nexus UI or controlled backend endpoint
- Confirm user status becomes `active`

### 4. Provision Validation

- Check UAT SSO user exists
- Check default role matches expected policy
- Check password reset path works if needed
- Check UAT FileBay user exists
- Check expected repo or org resources exist according to current mode

### 5. Login Validation

- Log in from local `/signin` via UAT SSO
- Confirm access lands on `/apps`
- Validate only the expected member permissions are visible

## Permission Policy

Current business rule:

- Ordinary beta users must not have app creation ability
- App and agent configuration is handled by team administrators

When testing member users:

- Successful login is expected
- Visibility of workspace content is expected
- Missing “create app” entry is not a bug if the role is `desktop_team_member`

## Common Failure Patterns

- Signup succeeds locally but record is missing in UAT Nexus:
  local proxy or nginx route is wrong
- Nexus activation succeeds but SSO/FileBay records are missing:
  provisioning config or downstream credentials are wrong
- Local login fails but UAT SSO user exists:
  check OAuth redirect, client ID/secret, and localhost callback chain
- `/signin` or `/apps` return `502`:
  check local `web` container health and nginx upstream target
- `/signin` redirects to `/install` after rebuild:
  current Docker stack is attached to an empty database or the wrong restored data directory
- `/apps` shows no app cards but PostgreSQL contains app rows:
  check the logged-in account's current workspace against the app `tenant_id`
- The current bind-mounted PostgreSQL looks healthy but `dify_setups = 0` and `apps = 0`:
  this is a structurally valid but business-empty Dify source, not the historical Desktop business database
- A historical named volume fails under the current PostgreSQL image:
  check `PG_VERSION`; the volume may require a higher PostgreSQL major version than the compose file currently uses
- A historical PostgreSQL candidate only contains `nexus` or other non-Dify schemas:
  exclude it from Desktop datasource candidates even if it is initialized and queryable
- Every discovered local candidate has `apps = 0`:
  the machine currently lacks a valid local Desktop business source and needs backup restore or data import before agent visibility can be validated

## Deliverables

When finishing a task with this skill, provide:

1. Local Docker status
2. UAT endpoint configuration summary
3. End-to-end flow result
4. Any broken hop in the chain
5. Exact fix applied
6. Remaining acceptance risks
7. Datasource scan matrix:
   - candidate path or volume
   - PostgreSQL major version
   - database names
   - `dify_setups/accounts/tenants/apps/installed_apps` counts
   - final classification: empty Dify source / non-Desktop source / valid business source / restore required
