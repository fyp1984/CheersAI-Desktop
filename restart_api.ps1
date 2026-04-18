# Restart API Server Script
# This script stops the current API server and restarts it

Write-Host "Stopping API server..." -ForegroundColor Yellow

# Find and stop the API process (listening on port 5001)
$apiProcess = Get-NetTCPConnection -LocalPort 5001 -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess
if ($apiProcess) {
    Stop-Process -Id $apiProcess -Force
    Write-Host "API server stopped (PID: $apiProcess)" -ForegroundColor Green
    Start-Sleep -Seconds 2
} else {
    Write-Host "No API server found on port 5001" -ForegroundColor Yellow
}

Write-Host "Starting API server..." -ForegroundColor Yellow
Write-Host "Please run the following command manually:" -ForegroundColor Cyan
Write-Host ""
Write-Host "cd api" -ForegroundColor White
Write-Host "flask run --host=0.0.0.0 --port=5001 --debug" -ForegroundColor White
Write-Host ""
Write-Host "Or use: make api-start" -ForegroundColor White
