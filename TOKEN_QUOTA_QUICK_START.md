# Token 配额系统 - 快速开始指南

## 🎯 系统概述

Token 配额管理系统可以：
- ✅ 设置时间间隔（每小时/每天/每周/每月/自定义）
- ✅ 设置 Token 使用上限
- ✅ 达到阈值后自动切换到本地模型
- ✅ 提供 API 接口供外部系统调用
- ✅ 详细的使用统计和日志

## 🚀 快速部署

### 1. 数据库迁移（已完成）

```bash
cd api
python -m uv run flask db upgrade
```

### 2. 初始化默认配额

为所有现有租户创建默认配额（每天 100,000 tokens）：

```bash
cd api
python -m uv run python init_default_quota.py --token-limit 100000 --interval-type daily
```

可选参数：
- `--token-limit`: Token 配额上限（默认 100000）
- `--interval-type`: 时间间隔类型（hourly/daily/weekly/monthly，默认 daily）
- `--force`: 强制更新已存在的配置

### 3. 验证安装

```bash
# 测试 API 接口
curl -X GET http://localhost:5001/console/api/token-quota/configs \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## 📝 基本使用

### 场景 1: 创建配额配置

```python
from services.token_quota_service import TokenQuotaService

# 创建每天 100,000 tokens 的配额
quota_config = TokenQuotaService.create_quota_config(
    tenant_id="your_tenant_id",
    user_id=None,  # None 表示租户级配置
    name="每日配额",
    interval_type="daily",
    token_limit=100000,
    cloud_models=[
        {"provider": "openai", "model": "gpt-4"},
        {"provider": "openai", "model": "gpt-3.5-turbo"}
    ],
    local_models=[
        {"provider": "ollama", "model": "llama2"},
        {"provider": "ollama", "model": "mistral"}
    ],
    created_by="admin_user_id"
)
```

### 场景 2: 在代码中检查配额

```python
from services.token_quota_service import TokenQuotaService

def call_llm_with_quota(tenant_id, user_id, prompt):
    # 1. 检查配额
    quota_check = TokenQuotaService.check_quota(
        tenant_id=tenant_id,
        user_id=user_id,
        tokens_to_use=1000  # 预估使用量
    )
    
    # 2. 根据配额选择模型
    if quota_check["should_use_local"]:
        # 配额已用完，使用本地模型
        model_provider = "ollama"
        model_name = "llama2"
        print(f"⚠️ 配额已达上限，切换到本地模型")
    else:
        # 配额充足，使用云端模型
        model_provider = "openai"
        model_name = "gpt-4"
        print(f"✅ 配额充足，使用云端模型")
        print(f"   剩余: {quota_check['remaining_tokens']:,} tokens")
    
    # 3. 调用模型
    response = call_model(model_provider, model_name, prompt)
    
    # 4. 记录实际使用
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

### 场景 3: 通过 API 调用

```bash
# 1. 检查配额
curl -X POST http://localhost:5001/console/api/token-quota/check \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"tokens_to_use": 1000}'

# 响应示例
{
  "within_quota": true,
  "remaining_tokens": 95000,
  "should_use_local": false,
  "quota_config": {
    "id": "config_id",
    "token_limit": 100000,
    "interval_type": "daily"
  },
  "current_usage": {
    "total_tokens": 5000,
    "request_count": 10
  }
}

# 2. 记录使用
curl -X POST http://localhost:5001/console/api/token-quota/usage/record \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "model_provider": "openai",
    "model_name": "gpt-4",
    "tokens_used": 1500,
    "input_tokens": 1000,
    "output_tokens": 500
  }'

# 3. 查看统计
curl -X GET http://localhost:5001/console/api/token-quota/usage/statistics \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## 🔧 配置示例

### 示例 1: 每天 100,000 tokens（推荐）

```json
{
  "name": "默认每日配额",
  "interval_type": "daily",
  "token_limit": 100000,
  "cloud_models": [
    {"provider": "openai", "model": "gpt-4"},
    {"provider": "openai", "model": "gpt-3.5-turbo"}
  ],
  "local_models": [
    {"provider": "ollama", "model": "llama2"}
  ]
}
```

### 示例 2: 每小时 5,000 tokens

```json
{
  "name": "每小时配额",
  "interval_type": "hourly",
  "token_limit": 5000,
  "cloud_models": [
    {"provider": "openai", "model": "gpt-3.5-turbo"}
  ],
  "local_models": [
    {"provider": "ollama", "model": "mistral"}
  ]
}
```

### 示例 3: 每周 500,000 tokens

```json
{
  "name": "每周配额",
  "interval_type": "weekly",
  "token_limit": 500000,
  "cloud_models": [
    {"provider": "openai", "model": "gpt-4"},
    {"provider": "anthropic", "model": "claude-3-opus"}
  ],
  "local_models": [
    {"provider": "ollama", "model": "llama2"},
    {"provider": "ollama", "model": "codellama"}
  ]
}
```

### 示例 4: 自定义间隔（每 6 小时）

```json
{
  "name": "6小时配额",
  "interval_type": "custom",
  "interval_value": 21600,
  "token_limit": 30000,
  "cloud_models": [
    {"provider": "openai", "model": "gpt-3.5-turbo"}
  ],
  "local_models": [
    {"provider": "ollama", "model": "mistral"}
  ]
}
```

## 📊 监控和管理

### 查看当前使用情况

```bash
# 获取当前时间窗口的使用情况
curl -X GET http://localhost:5001/console/api/token-quota/usage/current \
  -H "Authorization: Bearer YOUR_TOKEN"

