# CheersAI Tauri 开发模式启动脚本

Write-Host "🚀 启动 CheersAI Tauri 开发环境...`n" -ForegroundColor Green

# 检查数据库服务是否运行
Write-Host "📦 检查数据库服务..." -ForegroundColor Cyan
$containers = docker ps --format "{{.Names}}" | Select-String -Pattern "dify-postgres|dify-redis|dify-plugin-daemon"
if ($containers.Count -lt 3) {
    Write-Host "⚠️  数据库服务未运行，正在启动..." -ForegroundColor Yellow
    & .\start-database.ps1
    Start-Sleep -Seconds 5
}

Write-Host "✅ 数据库服务已就绪`n" -ForegroundColor Green

# 启动后端 API（后台运行）
Write-Host "🔧 启动后端 API..." -ForegroundColor Cyan
$backendJob = Start-Job -ScriptBlock {
    Set-Location $using:PWD
    & .\start-backend.ps1
}
Write-Host "✅ 后端 API 正在启动（Job ID: $($backendJob.Id)）`n" -ForegroundColor Green

# 等待后端启动
Write-Host "⏳ 等待后端 API 启动..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

# 启动前端开发服务器（后台运行）
Write-Host "🎨 启动前端开发服务器..." -ForegroundColor Cyan
$frontendJob = Start-Job -ScriptBlock {
    Set-Location "$using:PWD\web"
    pnpm dev
}
Write-Host "✅ 前端开发服务器正在启动（Job ID: $($frontendJob.Id)）`n" -ForegroundColor Green

# 等待前端启动
Write-Host "⏳ 等待前端服务器启动..." -ForegroundColor Yellow
Start-Sleep -Seconds 15

# 启动 Tauri
Write-Host "🖥️  启动 Tauri 桌面应用...`n" -ForegroundColor Cyan
Set-Location web
pnpm run dev:tauri

# 清理
Write-Host "`n🛑 正在停止服务..." -ForegroundColor Yellow
Stop-Job -Job $backendJob, $frontendJob
Remove-Job -Job $backendJob, $frontendJob
Write-Host "✅ 已停止所有服务" -ForegroundColor Green
