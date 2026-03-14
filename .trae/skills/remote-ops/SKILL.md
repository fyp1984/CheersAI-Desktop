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
./scripts/local_push.sh
```

**Note**: This script uses `rsync` to efficiently synchronize `api/`, `web/`, and `scripts/` directories.

### 2. Remote Build & Deploy

Use this to rebuild the application on the server. This is critical after code changes or dependency updates.

**Command (Run on Local Machine via SSH):**

```bash
ssh -t cheersai@62.234.210.100 "nohup /home/cheersai/CheersAI-Desktop/scripts/server_build.sh > /home/cheersai/logs/build_$(date +%Y%m%d_%H%M%S).log 2>&1 &"
```

38→**Why `nohup`?**
39→- Prevents the build process from being killed if the SSH connection times out (common during long builds).
40→- Redirects output to a log file for later inspection.
41→- **Note**: The build script will automatically detect non-interactive environments and skip service restart if sudo password is required. You may need to run the restart command manually.
42→
43→**Monitoring the Build:**

```bash
ssh -t cheersai@62.234.210.100 "tail -f /home/cheersai/logs/build_*.log"
```

### 3. Service Management (Restart/Status)

Use this to quickly restart services without rebuilding.

**Restart All Services:**

```bash
ssh -t cheersai@62.234.210.100 "sudo /home/cheersai/CheersAI-Desktop/scripts/server_manage.sh restart"
```

**Check Status:**

```bash
ssh -t cheersai@62.234.210.100 "sudo /home/cheersai/CheersAI-Desktop/scripts/server_manage.sh status"
```

## Recommended Workflow for Fixes

67→When applying a fix (e.g., frontend code change):
68→
69→1.  **Edit**: Modify the code locally.
70→2.  **Sync**: Run `./scripts/local_push.sh` to upload changes.
71→3.  **Build**: Trigger the remote build script via SSH with `nohup`.
72→4.  **Monitor**: Watch the log file until completion.
73→5.  **Verify**: Check the website.
74→6.  **Commit**: Commit changes to Git (optional but recommended).

## Configuration

- **Server IP**: `62.234.210.100`
- **User**: `cheersai`
- **App Directory**: `/home/cheersai/CheersAI-Desktop`
- **Log Directory**: `/home/cheersai/logs`
