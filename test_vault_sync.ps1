# 测试 Vault Bridge 配置同步
# 模拟 Desktop 登录后的配置同步过程

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Vault Bridge 配置同步测试" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 1. 检查 Vault Bridge 健康状态
Write-Host "1. 检查 Vault Bridge 服务..." -ForegroundColor Yellow
$healthResponse = curl http://localhost:8765/health 2>$null
if ($LASTEXITCODE -eq 0) {
    Write-Host "   ✓ Vault Bridge 运行正常" -ForegroundColor Green
    Write-Host "   响应: $healthResponse" -ForegroundColor Gray
} else {
    Write-Host "   ✗ Vault Bridge 未运行" -ForegroundColor Red
    Write-Host "   请先运行: .\start_vault_bridge.ps1" -ForegroundColor Yellow
    exit 1
}

Write-Host ""

# 2. 模拟配置同步
Write-Host "2. 模拟配置同步..." -ForegroundColor Yellow

$testConfig = @{
    user_id = "test_user_123"
    config = @{
        url = "https://filebay.example.com"
        username = "test_user"
        repoName = "workspace"
        email = "test@example.com"
        token = "ghp_test_token_1234567890"
    }
} | ConvertTo-Json -Depth 3

Write-Host "   发送配置数据..." -ForegroundColor Gray

$syncResponse = curl -X POST http://localhost:8765/vault/config/filebay `
    -H "Content-Type: application/json" `
    -d $testConfig 2>$null

if ($LASTEXITCODE -eq 0) {
    Write-Host "   ✓ 配置同步成功" -ForegroundColor Green
    Write-Host "   响应: $syncResponse" -ForegroundColor Gray
} else {
    Write-Host "   ✗ 配置同步失败" -ForegroundColor Red
    exit 1
}

Write-Host ""

# 3. 验证配置已保存
Write-Host "3. 验证配置已保存..." -ForegroundColor Yellow

$getResponse = curl http://localhost:8765/vault/config/filebay/test_user_123 2>$null

if ($LASTEXITCODE -eq 0) {
    Write-Host "   ✓ 配置读取成功" -ForegroundColor Green
    Write-Host "   配置内容:" -ForegroundColor Gray
    Write-Host "   $getResponse" -ForegroundColor Cyan
} else {
    Write-Host "   ✗ 配置读取失败" -ForegroundColor Red
    exit 1
}

Write-Host ""

# 4. 查看数据库
Write-Host "4. 查看数据库内容..." -ForegroundColor Yellow

$dbPath = "$env:USERPROFILE\.cheersai\vault.db"
if (Test-Path $dbPath) {
    Write-Host "   数据库位置: $dbPath" -ForegroundColor Gray
    
    $dbContent = sqlite3 $dbPath "SELECT user_id, email, username, repo_name, substr(token, 1, 20) || '...' as token FROM filebay_configs;" 2>$null
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "   ✓ 数据库查询成功" -ForegroundColor Green
        Write-Host "   数据库记录:" -ForegroundColor Gray
        Write-Host "   $dbContent" -ForegroundColor Cyan
    } else {
        Write-Host "   ⚠ 需要安装 sqlite3 才能查看数据库" -ForegroundColor Yellow
        Write-Host "   你可以手动打开数据库: $dbPath" -ForegroundColor Gray
    }
} else {
    Write-Host "   ✗ 数据库文件不存在" -ForegroundColor Red
}

Write-Host ""

# 5. 清理测试数据
Write-Host "5. 清理测试数据..." -ForegroundColor Yellow

$deleteResponse = curl -X DELETE http://localhost:8765/vault/config/filebay/test_user_123 2>$null

if ($LASTEXITCODE -eq 0) {
    Write-Host "   ✓ 测试数据已清理" -ForegroundColor Green
} else {
    Write-Host "   ⚠ 清理失败（可能已被删除）" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  测试完成！" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "下一步：" -ForegroundColor Yellow
Write-Host "1. 访问 http://localhost:3000/signin" -ForegroundColor White
Write-Host "2. 使用 Desktop SSO 登录" -ForegroundColor White
Write-Host "3. 打开浏览器开发者工具 (F12)" -ForegroundColor White
Write-Host "4. 查看 Console 日志，搜索 [Vault Bridge]" -ForegroundColor White
Write-Host "5. 登录成功后，配置会自动同步到 Vault 数据库" -ForegroundColor White
Write-Host ""
