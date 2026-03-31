Write-Host "Checking Docker status..." -ForegroundColor Cyan
try {
    $dockerCheck = docker ps 2>&1
    if ($dockerCheck -match "error during connect" -or $dockerCheck -match "failed to connect") {
        Write-Host "WARNING: Docker Desktop is not running! Please start Docker Desktop first to bring up the database/Redis middleware." -ForegroundColor Red
        Write-Host "Continuing anyway, but backend services may fail without PostgreSQL/Redis." -ForegroundColor Yellow
        Start-Sleep -s 3
    }
} catch {
    Write-Host "Docker command failed. Is Docker installed?" -ForegroundColor Red
}

Write-Host "Starting CheersAI-Desktop Services..." -ForegroundColor Green

# 1. Start Docker Middleware
Write-Host "1. Launching Docker Middleware..." -ForegroundColor Yellow
Start-Process pwsh -ArgumentList "-NoExit", "-Command", "cd docker; if (!(Test-Path middleware.env)) { Copy-Item middleware.env.example middleware.env }; docker compose -f docker-compose.middleware.yaml --env-file middleware.env -p dify-middlewares-dev up -d; Write-Host 'Middleware started. Keep this running or close if finished.' -ForegroundColor Green"

# 2. Start API (Flask)
Write-Host "2. Launching Backend API (Flask on 5001)..." -ForegroundColor Yellow
Start-Process pwsh -ArgumentList "-NoExit", "-Command", "cd api; uv run flask db upgrade; uv run flask run --host 0.0.0.0 --port=5001 --debug"

# 3. Start Celery Worker
Write-Host "3. Launching Celery Worker..." -ForegroundColor Yellow
Start-Process pwsh -ArgumentList "-NoExit", "-Command", "cd api; uv run celery -A app.celery worker -P threads -c 2 --loglevel INFO -Q dataset,priority_dataset,priority_pipeline,pipeline,mail,ops_trace,app_deletion,plugin,workflow_storage,conversation,workflow,schedule_poller,schedule_executor,triggered_workflow_dispatcher,trigger_refresh_executor,retention"

# 4. Start Web Frontend
Write-Host "4. Launching Web Frontend (Next.js)..." -ForegroundColor Yellow
Start-Process pwsh -ArgumentList "-NoExit", "-Command", "cd web; pnpm dev:inspect"

# 5. Start Tauri Desktop Client
Write-Host "5. Launching Tauri Desktop App..." -ForegroundColor Yellow
Start-Process pwsh -ArgumentList "-NoExit", "-Command", "cd web; Write-Host 'Waiting 10s for Next.js to be ready on port 3000...'; Start-Sleep -s 10; pnpm dev:tauri"

Write-Host "All scripts have been executed. 5 new windows should pop up." -ForegroundColor Green
