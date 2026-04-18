# FileBay 用户配置流程说明

## 配置存储位置

用户的 FileBay/Gitea 配置存储在数据库的 `accounts` 表的 `custom_config` 字段中（JSON 格式）。

### 配置结构

```json
{
  "gitea_url": "https://uat-filebay.cheersai.cloud",
  "gitea_owner": "junqianxi",
  "gitea_repo": "CheersAI-Desktop",
  "gitea_token": "your_gitea_token_here"
}
```

## API 调用流程

### 1. 前端获取配置

前端通过 `/console/api/gitea/config` 获取当前用户的 FileBay 配置。

**请求：**
```
GET /console/api/gitea/config
Headers:
  Cookie: session_id=xxx
```

**响应：**
```json
{
  "gitea_url": "https://uat-filebay.cheersai.cloud",
  "gitea_owner": "junqianxi",
  "gitea_repo": "CheersAI-Desktop",
  "gitea_token": "abc****xyz"  // 已脱敏
}
```

### 2. Console API 处理逻辑

`/console/api/gitea/config` 的处理流程：

1. 获取当前登录用户的 email
2. 调用本地企业 API：`http://localhost:5001/inner/api/enterprise/gitea/config?email={user_email}`
3. 如果企业 API 失败，直接查询数据库的 `account.custom_config_dict`
4. 如果都没有配置，回退到环境变量
5. 返回配置（token 已脱敏）

### 3. 企业 API 处理逻辑

`/inner/api/enterprise/gitea/config` 的处理流程：

1. 接收 `email` 查询参数
2. 从数据库查询该用户的 Account 记录
3. 读取 `account.custom_config_dict`
4. 如果找到 `gitea_url` 配置，返回用户配置
5. 否则回退到环境变量
6. 返回配置（token 未脱敏，用于后端间通信）

## 配置优先级

1. **用户数据库配置** (`account.custom_config_dict`) - 最高优先级
2. **环境变量配置** (`.env` 文件) - 回退方案

## 如何为用户设置 FileBay 配置

### 方法 1：通过 Python 脚本

```python
from extensions.ext_database import db
from models.account import Account
from app import create_app

app = create_app()

with app.app_context():
    email = '103456686@qq.com'
    account = db.session.query(Account).filter_by(email=email).first()
    
    if account:
        # 使用 custom_config_dict 属性（自动处理 JSON 序列化）
        config = account.custom_config_dict or {}
        config.update({
            'gitea_url': 'https://uat-filebay.cheersai.cloud',
            'gitea_owner': 'junqianxi',
            'gitea_repo': 'CheersAI-Desktop',
            'gitea_token': 'your_token_here'
        })
        account.custom_config_dict = config
        db.session.commit()
        print('配置已保存')
```

### 方法 2：通过 SQL

```sql
UPDATE accounts 
SET custom_config = '{"gitea_url":"https://uat-filebay.cheersai.cloud","gitea_owner":"junqianxi","gitea_repo":"CheersAI-Desktop","gitea_token":"your_token_here"}'
WHERE email = '103456686@qq.com';
```

## 测试配置

### 1. 测试企业 API

```bash
curl "http://localhost:5001/inner/api/enterprise/gitea/config?email=103456686@qq.com"
```

**预期响应：**
```json
{
  "gitea_url": "https://uat-filebay.cheersai.cloud",
  "gitea_owner": "junqianxi",
  "gitea_repo": "CheersAI-Desktop",
  "gitea_token": "your_token_here"
}
```

### 2. 测试 Console API（需要登录）

在浏览器中登录后，打开开发者工具 Console：

```javascript
fetch('/console/api/gitea/config', {
  credentials: 'include'
}).then(r => r.json()).then(console.log)
```

**预期响应：**
```json
{
  "gitea_url": "https://uat-filebay.cheersai.cloud",
  "gitea_owner": "junqianxi",
  "gitea_repo": "CheersAI-Desktop",
  "gitea_token": "your****here"
}
```

## 文件选择器使用流程

1. 用户登录系统
2. 打开对话页面，点击文件上传按钮
3. 选择"从 FileBay 选择"
4. 文件选择器调用 `/console/api/gitea/config` 获取配置
5. 使用获取的配置（owner/repo）显示文件列表
6. 用户选择文件后，通过 `/console/api/gitea/files/{path}` 下载文件内容

## 相关文件

- **企业 API**: `api/controllers/inner_api/gitea.py`
- **Console API**: `api/controllers/console/gitea_api/gitea_config.py`
- **文件 API**: `api/controllers/console/gitea_api/gitea_files.py`
- **前端组件**: `web/app/components/base/sandbox-file-picker/index.tsx`
- **Account 模型**: `api/models/account.py`

## 注意事项

1. **Token 安全**：
   - Console API 返回的 token 已脱敏（用于前端显示）
   - 企业 API 返回的 token 未脱敏（用于后端间通信）
   - 前端不应该存储或显示完整的 token

2. **配置更新**：
   - 目前没有前端界面来更新用户的 FileBay 配置
   - 需要通过数据库或脚本手动设置
   - 未来可以添加用户设置页面

3. **环境变量回退**：
   - 如果用户没有配置，系统会使用 `.env` 中的默认配置
   - 这对于开发和测试很有用

## 修改记录

- 2026-04-17: 修改企业 API 和 Console API，从 `custom_config_dict` 读取配置
- 2026-04-17: 修改 Console API 使用本地企业 API 而不是外部 tunnel URL
