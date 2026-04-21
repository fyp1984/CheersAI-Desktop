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

## Standard Validation Flow

### 1. Preflight

- Check `docker/.env`
- Check running containers with `docker compose ps`
- Confirm `localhost` pages return `200`
- Confirm nginx routes `/api/nexus/beta-applications/apply` correctly

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

## Deliverables

When finishing a task with this skill, provide:

1. Local Docker status
2. UAT endpoint configuration summary
3. End-to-end flow result
4. Any broken hop in the chain
5. Exact fix applied
6. Remaining acceptance risks
