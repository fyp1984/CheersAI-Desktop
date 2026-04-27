---
name: "remote-ops"
description: "Handles remote server operations including code sync, service build, restart, and UAT rollout. Invoke when user asks to deploy changes, restart services, fix server issues, or says '应用发布UAT'."
---

# Remote Operations Skill

This skill manages remote server operations safely and efficiently by utilizing pre-configured scripts on the server. This avoids high CPU usage from direct interactive commands and ensures consistent deployment processes.

## Capabilities

1.  **Code Synchronization (`sync`)**: Pushes local code changes to the server.
2.  **Service Build (`build`)**: Triggers a safe build process on the server (backend dependencies, database migrations, frontend build).
3.  **Service Management (`manage`)**: Restarts or checks the status of services.
4.  **Full Deployment (`deploy`)**: Combines sync, build, and restart in one flow.
5.  **Bootstrap (`bootstrap`)**: Initializes deploy users, runtime directories, and one-time dependencies.
6.  **Gateway Rollout (`gateway`)**: Publishes multiple tools under one shared domain and path-prefix layout.

## Usage

This skill should prefer standardized scripts under `CheersAI - docs/技术/scripts/<product>-uat` instead of ad-hoc SSH command sequences.

## CheersAI Desktop UAT Canonical Flow

When the user says `应用发布UAT`, default to this exact Desktop release flow unless the user explicitly requests a different source branch or a local-authoritative release:

1. Use repo: `/Users/FYP/Documents/WorkSpace/CheersAI/subproducts/CheersAI-Desktop/CheersAI-Desktop-Uat`
2. Confirm the repo is clean before changing branches; if it is dirty, stop and ask instead of forcing reset or overwrite
3. Run:

```bash
git checkout master
git pull --ff-only origin master
git rev-parse --short HEAD
```

4. Release with the standard one-click script:

```bash
PLUGIN_DAEMON_UPLOAD=no bash "/Users/FYP/Documents/WorkSpace/CheersAI/CheersAI - docs/技术/scripts/desktop-uat/00-deploy-all.sh"
```

5. Verify runtime after deployment:

```bash
ssh desktop@121.41.195.46 "systemctl show cheersai-api -p ExecMainStartTimestamp -p ActiveState -p SubState; systemctl show cheersai-web -p ExecMainStartTimestamp -p ActiveState -p SubState"
ssh desktop@121.41.195.46 "curl -I -s https://uat-desktop.cheersai.cloud/signin/ | head -n 5"
ssh desktop@121.41.195.46 "curl -I -s https://uat-desktop.cheersai.cloud/apps/ | head -n 5"
```

6. Run browser regression after release. At minimum verify:
- sign-in page loads
- SSO login works for `user_01 / 2026@CheersAI`
- SSO login works for `C_Admin / 2026@CheersAI1`
- `/apps` loads
- `/account` loads
- `FileBay 设置` opens from settings
- `/audit-logs` behavior matches role permissions

7. Final response must state:
- released Git commit SHA
- deploy script result
- core service health result
- browser regression pass/fail items
- any remaining production-impacting issues

## Historical Failure Modes To Strictly Forbid

The following recurring failure modes are now prohibited in future remote-ops execution:

- **Over-cleaning during ops**: do not piggyback formatting, import-order cleanup, logging rewrites, or unrelated refactors onto a deployment or restart task.
- **Debug-stage residue**: do not push temporary debug scripts, one-time fix tools, local notes, copied outputs, or ad-hoc helper files to remote environments unless they are explicitly approved as durable ops assets.
- **Requirement-boundary drift**: do not expand a remote fix into unrelated code cleanup, config redesign, or side-feature work while handling an operational request.
- **Automation-induced churn**: do not treat linter, formatter, or code-action rewrites as a reason to enlarge the sync set; only ship files required for the requested operational outcome.

When these patterns appear, stop widening the scope, restore focus to the requested fix or release, and leave optional follow-up work in a separate branch or documented backlog.

### 1. Sync Code (Local -> Remote)

Use this when you have made local code changes and need to update the server.

```bash
bash "/Users/FYP/Documents/WorkSpace/CheersAI/CheersAI - docs/技术/scripts/desktop-uat/01-push-code.sh"
```

**Note**: This flow uses `rsync` to synchronize `api/`, `web/`, root lock files, and deployment scripts to the UAT host. Set `PLUGIN_DAEMON_UPLOAD=yes` when you need to refresh the plugin daemon binary.

### 2. Remote Build & Deploy

Use this to rebuild the application on the server. This is critical after code changes or dependency updates.

**Command (Run on Local Machine via SSH):**

