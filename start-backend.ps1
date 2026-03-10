# CheersAI 后端启动脚本
# 使用方法: .\start-backend.ps1

Write-Host "正在启动 CheersAI 后端服务..." -ForegroundColor Green

# 切换到 API 目录
Set-Location -Path "$PSScriptRoot\api"

# 检查 .env 文件
if (-not (Test-Path ".env")) {
    Write-Host "警告: .env 文件不存在，请先配置环境变量" -ForegroundColor Yellow
    Write-Host "你可以复制 .env.example 并重命名为 .env" -ForegroundColor Yellow
}

# 运行数据库迁移
Write-Host "`n正在运行数据库迁移..." -ForegroundColor Cyan
python -m uv run flask db upgrade

# 启动 Flask 开发服务器
Write-Host "`n正在启动 Flask 开发服务器..." -ForegroundColor Cyan
Write-Host "后端 API 地址: http://localhost:5001" -ForegroundColor Green
Write-Host "按 Ctrl+C 停止服务器`n" -ForegroundColor Yellow

python -m uv run flask run --host 0.0.0.0 --port=5001 --debug
