# Token 配额管理系统

## 📋 概述

Token 配额管理系统允许你为租户或用户设置云端模型的 Token 使用配额。当达到配额阈值后，系统会自动切换到本地模型，实现成本控制和资源管理。

## 🎯 核心功能

### 1. 灵活的时间间隔配置
- **每小时** (hourly): 每小时重置配额
- **每天** (daily): 每天重置配额（默认）
- **每周** (weekly): 每周重置配额
- **每月** (monthly): 每月重置配额
- **自定义** (custom): 自定义时间间隔（秒数）

### 2. 多级配额管理
- **租户级配额**: 适用于整个租户的所有用户
- **用户级配额**: 针对特定用户的个性化配额
- **优先级机制**: 用户级配额优先于租户级配额

### 3. 自动模型切换
- 配额内：使用云端模型（高性能）
- 超额后：自动切换到本地模型（成本控制）
- 支持配置多个云端和本地模型

### 4. 详细的使用统计
- 实时 Token 使用监控
- 按模型统计使用情况
- 历史数据分析和报表

## 🚀 快速开始

### 1. 创建默认配额配置

```bash
# 使用 API 创建配额配置
curl -X POST http://localhost:5001/console/api/token-quota/configs \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "name": "默认每日配额",
    "description": "每天 100,000 tokens 的默认配额",
    "interval_type": "daily",
    "token_limit": 100000,
    "cloud_models": [
      {"provider": "openai", "model": "gpt-4"},
      {"provider": "anthropic", "model": "claude-3-opus"}
    ],
    "local_models": [
      {"provider": "ollama", "model": "llama2"},
      {"provider": "ollama", "model": "mistral"}
    ],
    "priority": 0
  }'
```

### 2. 检查配额状态

```bash
# 检查当前配额
curl -X POST http://localhost:5001/console/api/token-quota/check \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "tokens_to_use": 1000
  }'

# 响应示例
{
  "within_quota": true,
  "remaining_tokens": 95000,
  "should_use_local": false,
  "quota_config": {...},
  "current_usage": {...}
}
```

### 3. 记录 Token 使用

```bash
# 记录 Token 使用
curl -X POST http://localhost:5001/console/api/token-quota/usage/record \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "model_provider": "openai",
    "model_name": "gpt-4",
    "tokens_used": 1500,
    "input_tokens": 1000,
    "output_tokens": 500,
    "request_id": "req_123456"
  }'
```

### 4. 查看使用统计

```bash
# 获取当前时间窗口的使用情况
curl -X GET http://localhost:5001/console/api/token-quota/usage/current \
  -H "Authorization: Bearer YOUR_TOKEN"

# 获取统计信息
curl -X GET "http://localhost:5001/console/api/token-quota/usage/statistics?start_date=2026-05-01&end_date=2026-05-31" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## 📊 API 接口文档

### 配额配置管理

#### 1. 获取配额配置列表
```
GET /console/api/token-quota/configs
```

#### 2. 创建配额配置
```
POST /console/api/token-quota/configs
Content-Type: application/json

{
  "name": "配置名称",
  "description": "配置描述",
  "interval_type": "daily|hourly|weekly|monthly|custom",
  "interval_value": 3600,  // 仅当 interval_type=custom 时需要
  "token_limit": 100000,
  "cloud_models": [
    {"provider": "openai", "model": "gpt-4"}
  ],
  "local_models": [
    {"provider": "ollama", "model": "llama2"}
  ],
  "priority": 0,
  "extra_config": {}
}
```

#### 3. 获取配额配置详情
```
GET /console/api/token-quota/configs/{config_id}
```

#### 4. 更新配额配置
```
PUT /console/api/token-quota/configs/{config_id}
Content-Type: application/json

{
  "token_limit": 200000,
  "status": "active|paused"
}
```

#### 5. 删除配额配置
```
DELETE /console/api/token-quota/configs/{config_id}
```

### 配额检查和使用

#### 6. 检查配额
```
POST /console/api/token-quota/check
Content-Type: application/json

