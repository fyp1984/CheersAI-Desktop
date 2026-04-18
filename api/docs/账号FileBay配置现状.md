# 账号 FileBay 配置现状

生成时间: 2026-04-17

## 账号统计

- 总账号数: 7
- 已配置 FileBay: 3 (42.9%)
- 未配置 FileBay: 4 (57.1%)

## 真实用户账号 (2个)

### 1. 1@qq.com (Admin)

- **ID**: 68393244-8477-4691-9f70-8a7dec8090dc
- **姓名**: admin
- **状态**: active
- **角色**: owner
- **创建时间**: 2026-04-16 07:52:29
- **最后登录**: 2026-04-16 07:52:30
- **工作空间**: admin's Workspace
- **FileBay 配置**: ✗ 未配置

### 2. 103456686@qq.com

- **ID**: f3056f10-d994-4c2b-8acd-c02c49c4e5d7
- **姓名**: 103456686_qq_com_nzvhyt
- **状态**: active
- **角色**: admin
- **创建时间**: 2026-04-16 09:06:04
- **最后登录**: 2026-04-16 09:06:07
- **工作空间**: 103456686_qq_com_nzvhyt's Workspace
- **FileBay 配置**: ✗ 未配置

## 测试账号 (5个)

### 已配置 (3个)

#### 1. mock_test@example.com

- **FileBay URL**: https://uat-filebay.cheersai.cloud
- **Owner**: mock_test_example_com_df138f
- **Repo**: workspace
- **Token**: mock_token...01vwx234yz (Mock 数据)

#### 2. existing_config@example.com

- **FileBay URL**: https://test.example.com
- **Owner**: test_user
- **Repo**: test_repo
- **Token**: **** (Mock 数据)

#### 3. no_config@example.com

- **FileBay URL**: https://new.example.com
- **Owner**: new_user
- **Repo**: new_repo
- **Token**: **** (Mock 数据)

### 未配置 (2个)

- test_api_auto@example.com
- test_auto_provision@example.com

## 按域名统计

| 域名 | 总数 | 已配置 | 未配置 |
|------|------|--------|--------|
| example.com | 5 | 3 | 2 |
| qq.com | 2 | 0 | 2 |

## FileBay 配置服务实现状态

### 已完成 ✓

1. **FileBay Config Service** (`api/services/filebay_config_service.py`)
   - 3-tier 配置解析策略:
     1. Account.custom_config_dict（优先）
     2. 查找 FileBay 已有用户并动态生成 Token
     3. 全局环境变量（fallback）
   - 支持通过 email、username、user_id 查找
   - 动态 Token 生成功能
   - SSL 解决方案（虽然当前无法连接 UAT）

2. **Enterprise API** (`api/controllers/inner_api/gitea.py`)
   - GET/POST 支持
   - 自动标识符解析
   - 返回未脱敏的 Token（后端通信）

3. **环境配置**
   - `FILEBAY_BASE_URL=https://uat-filebay.cheersai.cloud`
   - `FILEBAY_ADMIN_USERNAME=admin`
   - `FILEBAY_ADMIN_PASSWORD=3DIS9cqlR8@E`
   - `FILEBAY_DEFAULT_REPO=workspace`
   - `BETA_PROVISION_SSL_VERIFY=false`
   - `BETA_PROVISION_HTTP_TIMEOUT=30`

### 阻塞问题 ✗

**Python 无法连接 UAT FileBay (SSL EOF 错误)**

```
SSLEOFError: [SSL: UNEXPECTED_EOF_WHILE_READING] EOF occurred in violation of protocol
```

- 所有 HTTPS 请求都失败
- Python 3.13 + OpenSSL 与 UAT FileBay TLS 配置不兼容
- Rust 实现可以连接（使用 `danger_accept_invalid_certs`）
- 已尝试多种 SSL 解决方案，均无效

详见: `FileBay_SSL问题最终诊断.md`

## 下一步行动

### 优先级 1: 解决 SSL 问题

1. 联系 FileBay 团队，请求修复 UAT 环境的 TLS 配置
2. 测试生产环境的 FileBay 是否有相同问题
3. 考虑部署 HTTP 代理或 Rust 微服务

### 优先级 2: 配置真实用户

一旦 SSL 问题解决，为真实用户配置 FileBay:

```bash
# 测试配置服务
python test_filebay_config_service.py

# 查看配置结果
python check_accounts_filebay.py check 1@qq.com
python check_accounts_filebay.py check 103456686@qq.com
```

### 优先级 3: 前端集成

更新前端文件选择器，使用 Enterprise API:

```typescript
// 调用 Enterprise API 获取配置
const response = await fetch('/inner/api/enterprise/gitea/config', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ email: userEmail })
});

const config = await response.json();
// 使用 config.gitea_url, config.gitea_token 等
```

## 临时解决方案

在 SSL 问题解决之前:

1. **手动配置**: 直接在数据库中设置 `Account.custom_config_dict`
2. **使用全局配置**: 所有用户共享一个 FileBay 账号（不推荐）
3. **等待生产环境**: 如果生产环境 SSL 正常，只在生产使用动态配置

## 相关文件

### 服务实现
- `api/services/filebay_config_service.py` - 配置服务
- `api/controllers/inner_api/gitea.py` - Enterprise API

### 测试工具
- `api/test_filebay_config_service.py` - 配置服务测试
- `api/test_filebay_ssl.py` - SSL 诊断工具
- `api/check_accounts_filebay.py` - 账号配置查看工具

### 文档
- `FileBay_SSL问题最终诊断.md` - SSL 问题详细分析
- `FileBay自动配置实现总结_最终版.md` - 实现总结
- `api/docs/FileBay自动配置完整实现.md` - 完整实现文档

### 参考
- `cheersai-desktop/src-tauri/src/core/gitea.rs` - Rust 参考实现（可用）

## API 使用示例

### 获取用户配置

```bash
# GET 请求
curl "http://localhost:5001/inner/api/enterprise/gitea/config?email=1@qq.com"

# POST 请求
curl -X POST "http://localhost:5001/inner/api/enterprise/gitea/config" \
  -H "Content-Type: application/json" \
  -d '{"email": "1@qq.com"}'
```

### 响应格式

```json
{
  "gitea_url": "https://uat-filebay.cheersai.cloud",
  "gitea_owner": "user_login_name",
  "gitea_repo": "workspace",
  "gitea_token": "actual_token_value_unmasked"
}
```

## 配置优先级

1. **Account.custom_config_dict** (最高优先级)
   - 用户特定配置
   - 手动设置或自动 provision 保存

2. **FileBay 已有用户** (中等优先级)
   - 查找 FileBay 中的用户
   - 动态生成临时 Token
   - 不创建新用户

3. **全局环境变量** (最低优先级)
   - 所有用户共享
   - 仅作为 fallback

## 注意事项

1. **Token 脱敏**: 
   - 日志和前端显示使用脱敏 Token
   - 后端 API 返回完整 Token

2. **Token 生命周期**:
   - 动态生成的 Token 是临时的
   - 每次调用可能生成新 Token
   - 考虑实现 Token 缓存机制

3. **错误处理**:
   - 用户不存在: 返回 404
   - SSL 连接失败: 返回 500
   - 配置缺失: fallback 到全局配置

4. **安全性**:
   - Enterprise API 需要认证
   - Token 不应暴露给前端
   - 使用 HTTPS 传输
