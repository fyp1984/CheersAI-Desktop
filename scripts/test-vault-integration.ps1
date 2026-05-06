# Vault 集成测试脚本 (PowerShell)
# 用于快速测试 Desktop 与 Vault 的集成

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Vault 集成测试" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 配置
$VaultApiUrl = "http://localhost:7788"
$DesktopApiUrl = "http://localhost:5001"

# 测试 1: Vault 健康检查
Write-Host "测试 1: Vault 健康检查" -ForegroundColor Yellow
Write-Host "----------------------------------------"

try {
    $response = Invoke-RestMethod -Uri "$VaultApiUrl/api/v1/health" -Method Get -TimeoutSec 3
    
    if ($response.success) {
        Write-Host "✅ Vault API 可用" -ForegroundColor Green
        Write-Host "   消息: $($response.message)" -ForegroundColor Gray
    } else {
        Write-Host "❌ Vault API 返回错误" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "❌ 无法连接到 Vault API ($VaultApiUrl)" -ForegroundColor Red
    Write-Host "   请确保 Vault 应用正在运行" -ForegroundColor Yellow
    exit 1
}

Write-Host ""

# 测试 2: 保存配置
Write-Host "测试 2: 保存 FileBay 配置" -ForegroundColor Yellow
Write-Host "----------------------------------------"

$testConfig = @{
    url = "https://uat-filebay.cheersai.cloud"
    username = "test_user"
    repo_name = "workspace"
    email = "test@example.com"
    token = "test_token_123456"
    downloaded_at = "2024-01-01T00:00:00Z"
    version = "1.0"
} | ConvertTo-Json

try {
    $response = Invoke-RestMethod -Uri "$VaultApiUrl/api/v1/filebay/config" -Method Post -Body $testConfig -ContentType "application/json" -TimeoutSec 10
    
    if ($response.success) {
        Write-Host "✅ 配置保存成功" -ForegroundColor Green
        Write-Host "   URL: $($response.data.url)" -ForegroundColor Gray
        Write-Host "   Username: $($response.data.username)" -ForegroundColor Gray
        Write-Host "   Repo: $($response.data.repo_name)" -ForegroundColor Gray
    } else {
        Write-Host "❌ 配置保存失败: $($response.message)" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "❌ 保存配置失败: $_" -ForegroundColor Red
    exit 1
}

Write-Host ""

# 测试 3: 获取配置
Write-Host "测试 3: 获取 FileBay 配置" -ForegroundColor Yellow
Write-Host "----------------------------------------"

try {
    $response = Invoke-RestMethod -Uri "$VaultApiUrl/api/v1/filebay/config" -Method Get -TimeoutSec 10
    
    if ($response.success -and $response.data) {
        Write-Host "✅ 配置获取成功" -ForegroundColor Green
        Write-Host "   URL: $($response.data.url)" -ForegroundColor Gray
        Write-Host "   Username: $($response.data.username)" -ForegroundColor Gray
        Write-Host "   Repo: $($response.data.repo_name)" -ForegroundColor Gray
        Write-Host "   Email: $($response.data.email)" -ForegroundColor Gray
    } else {
        Write-Host "❌ 未找到配置" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "❌ 获取配置失败: $_" -ForegroundColor Red
    exit 1
}

Write-Host ""

# 测试 4: Desktop 健康检查
Write-Host "测试 4: Desktop Vault 健康检查接口" -ForegroundColor Yellow
Write-Host "----------------------------------------"

try {
    $response = Invoke-RestMethod -Uri "$DesktopApiUrl/console/api/vault/health" -Method Get -TimeoutSec 10
    
    Write-Host "✅ Desktop API 可用" -ForegroundColor Green
    
    if ($response.available) {
        Write-Host "   Vault 状态: 可用" -ForegroundColor Green
    } else {
        Write-Host "   Vault 状态: 不可用" -ForegroundColor Yellow
    }
    
    Write-Host "   消息: $($response.message)" -ForegroundColor Gray
} catch {
    Write-Host "⚠️  无法连接到 Desktop API ($DesktopApiUrl)" -ForegroundColor Yellow
    Write-Host "   请确保 Desktop API 正在运行" -ForegroundColor Gray
}

Write-Host ""

# 测试 5: 删除配置
Write-Host "测试 5: 删除 FileBay 配置" -ForegroundColor Yellow
Write-Host "----------------------------------------"

try {
    $response = Invoke-RestMethod -Uri "$VaultApiUrl/api/v1/filebay/config" -Method Delete -TimeoutSec 10
    
    if ($response.success) {
        Write-Host "✅ 配置删除成功" -ForegroundColor Green
    } else {
        Write-Host "❌ 配置删除失败: $($response.message)" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "❌ 删除配置失败: $_" -ForegroundColor Red
    exit 1
}

Write-Host ""

# 总结
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  测试完成" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "🎉 所有测试通过!" -ForegroundColor Green
Write-Host ""
Write-Host "下一步:" -ForegroundColor Yellow
Write-Host "  1. 在 Desktop 登录测试自动同步" -ForegroundColor Gray
Write-Host "  2. 在设置页面测试手动同步" -ForegroundColor Gray
Write-Host "  3. 检查 Vault 数据库中的配置" -ForegroundColor Gray
Write-Host ""