{
  "user_id": "optional_user_id",
  "tokens_to_use": 1000
}

响应:
{
  "within_quota": true,
  "remaining_tokens": 95000,
  "should_use_local": false,
  "quota_config": {...},
  "current_usage": {...}
}
```

#### 7. 记录 Token 使用
```
POST /console/api/token-quota/usage/record
Content-Type: application/json

{
  "model_provider": "openai",
  "model_name": "gpt-4",
  "tokens_used": 1500,
  "input_tokens": 1000,
  "output_tokens": 500,
  "user_id": "optional_user_id",
  "request_id": "optional_request_id",
  "extra_info": {}
}
```

#### 8. 获取当前使用情况
```
GET /console/api/token-quota/usage/current?user_id=optional_user_id
```

#### 9. 获取统计信息
```
GET /console/api/token-quota/usage/statistics?user_id=optional&start_date=2026-05-01&end_date=2026-05-31
```

#### 10. 重置配额
```
POST /console/api/token-quota/reset
Content-Type: application/json

{
  "user_id": "optional_user_id"
}
```

## 💡 使用场景

### 场景 1: 租户级每日配额
```python
# 为租户设置每天 100,000 tokens 的配额
TokenQuotaService.create_quota_config(
    tenant_id="tenant_123",
    user_id=None,  # 租户级配置
    name="租户每日配额",
    interval_type="daily",
    token_limit=100000,
    cloud_models=[
        {"provider": "openai", "model": "gpt-4"}
    ],
    local_models=[
        {"provider": "ollama", "model": "llama2"}
    ],
    created_by="admin_user_id"
)
```

### 场景 2: 用户级每小时配额
```python
# 为特定用户设置每小时 5,000 tokens 的配额
TokenQuotaService.create_quota_config(
    tenant_id="tenant_123",
    user_id="user_456",  # 用户级配置
    name="用户每小时配额",
    interval_type="hourly",
    token_limit=5000,
    cloud_models=[
        {"provider": "openai", "model": "gpt-3.5-turbo"}
    ],
    local_models=[
        {"provider": "ollama", "model": "mistral"}
    ],
    created_by="admin_user_id",
    priority=10  # 高优先级
)
```

### 场景 3: 自定义时间间隔
```python
# 每 6 小时 50,000 tokens
TokenQuotaService.create_quota_config(
    tenant_id="tenant_123",
    user_id=None,
    name="6小时配额",
    interval_type="custom",
    interval_value=21600,  # 6 小时 = 21600 秒
    token_limit=50000,
    cloud_models=[...],
    local_models=[...],
    created_by="admin_user_id"
)
```

### 场景 4: 在应用中集成配额检查
```python
from services.token_quota_service import TokenQuotaService

# 在调用模型前检查配额
def call_llm_with_quota_check(tenant_id, user_id, prompt):
    # 估算需要的 tokens
    estimated_tokens = len(prompt) // 4  # 粗略估算
    
    # 检查配额
    quota_check = TokenQuotaService.check_quota(
        tenant_id=tenant_id,
        user_id=user_id,
        tokens_to_use=estimated_tokens
    )
    
    # 根据配额选择模型
    if quota_check["should_use_local"]:
        # 使用本地模型
        model_provider = "ollama"
        model_name = "llama2"
        print(f"配额已用完，切换到本地模型: {model_provider}/{model_name}")
    else:
        # 使用云端模型
        model_provider = "openai"
        model_name = "gpt-4"
        print(f"配额充足，使用云端模型: {model_provider}/{model_name}")
    
    # 调用模型...
    response = call_model(model_provider, model_name, prompt)
    
    # 记录实际使用
    TokenQuotaService.record_token_usage(
        tenant_id=tenant_id,
        user_id=user_id,
        model_provider=model_provider,
        model_name=model_name,
        tokens_used=response.total_tokens,
        input_tokens=response.prompt_tokens,
        output_tokens=response.completion_tokens
    )
    
    return response
