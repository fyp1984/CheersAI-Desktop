# FileBay 自动配置测试指南

## 快速测试

### 1. Mock 测试（推荐）

不需要实际 FileBay 连接，测试代码逻辑。

```bash
cd api
python test_auto_provision_mock.py
```

**预期输出**:
```
Username Generation            ✓ PASSED
Auto Provision (Mock)          ✓ PASSED
Enterprise API Logic           ✓ PASSED
```

### 2. 数据库验证

查看测试账号的配置：

```sql
-- 查看所有有配置的账号
SELECT 
    email, 
    name,
    JSON_EXTRACT(custom_config, '$.gitea_url') as gitea_url,
    JSON_EXTRACT(custom_config, '$.gitea_owner') as gitea_owner,
    JSON_EXTRACT(custom_config, '$.gitea_repo') as gitea_repo
FROM accounts 
WHERE custom_config IS NOT NULL 
  AND custom_config != '{}';

-- 查看特定账号
SELECT email, custom_config 
FROM accounts 
WHERE email = 'test@example.com';
```

### 3. Enterprise API 测试

#### 获取配置（不自动配置）

```bash
curl "http://localhost:5001/inner/api/enterprise/gitea/config?email=test@example.com"
```

#### 获取配置（自动配置）

```bash
curl "http://localhost:5001/inner/api/enterprise/gitea/config?email=test@example.com&auto_provision=true"
```

#### 预期响应

```json
{
    "gitea_url": "https://uat-filebay.cheersai.cloud",
    "gitea_owner": "test_example_com_abc123",
    "gitea_repo": "workspace",
    "gitea_token": "a1b2c3d4e5f6..."
}
```

## 完整测试流程

### 步骤 1: 准备环境

确保 Flask 后端正在运行：

```bash
cd api
python app.py
```

### 步骤 2: 创建测试账号

使用 SSO 登录或直接在数据库创建：

```python
from models.account import Account
from extensions.ext_database import db

account = Account(
    name="Test User",
    email="test_flow@example.com",
)
db.session.add(account)
db.session.commit()
```

### 步骤 3: 清空现有配置

```python
account = db.session.query(Account).filter_by(email="test_flow@example.com").first()
account.custom_config_dict = {}
db.session.commit()
```

### 步骤 4: 触发自动配置

#### 方式 A: SSO 登录

1. 访问 SSO 登录页面
2. 使用测试账号登录
3. 查看日志确认自动配置执行

#### 方式 B: API 调用

```bash
curl "http://localhost:5001/inner/api/enterprise/gitea/config?email=test_flow@example.com&auto_provision=true"
```

### 步骤 5: 验证配置

```python
from models.account import Account
from extensions.ext_database import db

account = db.session.query(Account).filter_by(email="test_flow@example.com").first()
config = account.custom_config_dict

print(f"URL: {config.get('gitea_url')}")
print(f"Owner: {config.get('gitea_owner')}")
print(f"Repo: {config.get('gitea_repo')}")
print(f"Token: {config.get('gitea_token')[:20]}...")
```

### 步骤 6: 测试文件选择器

1. 登录 Desktop
2. 打开文件选择器
3. 验证可以浏览和选择文件

## 日志检查

### SSO 登录日志

```
[SSO Auto Provision] Triggering FileBay auto-provision for test@example.com
[FileBay Auto Provision] Starting for test@example.com
[FileBay Auto Provision] Generated username: test_example_com_abc123
[FileBay Auto Provision] Created user test_example_com_abc123
[FileBay Auto Provision] Created repo test_example_com_abc123/workspace
[FileBay Auto Provision] Generated token for test_example_com_abc123
[FileBay Auto Provision] Initialized masked directory
[FileBay Auto Provision] Completed for test@example.com
[SSO Auto Provision] FileBay provisioned for test@example.com
```

### Enterprise API 日志

```
[Enterprise Gitea Config] Getting config for user: test@example.com (auto_provision=true)
[Enterprise Gitea Config] No Gitea config found in custom_config for test@example.com
[Enterprise Gitea Config] Triggering auto-provision for test@example.com
[FileBay Auto Provision] Starting for test@example.com
...
[Enterprise Gitea Config] Auto-provision completed for test@example.com
```

## 故障排查

### 问题 1: SSL 错误

**症状**:
```
SSLError: [SSL: UNEXPECTED_EOF_WHILE_READING] EOF occurred in violation of protocol
```

**解决**:
在 `.env` 中设置：
```env
BETA_PROVISION_SSL_VERIFY=false
```

### 问题 2: 自动配置未触发

**检查**:
1. 查看 SSO 登录日志
2. 确认用户没有现有配置
3. 检查环境变量配置

