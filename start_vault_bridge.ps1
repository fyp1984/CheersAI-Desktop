# 启动 Vault Bridge 服务
# 用于 Desktop 登录后同步 FileBay 配置到脱敏系统

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Vault Bridge Service Starter" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 检查 Python 是否安装
$pythonCmd = Get-Command python -ErrorAction SilentlyContinue
if (-not $pythonCmd) {
    Write-Host "错误: 未找到 Python，请先安装 Python 3.10+" -ForegroundColor Red
    exit 1
}

Write-Host "Python 版本:" -ForegroundColor Green
python --version
Write-Host ""

# 进入 API 目录
$apiDir = Join-Path $PSScriptRoot "api"
if (-not (Test-Path $apiDir)) {
    Write-Host "错误: 未找到 api 目录" -ForegroundColor Red
    exit 1
}

Set-Location $apiDir

# 检查虚拟环境
$venvPath = ".venv"
if (Test-Path $venvPath) {
    Write-Host "激活虚拟环境..." -ForegroundColor Yellow
    & "$venvPath\Scripts\Activate.ps1"
} else {
    Write-Host "警告: 未找到虚拟环境，使用全局 Python" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "启动 Vault Bridge 服务..." -ForegroundColor Green
Write-Host "监听地址: http://127.0.0.1:8765" -ForegroundColor Cyan
Write-Host "数据库位置: ~/.cheersai/vault.db" -ForegroundColor Cyan
Write-Host ""
Write-Host "按 Ctrl+C 停止服务" -ForegroundColor Yellow
Write-Host ""

# 启动服务
python start_vault_bridge.py

# 如果服务异常退出
if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "Vault Bridge 服务异常退出" -ForegroundColor Red
    exit $LASTEXITCODE
}
