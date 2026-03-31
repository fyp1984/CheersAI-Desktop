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

Check at least:

- Source directory exists
- Git repository valid
- Current branch and commit visible
- Required source files exist
- Required commands exist
- SSH connectivity works
- Remote staging directory available

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