```bash
ssh -t desktop@121.41.195.46 "nohup /home/desktop/CheersAI-Desktop/scripts/server_build.sh > /home/desktop/logs/build_$(date +%Y%m%d_%H%M%S).log 2>&1 &"
```

**Why `nohup`?**
- Prevents the build process from being killed if the SSH connection times out (common during long builds).
- Redirects output to a log file for later inspection.
- **Note**: The build script will automatically detect non-interactive environments and skip service restart if sudo password is required. You may need to run the restart command manually.

**Monitoring the Build:**

```bash
ssh -t desktop@121.41.195.46 "tail -f /home/desktop/logs/build_*.log"
```

### 3. Service Management (Restart/Status)

Use this to quickly restart services without rebuilding.

**Restart All Services:**

```bash
ssh -t sso@121.41.195.46 "sudo /home/desktop/CheersAI-Desktop/scripts/server_manage.sh restart"
```

**Check Status:**

```bash
ssh -t sso@121.41.195.46 "sudo /home/desktop/CheersAI-Desktop/scripts/server_manage.sh status"
```

### 4. Multi-Tool Gateway Deployment

Use this when several lightweight products share one gateway domain.

Reference layout:

```text
/home/cheersai/apps/tools/current
  gateway/
  ts/
  survey/
  rm/
```

Reference workflow:

```bash
bash "/Users/FYP/Documents/WorkSpace/CheersAI/CheersAI - docs/技术/scripts/tools-uat/check-env.sh"
ALLOW_DIRTY_BUILD=1 RELEASE_SOURCE_MODE=local bash "/Users/FYP/Documents/WorkSpace/CheersAI/CheersAI - docs/技术/scripts/tools-uat/00-deploy-all.sh"
```

Reference bootstrap:

```bash
scp "/Users/FYP/Documents/WorkSpace/CheersAI/CheersAI - docs/技术/scripts/tools-uat/bootstrap-cheersai-user.sh" sso@121.41.195.46:/tmp/
ssh -t sso@121.41.195.46 "sudo bash /tmp/bootstrap-cheersai-user.sh"

scp "/Users/FYP/Documents/WorkSpace/CheersAI/CheersAI - docs/技术/scripts/tools-uat/prepare-survey-mongo.sh" sso@121.41.195.46:/tmp/
ssh -t sso@121.41.195.46 "sudo bash /tmp/prepare-survey-mongo.sh"
```

Rules:

- Dynamic services stay on loopback ports, for example `127.0.0.1:18188`
- Static services are served by Nginx aliases
- Prefer `cheersai` as the deploy user for shared tools
- Keep sensitive runtime config in `/home/cheersai/apps/tools/config`
- Validate both app status and Nginx permission to read the static release tree

## Recommended Workflow for Fixes

Before `sync`, review the outgoing file list and remove anything that exists only because of formatting tools, temporary diagnosis, or unrelated cleanup. The remote environment should receive the smallest change set that can achieve the requested operational goal.

When applying a fix (e.g., frontend code change):

1.  **Edit**: Modify the code locally.
2.  **Sync**: Run `bash "/Users/FYP/Documents/WorkSpace/CheersAI/CheersAI - docs/技术/scripts/desktop-uat/01-push-code.sh"` to upload changes.
3.  **Build**: Trigger the remote build script via SSH with `nohup`.
4.  **Monitor**: Watch the log file until completion.
5.  **Verify**: Check the website.
6.  **Commit**: Commit changes to Git (optional but recommended).

For gateway deployments, extend verification with:

1. `curl -I -H 'Host: <domain>' http://127.0.0.1/<path>/`
2. `systemctl is-active <service>`
3. `nginx -t`
4. HTML keyword checks for branding and page entrypoints
5. Static asset checks such as logo or favicon URLs

## Configuration

- **Server IP**: `121.41.195.46`
- **Deploy User**: `desktop`
- **Privileged User**: `sso`
- **App Directory**: `/home/desktop/CheersAI-Desktop`
- **Log Directory**: `/home/desktop/logs`
- **API / Web / Plugin Ports**: `8080 / 3100 / 5002-5003`
- **Weaviate Ports**: `8081 / 50051`

## Tools Gateway Example

- **Server IP**: `121.41.195.46`
- **Deploy User**: `cheersai`
- **Bootstrap User**: `sso`
- **App Directory**: `/home/cheersai/apps/tools`
- **Config Directory**: `/home/cheersai/apps/tools/config`
- **Release Roots**: `/home/cheersai/release/staging/tools`, `/home/cheersai/release/releases/tools`
- **Gateway Domain**: `tools.cheersai.cloud`
- **Path Prefixes**: `/ts/`, `/survey/`, `/rm/`
- **Survey Port**: `18188`
- **Survey Dependency**: MongoDB on `127.0.0.1:27017`