**验证环境变量**:
```python
import os
print(f"FILEBAY_BASE_URL: {os.getenv('FILEBAY_BASE_URL')}")
print(f"FILEBAY_ADMIN_USERNAME: {os.getenv('FILEBAY_ADMIN_USERNAME')}")
print(f"FILEBAY_ADMIN_PASSWORD: {'***' if os.getenv('FILEBAY_ADMIN_PASSWORD') else 'NOT SET'}")
```

### 问题 3: Token 无效

**检查**:
1. 验证 Token 格式（应该是长字符串）
2. 测试 Token 权限
3. 重新生成 Token

**测试 Token**:
```bash
curl -H "Authorization: token YOUR_TOKEN" \
  "https://uat-filebay.cheersai.cloud/api/v1/user"
```

### 问题 4: 配置未保存

**检查**:
```python
from models.account import Account
from extensions.ext_database import db

account = db.session.query(Account).filter_by(email="test@example.com").first()
print(f"custom_config: {account.custom_config}")
print(f"custom_config_dict: {account.custom_config_dict}")
```

## 性能测试

### 测试自动配置耗时

```python
import time
from services.filebay_auto_provision_service import FileBayAutoProvisionService

service = FileBayAutoProvisionService()

start_time = time.time()
config = service.auto_provision("perf_test@example.com")
end_time = time.time()

print(f"Auto-provision took {end_time - start_time:.2f} seconds")
```

**预期耗时**: 2-5 秒（取决于网络和 FileBay 响应速度）

## 批量测试

### 批量创建测试账号

```python
from models.account import Account
from extensions.ext_database import db
from services.filebay_auto_provision_service import FileBayAutoProvisionService

service = FileBayAutoProvisionService()

for i in range(10):
    email = f"batch_test_{i}@example.com"
    
    # 创建账号
    account = Account(name=f"Batch Test {i}", email=email)
    db.session.add(account)
    db.session.commit()
    
    # 自动配置
    try:
        config = service.auto_provision(email)
        account.custom_config_dict = config
        db.session.commit()
        print(f"✓ {email}")
    except Exception as e:
        print(f"✗ {email}: {e}")
```

## 清理测试数据

### 删除测试账号

```sql
-- 查看测试账号
SELECT id, email, name 
FROM accounts 
WHERE email LIKE '%test%' 
   OR email LIKE '%example.com%';

-- 删除测试账号（谨慎操作！）
DELETE FROM accounts 
WHERE email LIKE '%test%' 
  AND email LIKE '%example.com%';
```

### 清空配置

```python
from models.account import Account
from extensions.ext_database import db

# 清空所有测试账号的配置
accounts = db.session.query(Account).filter(
    Account.email.like('%test%')
).all()

for account in accounts:
    account.custom_config_dict = {}
    db.session.add(account)

db.session.commit()
print(f"Cleared config for {len(accounts)} accounts")
```

## 监控和告警

### 成功率监控

```python
from models.account import Account
from extensions.ext_database import db

# 统计有配置的账号数
total_accounts = db.session.query(Account).count()
configured_accounts = db.session.query(Account).filter(
    Account.custom_config.isnot(None),
    Account.custom_config != '{}'
).count()

success_rate = (configured_accounts / total_accounts * 100) if total_accounts > 0 else 0
print(f"Configuration success rate: {success_rate:.2f}%")
print(f"Configured: {configured_accounts}/{total_accounts}")
```

### 错误日志查询

```bash
# 查看自动配置相关日志
grep "FileBay Auto Provision" logs/app.log | tail -50

# 查看错误日志
grep "ERROR.*FileBay" logs/app.log | tail -20
```

## 测试检查清单

- [ ] Mock 测试通过
- [ ] 用户名生成正确
- [ ] 配置保存到数据库
- [ ] Enterprise API 返回正确
- [ ] SSO 登录触发自动配置
- [ ] 文件选择器可以使用
- [ ] 日志记录完整
- [ ] 错误处理正确
- [ ] 性能符合预期
- [ ] 清理测试数据

## 相关命令

```bash
# 运行 Mock 测试
python test_auto_provision_mock.py

# 运行完整测试（需要 FileBay 连接）
python test_complete_auto_provision.py

# 查看日志
tail -f logs/app.log | grep "FileBay"

# 重启 Flask
pkill -f "python app.py"
python app.py

# 查看数据库
sqlite3 storage/dify.db
# 或
psql -U postgres -d dify
```

## 总结

本测试指南提供了完整的测试方法和故障排查步骤。建议按照以下顺序进行测试：

1. ✓ 运行 Mock 测试（验证代码逻辑）
2. ✓ 测试 Enterprise API（验证 API 功能）
3. ✓ 测试 SSO 登录（验证完整流程）
4. ✓ 测试文件选择器（验证用户体验）

---

**文档版本**: 1.0  
**更新时间**: 2026-04-17
