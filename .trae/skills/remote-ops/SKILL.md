---
name: "remote-ops"
description: "Handles remote server operations including code sync, service build, and management using optimized scripts to prevent server overload. Invoke when user wants to deploy changes, restart services, or fix server issues."
---

# Remote Operations Skill

This skill manages remote server operations safely and efficiently by utilizing pre-configured scripts on the server. This avoids high CPU usage from direct interactive commands and ensures consistent deployment processes.

## Capabilities

1.  **Code Synchronization (`sync`)**: Pushes local code changes to the server.
2.  **Service Build (`build`)**: Triggers a safe build process on the server (backend dependencies, database migrations, frontend build).
3.  **Service Management (`manage`)**: Restarts or checks the status of services.
4.  **Full Deployment (`deploy`)**: Combines sync, build, and restart in one flow.

## Usage

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

## Recommended Workflow for Fixes

When applying a fix (e.g., frontend code change):

1.  **Edit**: Modify the code locally.
2.  **Sync**: Run `bash "/Users/FYP/Documents/WorkSpace/CheersAI/CheersAI - docs/技术/scripts/desktop-uat/01-push-code.sh"` to upload changes.
3.  **Build**: Trigger the remote build script via SSH with `nohup`.
4.  **Monitor**: Watch the log file until completion.
5.  **Verify**: Check the website.
6.  **Commit**: Commit changes to Git (optional but recommended).

## Configuration

- **Server IP**: `121.41.195.46`
- **Deploy User**: `desktop`
- **Privileged User**: `sso`
- **App Directory**: `/home/desktop/CheersAI-Desktop`
- **Log Directory**: `/home/desktop/logs`
- **API / Web / Plugin Ports**: `8080 / 3100 / 5002-5003`
- **Weaviate Ports**: `8081 / 50051`
