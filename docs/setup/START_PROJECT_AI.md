# AI-Friendly Startup

This project now includes a PowerShell one-click startup script that an AI agent can run directly.

## Recommended command

From the project root:

```powershell
pwsh -File .\scripts\start-all.ps1
```

Or with an absolute path:

```powershell
D:\PowerShell\7\pwsh.exe -File E:\CheersAI-Desktop\scripts\start-all.ps1
```

## What the script does

`E:\CheersAI-Desktop\scripts\start-all.ps1` will try to:

1. Start Docker Desktop if the Docker engine is not ready
2. Run `docker compose -f E:\CheersAI-Desktop\docker\docker-compose.middleware.yaml up -d`
3. Start Ollama if port `11434` is not listening
4. Start the API if port `5001` is not listening
5. Start the web app if port `3000` is not listening
6. Print the final URLs and log file locations

The script is designed to be re-runnable. If a service is already up, it skips that step.

## Optional flags

You can skip parts of startup if needed:

```powershell
pwsh -File .\scripts\start-all.ps1 -SkipOllama
pwsh -File .\scripts\start-all.ps1 -SkipMiddleware
pwsh -File .\scripts\start-all.ps1 -SkipApi -SkipWeb
```

Available switches:

- `-SkipDockerDesktop`
- `-SkipMiddleware`
- `-SkipOllama`
- `-SkipApi`
- `-SkipWeb`

## Default ports

- Web: `3000`
- API: `5001`
- Plugin daemon: `5002`
- Ollama: `11434`
- PostgreSQL: `5432`

## Logs

The script writes logs to:

- API: `E:\CheersAI-Desktop\api\logs\manual-api.out.log`
- Web: `E:\CheersAI-Desktop\web\dev.out.log`
- Ollama: `E:\CheersAI-Desktop\storage\ollama\ollama.out.log`

## Notes for this machine

This machine has had both `docker-*` and `dify-*` containers present at the same time.
The startup script uses a best-effort strategy: it tries to bring up the expected middleware,
but it does not delete or reset existing containers.

If Docker reports a port conflict, check current containers first:

```powershell
docker ps -a --format "table {{.Names}}`t{{.Status}}`t{{.Ports}}"
```

## If you want AI to run it

You can tell the AI:

- "Run `pwsh -File E:\CheersAI-Desktop\scripts\start-all.ps1`"
- "Start only web and api"
- "Start everything except Ollama"

That gives the AI a single PowerShell entry point instead of a `.bat` file.