```

## 🔧 配置示例

### 默认配置（推荐）
```json
{
  "name": "默认每日配额",
  "interval_type": "daily",
  "token_limit": 100000,
  "cloud_models": [
    {"provider": "openai", "model": "gpt-4"},
    {"provider": "openai", "model": "gpt-3.5-turbo"},
    {"provider": "anthropic", "model": "claude-3-opus"}
  ],
  "local_models": [
    {"provider": "ollama", "model": "llama2"},
    {"provider": "ollama", "model": "mistral"},
    {"provider": "ollama", "model": "codellama"}
  ],
  "extra_config": {
    "alert_threshold": 0.8,  // 80% 时发送告警
    "notification_email": "admin@example.com"
  }
}
```

## 📈 监控和告警

### 配额使用监控
```python
# 获取实时使用情况
statistics = TokenQuotaService.get_quota_statistics(
    tenant_id="tenant_123",
    start_date=datetime.now() - timedelta(days=7),
    end_date=datetime.now()
)

print(f"总使用: {statistics['total_tokens']} tokens")
print(f"总请求: {statistics['total_requests']} 次")
print(f"超额次数: {statistics['exceeded_periods']} 次")
print(f"模型统计: {statistics['model_statistics']}")
```

### 告警配置
在 `extra_config` 中配置告警阈值：
```json
{
  "extra_config": {
    "alert_threshold": 0.8,  // 80% 时告警
    "alert_threshold_90": 0.9,  // 90% 时二次告警
    "notification_email": "admin@example.com",
    "notification_webhook": "https://your-webhook.com/alert"
  }
}
```

## 🗄️ 数据库表结构

### token_quota_configs
配额配置表，存储配额规则。

### token_quota_usages
使用记录表，存储每个时间窗口的使用情况。

### token_quota_logs
日志表，记录每次 Token 使用的详细信息。

## 🔐 权限控制

所有 API 接口都需要登录认证：
- 需要 `@login_required` 装饰器
- 需要 `@account_initialization_required` 装饰器
- 自动关联到当前用户的租户

## 🎨 前端集成

### React 组件示例
```typescript
// 检查配额并显示提示
const QuotaIndicator = () => {
  const [quotaInfo, setQuotaInfo] = useState(null);
  
  useEffect(() => {
    fetch('/console/api/token-quota/check', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({tokens_to_use: 0})
    })
    .then(res => res.json())
    .then(data => setQuotaInfo(data));
  }, []);
  
  if (!quotaInfo) return null;
  
  const usagePercent = (quotaInfo.quota_config.token_limit - quotaInfo.remaining_tokens) 
    / quotaInfo.quota_config.token_limit * 100;
  
  return (
    <div className="quota-indicator">
      <div className="progress-bar">
        <div style={{width: `${usagePercent}%`}} />
      </div>
      <span>
        剩余: {quotaInfo.remaining_tokens.toLocaleString()} tokens
        {quotaInfo.should_use_local && ' (已切换到本地模型)'}
      </span>
    </div>
  );
};
```

## 📝 注意事项

1. **时区处理**: 所有时间使用 UTC，前端需要转换为本地时区
2. **并发安全**: 使用数据库事务确保并发更新的安全性
3. **性能优化**: 使用索引优化查询性能
4. **数据清理**: 建议定期清理旧的日志数据
5. **配额重置**: 时间窗口自动切换，无需手动重置

## 🚀 后续扩展

- [ ] 添加配额告警通知（邮件/Webhook）
- [ ] 支持配额共享（多个用户共享配额池）
- [ ] 添加配额购买和充值功能
- [ ] 支持按成本计费（而不仅是 Token 数）
- [ ] 添加配额预测和建议功能
- [ ] 支持配额转移和赠送

## 📞 技术支持

如有问题，请联系技术团队或查看详细文档。
