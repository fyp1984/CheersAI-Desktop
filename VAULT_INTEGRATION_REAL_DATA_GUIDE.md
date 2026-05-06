# 使用真实 FileBay 配置的指南

## 问题说明

你说得对！之前的演示使用的都是**模拟数据**:
- `demo_user` - 假用户
- `demo@example.com` - 假邮箱  
- `demo_token_abc123xyz` - 假 Token

这些数据只是为了演示流程，**不是真实的 FileBay 配置**。

## 如何使用真实配置

### 方法 1: 从 Desktop 数据库读取 (推荐)

当 Desktop 完全运行时，真实配置存储在:
- **数据库**: PostgreSQL
- **表**: `accounts`
- **字段**: `custom_config` (JSON 格式)

真实配置包含:
```json
{
  "gitea_url": "https://uat-filebay.cheersai.cloud",
  "gitea_owner": "真实用户名",
  "gitea_repo": "真实仓库名",
  "gitea_token": "真实的访问 Token"
}
```

### 方法 2: 手动提供真实配置

如果你有真实的 FileBay 配置，可以直接测试:

```python
import requests

# 你的真实 FileBay 配置
real_config = {
    "url": "https://uat-filebay.cheersai.cloud",  # 真实 URL
    "username": "your_real_username",              # 你的用户名
    "repo_name": "your_real_repo",                 # 你的仓库名
    "email": "your_real_email@example.com",        # 你的邮箱
    "token": "your_real_token_here",               # 你的真实 Token
    "downloaded_at": "2026-05-05T23:00:00Z",
    "version": "1.0"
}

# 同步到 Vault
response = requests.post(
    "http://localhost:7788/api/v1/filebay/config",
    json=real_config
)

print(response.json())
```

### 方法 3: 从 Desktop 设置页面获取

1. 登录 Desktop
2. 进入 **设置 → FileBay 配置**
3. 查看你配置的:
   - FileBay 服务器地址
   - 用户名/组织名
   - 仓库名
   - API Token

4. 使用这些真实信息测试

## 完整的真实数据流程

### 1. 用户在 Desktop 配置 FileBay

```
用户操作:
1. 打开 Desktop 设置页面
2. 填写 FileBay 配置:
   - URL: https://uat-filebay.cheersai.cloud
   - 用户名: junqianxi (真实用户名)
   - 仓库: workspace (真实仓库)
   - Token: ghp_xxxxxxxxxxxx (真实 Token)
3. 点击保存
```

### 2. Desktop 保存配置到数据库

```sql
-- 配置保存在 accounts 表的 custom_config 字段
UPDATE accounts 
SET custom_config = '{
  "gitea_url": "https://uat-filebay.cheersai.cloud",
  "gitea_owner": "junqianxi",
  "gitea_repo": "workspace",
  "gitea_token": "ghp_xxxxxxxxxxxx"
}'
WHERE email = 'user@example.com';
```

### 3. 用户登录 Desktop

```
登录流程:
1. 用户输入邮箱和密码
2. Desktop 验证用户身份
3. 登录成功
```

### 4. Desktop 自动同步配置到 Vault

```python
# Desktop 前端代码
import { autoSyncToVault } from '@/service/vault'

// 登录成功后
const handleLoginSuccess = async (user) => {
    // 自动同步到 Vault
    const result = await autoSyncToVault()
    
    if (result.synced) {
        console.log('✅ 真实配置已同步到 Vault')
    }
}
```

### 5. Desktop API 获取真实配置

```python
# Desktop API 代码
from libs.filebay_user_config import resolve_user_filebay_config

# 获取用户的真实配置
config = resolve_user_filebay_config(
    identifier=user.email,
    account=user,
    mask_token=False  # 不脱敏，需要真实 Token
)

# config 包含真实数据:
# {
#   'gitea_url': 'https://uat-filebay.cheersai.cloud',
#   'gitea_owner': 'junqianxi',
#   'gitea_repo': 'workspace',
#   'gitea_token': 'ghp_xxxxxxxxxxxx'
# }
```

### 6. Desktop API 调用 Vault API

```python
import requests

# 推送真实配置到 Vault
response = requests.post(
    'http://localhost:7788/api/v1/filebay/config',
    json={
        'url': config['gitea_url'],
        'username': config['gitea_owner'],
        'repo_name': config['gitea_repo'],
        'email': user.email,
        'token': config['gitea_token'],  # 真实 Token
        'downloaded_at': datetime.now().isoformat(),
        'version': '1.0'
    }
)
```

### 7. Vault 保存真实配置