# 响应示例
{
  "id": "usage_id",
  "period_start": "2026-05-09T00:00:00Z",
  "period_end": "2026-05-10T00:00:00Z",
  "total_tokens": 45000,
  "input_tokens": 30000,
  "output_tokens": 15000,
  "request_count": 50,
  "is_exceeded": false,
  "model_usage_details": {
    "openai/gpt-4": {
      "tokens": 30000,
      "requests": 30
    },
    "openai/gpt-3.5-turbo": {
      "tokens": 15000,
      "requests": 20
    }
  }
}
```

### 查看历史统计

```bash
# 获取过去 30 天的统计
curl -X GET "http://localhost:5001/console/api/token-quota/usage/statistics?start_date=2026-04-09&end_date=2026-05-09" \
  -H "Authorization: Bearer YOUR_TOKEN"

# 响应示例
{
  "total_tokens": 2500000,
  "total_requests": 5000,
  "total_periods": 30,
  "exceeded_periods": 3,
  "model_statistics": {
    "openai/gpt-4": {
      "tokens": 1800000,
      "requests": 3000
    },
    "openai/gpt-3.5-turbo": {
      "tokens": 700000,
      "requests": 2000
    }
  }
}
```

### 重置配额

```bash
# 手动重置当前时间窗口的配额
curl -X POST http://localhost:5001/console/api/token-quota/reset \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{}'
```

## 🎨 前端集成示例

### React 组件

```typescript
import { useState, useEffect } from 'react';

const TokenQuotaIndicator = () => {
  const [quotaInfo, setQuotaInfo] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchQuotaInfo();
    // 每分钟刷新一次
    const interval = setInterval(fetchQuotaInfo, 60000);
    return () => clearInterval(interval);
  }, []);

  const fetchQuotaInfo = async () => {
    try {
      const response = await fetch('/console/api/token-quota/check', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${getToken()}`
        },
        body: JSON.stringify({ tokens_to_use: 0 })
      });
      const data = await response.json();
      setQuotaInfo(data);
    } catch (error) {
      console.error('Failed to fetch quota info:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading || !quotaInfo?.quota_config) {
    return <div>加载中...</div>;
  }

  const { quota_config, remaining_tokens, should_use_local } = quotaInfo;
  const usedTokens = quota_config.token_limit - remaining_tokens;
  const usagePercent = (usedTokens / quota_config.token_limit) * 100;

  return (
    <div className="quota-indicator">
      <div className="quota-header">
        <span>Token 配额</span>
        {should_use_local && (
          <span className="badge badge-warning">已切换到本地模型</span>
        )}
      </div>
      
      <div className="progress-bar">
        <div 
          className={`progress-fill ${usagePercent > 80 ? 'warning' : ''}`}
          style={{ width: `${usagePercent}%` }}
        />
      </div>
      
      <div className="quota-stats">
        <span>已使用: {usedTokens.toLocaleString()} tokens</span>
        <span>剩余: {remaining_tokens.toLocaleString()} tokens</span>
      </div>
      
      <div className="quota-info">
        <small>
          配额: {quota_config.token_limit.toLocaleString()} tokens / 
          {quota_config.interval_type === 'daily' && '天'}
          {quota_config.interval_type === 'hourly' && '小时'}
          {quota_config.interval_type === 'weekly' && '周'}
          {quota_config.interval_type === 'monthly' && '月'}
        </small>
      </div>
    </div>
  );
};

export default TokenQuotaIndicator;
```

## 🔍 常见问题

### Q1: 如何修改配额上限？

```bash
curl -X PUT http://localhost:5001/console/api/token-quota/configs/{config_id} \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"token_limit": 200000}'
```

### Q2: 如何暂停配额限制？

```bash
curl -X PUT http://localhost:5001/console/api/token-quota/configs/{config_id} \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"status": "paused"}'
```

### Q3: 如何为特定用户设置配额？

```python
# 创建用户级配额（优先级高于租户级）
TokenQuotaService.create_quota_config(
    tenant_id="tenant_id",
    user_id="specific_user_id",  # 指定用户ID
    name="用户专属配额",
    interval_type="daily",
    token_limit=50000,
    cloud_models=[...],
    local_models=[...],
    created_by="admin_id",
    priority=10  # 高优先级
)
```

### Q4: 配额何时重置？

配额会在时间窗口结束时自动重置：
- **hourly**: 每小时的 00 分
- **daily**: 每天的 00:00
- **weekly**: 每周一的 00:00
- **monthly**: 每月 1 日的 00:00
- **custom**: 根据设置的秒数自动计算

### Q5: 如何查看配额日志？

```python
from models.token_quota import TokenQuotaLog

# 查询最近的日志
logs = TokenQuotaLog.query.filter_by(
    tenant_id="tenant_id"
).order_by(
    TokenQuotaLog.created_at.desc()
).limit(100).all()

for log in logs:
    print(f"{log.created_at}: {log.model_provider}/{log.model_name} "
          f"used {log.tokens_used} tokens, "
          f"total: {log.tokens_after}/{log.quota_limit}")
```

## 📞 技术支持

如有问题，请查看完整文档 `TOKEN_QUOTA_SYSTEM.md` 或联系技术团队。

## 🎉 完成！

现在你的系统已经具备完整的 Token 配额管理功能！