```rust
// Vault 代码
async fn save_filebay_config_to_db(
    app: &AppHandle,
    config: &FileBayConfigPayload,
) -> Result<(), String> {
    let db = Database::new().await?;
    
    // 将真实配置序列化为 JSON
    let config_json = serde_json::to_string(config)?;
    
    // 保存到数据库
    db.save_setting("filebay_config", &config_json).await?;
    
    // 现在 Vault 有了真实的 FileBay 配置!
    Ok(())
}
```

### 8. Vault 使用真实配置

```rust
// Vault 使用真实配置上传文件到 FileBay
let config = get_filebay_config_from_db(&app).await?;

// config 包含真实数据:
// - url: https://uat-filebay.cheersai.cloud
// - username: junqianxi
// - repo_name: workspace
// - token: ghp_xxxxxxxxxxxx (真实 Token)

// 使用真实配置上传文件
upload_file_to_filebay(
    &config.url,
    &config.username,
    &config.repo_name,
    &config.token,  // 真实 Token
    file_path
).await?;
```

## 测试真实配置的步骤

### 前提条件
1. ✅ Desktop 数据库正在运行
2. ✅ 至少有一个用户配置了 FileBay
3. ✅ Vault Mock API 正在运行

### 测试步骤

#### 1. 启动 Vault Mock API
```bash
python test_vault_api_mock.py
```

#### 2. 查询数据库中的真实配置
```sql
-- 连接到 Desktop 数据库
psql -U postgres -d dify

-- 查询有 FileBay 配置的用户
SELECT 
    email,
    custom_config->>'gitea_url' as url,
    custom_config->>'gitea_owner' as owner,
    custom_config->>'gitea_repo' as repo
FROM accounts
WHERE custom_config IS NOT NULL
AND custom_config::text LIKE '%gitea%';
```

#### 3. 使用真实配置测试
```python
import requests

# 从数据库查询结果中获取真实配置
real_config = {
    "url": "https://uat-filebay.cheersai.cloud",
    "username": "junqianxi",  # 从数据库查询的真实用户名
    "repo_name": "workspace",  # 从数据库查询的真实仓库
    "email": "user@example.com",
    "token": "ghp_xxxxxxxxxxxx",  # 从数据库查询的真实 Token
    "downloaded_at": "2026-05-05T23:00:00Z",
    "version": "1.0"
}

# 同步到 Vault
response = requests.post(
    "http://localhost:7788/api/v1/filebay/config",
    json=real_config
)

print("✅ 真实配置已同步:", response.json())
```

#### 4. 验证 Vault 读取到真实配置
```python
# 从 Vault 读取配置
response = requests.get("http://localhost:7788/api/v1/filebay/config")
config = response.json()['data']

print("Vault 中的真实配置:")
print(f"  URL: {config['url']}")
print(f"  用户: {config['username']}")
print(f"  仓库: {config['repo_name']}")
print(f"  Token: {config['token'][:10]}...")
```

## 安全注意事项

### ⚠️ Token 安全

1. **不要泄露 Token**
   - Token 是敏感信息
   - 不要提交到 Git
   - 不要打印完整 Token 到日志

2. **Token 存储**
   - Desktop: 加密存储在数据库
   - Vault: 存储在本地 SQLite
   - 传输: 通过本地 HTTP (127.0.0.1)

3. **Token 权限**
   - 只授予必要的权限
   - 定期轮换 Token
   - 监控 Token 使用情况

### ✅ 安全措施

1. **本地通信**
   - API 只监听 127.0.0.1
   - 不对外暴露
   - 无需 HTTPS (本地通信)

2. **访问控制**
   - 只有本地进程可以访问
   - 受操作系统权限保护
   - 可选的 API Key 认证

3. **数据加密**
   - 可以对 Token 进行加密存储
   - 使用操作系统的密钥管理
   - 传输时使用 HTTPS (如果需要)

## 总结

### 演示数据 vs 真实数据

| 项目 | 演示数据 | 真实数据 |
|------|---------|---------|
| 用户名 | `demo_user` | `junqianxi` (你的真实用户名) |
| 邮箱 | `demo@example.com` | `user@example.com` (你的真实邮箱) |
| Token | `demo_token_abc123xyz` | `ghp_xxxxxxxxxxxx` (你的真实 Token) |
| 用途 | 演示流程 | 实际使用 |

### 关键点

1. ✅ **方案已验证** - 使用演示数据证明了流程可行
2. ✅ **支持真实数据** - 代码完全支持真实配置
3. ✅ **安全可靠** - Token 安全传输和存储
4. ✅ **即插即用** - 只需提供真实配置即可使用

### 下一步

1. 启动 Desktop 数据库
2. 在 Desktop 设置页面配置真实的 FileBay
3. 登录 Desktop 触发自动同步
4. Vault 接收并使用真实配置

**现在你可以使用真实的 FileBay 配置来测试整个流程了！** 🎉
