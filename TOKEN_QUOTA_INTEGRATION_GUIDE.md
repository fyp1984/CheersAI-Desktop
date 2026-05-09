# Token 配额系统 - 集成指南

## 📋 概述

本文档说明如何将 Token 配额系统集成到现有的 LLM 调用流程中，实现自动配额检查和模型切换。

## ✅ 已完成的工作

### 1. 核心系统实现 ✅
- ✅ 数据库模型（3个表）
- ✅ 服务层（TokenQuotaService）
- ✅ API 接口（10个端点）
- ✅ 数据库迁移
- ✅ 初始化脚本
- ✅ 完整文档

### 2. 系统状态 ✅
- ✅ 所有服务正在运行
  - Docker 中间件服务
  - Celery Worker
  - Celery Beat
  - Flask API (http://localhost:5001)
  - Next.js 前端 (http://localhost:3000)

## 🔧 集成步骤

### 步骤 1: 初始化默认配额（必需）

为所有现有租户创建默认配额配置：

```bash
cd api
python -m uv run python init_default_quota.py --token-limit 100000 --interval-type daily
```

**参数说明**：
- `--token-limit`: Token 配额上限（默认 100000）
- `--interval-type`: 时间间隔类型（hourly/daily/weekly/monthly，默认 daily）
- `--force`: 强制更新已存在的配置

### 步骤 2: 在 LLM 调用前集成配额检查

有两种集成方式：

#### 方式 A: 在 LLM Node 中集成（推荐）

修改 `api/core/workflow/nodes/llm/node.py` 的 `invoke_llm` 方法：

```python
@staticmethod
def invoke_llm(
    *,
    node_data_model: ModelConfig,
    model_instance: ModelInstance,
    prompt_messages: Sequence[PromptMessage],
    stop: Sequence[str] | None = None,
    user_id: str,
    tenant_id: str,  # 添加 tenant_id 参数
    structured_output_enabled: bool,
    structured_output: Mapping[str, Any] | None = None,
    file_saver: LLMFileSaver,
    file_outputs: list[File],
    node_id: str,
    node_type: NodeType,
    reasoning_format: Literal["separated", "tagged"] = "tagged",
) -> Generator[NodeEventBase | LLMStructuredOutput, None, None]:
    
    # ========== 添加配额检查逻辑 ==========
    from services.token_quota_service import TokenQuotaService
    
    # 1. 预估 Token 使用量（可以根据 prompt_messages 长度估算）
    estimated_tokens = sum(len(msg.content) // 4 for msg in prompt_messages if hasattr(msg, 'content'))
    
    # 2. 检查配额
    quota_check = TokenQuotaService.check_quota(
        tenant_id=tenant_id,
        user_id=user_id,
        tokens_to_use=estimated_tokens
    )
    
    # 3. 根据配额决定使用哪个模型
    if quota_check["should_use_local"]:
        # 配额已用完，切换到本地模型
        logger.warning(
            f"Token quota exceeded for tenant {tenant_id}, "
            f"switching to local model. "
            f"Remaining: {quota_check['remaining_tokens']} tokens"
        )
        
        # 从配额配置中获取本地模型
        quota_config = quota_check.get("quota_config")
        if quota_config and quota_config.local_models:
            local_model = quota_config.local_models[0]  # 使用第一个本地模型
            
            # 重新获取本地模型实例
            from core.model_manager import ModelManager
            model_manager = ModelManager()
            model_instance = model_manager.get_model_instance(
                tenant_id=tenant_id,
                provider=local_model["provider"],
                model_type=ModelType.LLM,
                model=local_model["model"]
            )
            
            # 更新 node_data_model
            node_data_model.provider = local_model["provider"]
            node_data_model.name = local_model["model"]
    # ========== 配额检查逻辑结束 ==========
    
    # 原有的模型调用逻辑
    model_schema = model_instance.model_type_instance.get_model_schema(
        node_data_model.name, model_instance.credentials
    )
    # ... 其余代码保持不变
```

然后在 `_run` 方法中调用时传入 `tenant_id`：

```python
def _run(self) -> Generator:
    # ... 现有代码 ...
    
    # handle invoke result
    generator = LLMNode.invoke_llm(
        node_data_model=self.node_data.model,
        model_instance=model_instance,
        prompt_messages=prompt_messages,
        stop=stop,
        user_id=self.user_id,
        tenant_id=self.tenant_id,  # 添加这一行
        structured_output_enabled=self.node_data.structured_output_enabled,
        structured_output=self.node_data.structured_output,
        file_saver=self._llm_file_saver,
        file_outputs=self._file_outputs,
        node_id=self._node_id,
        node_type=self.node_type,
        reasoning_format=self.node_data.reasoning_format,
    )
    # ... 其余代码保持不变
```

#### 方式 B: 在 ModelManager 中集成（全局）

修改 `api/core/model_manager.py` 的模型获取逻辑：

```python
class ModelManager:
    def get_model_instance_with_quota_check(
        self,
        tenant_id: str,
        user_id: str,
        provider: str,
        model_type: ModelType,
        model: str,
        estimated_tokens: int = 1000,
    ) -> ModelInstance:
        """
        获取模型实例，并根据配额自动选择云端或本地模型
        """
        from services.token_quota_service import TokenQuotaService
        
        # 检查配额
        quota_check = TokenQuotaService.check_quota(
            tenant_id=tenant_id,
            user_id=user_id,
            tokens_to_use=estimated_tokens
        )
        
        # 如果需要使用本地模型
        if quota_check["should_use_local"]:
            quota_config = quota_check.get("quota_config")
            if quota_config and quota_config.local_models:
                # 找到匹配的本地模型
                for local_model in quota_config.local_models:
                    if local_model.get("provider") and local_model.get("model"):
                        logger.warning(
                            f"Switching to local model: {local_model['provider']}/{local_model['model']}"
                        )
                        provider = local_model["provider"]
                        model = local_model["model"]
                        break
        
        # 获取模型实例
        return self.get_model_instance(
            tenant_id=tenant_id,
            provider=provider,
            model_type=model_type,
            model=model
        )
```

### 步骤 3: 记录 Token 使用

在 `api/core/workflow/nodes/llm/llm_utils.py` 的 `deduct_llm_quota` 函数中添加：

```python
def deduct_llm_quota(
    tenant_id: str,
    model_instance: ModelInstance,
    usage: LLMUsage,
    user_id: str | None = None,
    request_id: str | None = None,
) -> None:
    """
    扣除 LLM 配额并记录使用
    """
    # 原有的配额扣除逻辑
    # ... 现有代码 ...
    
    # ========== 添加 Token 配额记录 ==========
    from services.token_quota_service import TokenQuotaService
    
    try:
        TokenQuotaService.record_token_usage(
            tenant_id=tenant_id,
            user_id=user_id,
            model_provider=model_instance.provider,
            model_name=model_instance.model,
            tokens_used=usage.total_tokens,
            input_tokens=usage.prompt_tokens,
            output_tokens=usage.completion_tokens,
            request_id=request_id,
            extra_info={
                "model_type": str(model_instance.model_type),
                "latency": usage.latency,
                "currency": usage.currency,
                "total_price": usage.total_price,
            }
        )
        logger.info(
            f"Recorded token usage: {usage.total_tokens} tokens for "
            f"{model_instance.provider}/{model_instance.model}"
        )
    except Exception as e:
        # 记录失败不应该影响主流程
        logger.error(f"Failed to record token usage: {e}")
    # ========== Token 配额记录结束 ==========
```

### 步骤 4: 前端集成（可选）

#### 4.1 创建配额显示组件

在 `web/app/components/header/` 创建 `TokenQuotaIndicator.tsx`：

```typescript
'use client'

import { useEffect, useState } from 'react'
import { AlertTriangle, CheckCircle2 } from 'lucide-react'

interface QuotaInfo {
  within_quota: boolean
  remaining_tokens: number
  should_use_local: boolean
  quota_config: {
    token_limit: number
    interval_type: string
  } | null
}

export default function TokenQuotaIndicator() {
  const [quotaInfo, setQuotaInfo] = useState<QuotaInfo | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchQuotaInfo()
    // 每分钟刷新一次
    const interval = setInterval(fetchQuotaInfo, 60000)
    return () => clearInterval(interval)
  }, [])

  const fetchQuotaInfo = async () => {
    try {
      const response = await fetch('/console/api/token-quota/check', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ tokens_to_use: 0 })
      })
      const data = await response.json()
      setQuotaInfo(data)
    } catch (error) {
      console.error('Failed to fetch quota info:', error)
    } finally {
      setLoading(false)
    }
  }

  if (loading || !quotaInfo?.quota_config) {
    return null
  }

  const { quota_config, remaining_tokens, should_use_local } = quotaInfo
  const usedTokens = quota_config.token_limit - remaining_tokens
  const usagePercent = (usedTokens / quota_config.token_limit) * 100

  const intervalText = {
    hourly: '小时',
    daily: '天',
    weekly: '周',
    monthly: '月'
  }[quota_config.interval_type] || quota_config.interval_type

  return (
    <div className="flex items-center gap-2 px-3 py-2 bg-white rounded-lg border border-gray-200">
      {should_use_local ? (
        <AlertTriangle className="w-4 h-4 text-warning-600" />
      ) : (
        <CheckCircle2 className="w-4 h-4 text-success-600" />
      )}
      
      <div className="flex flex-col gap-1 min-w-[200px]">
        <div className="flex items-center justify-between text-xs">
          <span className="text-gray-600">Token 配额</span>
          {should_use_local && (
            <span className="text-warning-600 font-medium">使用本地模型</span>
          )}
        </div>
        
        <div className="w-full bg-gray-200 rounded-full h-1.5">
          <div 
            className={`h-1.5 rounded-full transition-all ${
              usagePercent > 90 ? 'bg-error-600' :
              usagePercent > 70 ? 'bg-warning-600' :
              'bg-primary-600'
            }`}
            style={{ width: `${Math.min(usagePercent, 100)}%` }}
          />
        </div>
        
        <div className="flex items-center justify-between text-xs text-gray-500">
          <span>剩余: {remaining_tokens.toLocaleString()}</span>
          <span>{quota_config.token_limit.toLocaleString()} / {intervalText}</span>
        </div>
      </div>
    </div>
  )
}
```

#### 4.2 在 Header 中使用

修改 `web/app/components/header/index.tsx`：

```typescript
import TokenQuotaIndicator from './TokenQuotaIndicator'

export default function Header() {
  return (
    <header className="...">
      {/* 其他 header 内容 */}
      
      {/* 添加配额指示器 */}
      <TokenQuotaIndicator />
      
      {/* 其他 header 内容 */}
    </header>
  )
}
```

#### 4.3 创建配额管理页面（可选）

在 `web/app/(commonLayout)/token-quota/` 创建配额管理页面，提供：
- 查看当前配额配置
- 修改配额上限
- 查看使用统计
- 查看历史记录

### 步骤 5: 测试集成

#### 5.1 测试配额检查

```bash
# 检查配额
curl -X POST http://localhost:5001/console/api/token-quota/check \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"tokens_to_use": 1000}'
```

#### 5.2 测试模型调用

创建一个测试脚本 `api/test_quota_integration.py`：

```python
"""测试配额集成"""
import logging
from core.model_manager import ModelManager
from core.model_runtime.entities.model_entities import ModelType
from services.token_quota_service import TokenQuotaService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_quota_integration():
    tenant_id = "your_tenant_id"
    user_id = "your_user_id"
    
    # 1. 检查配额
    quota_check = TokenQuotaService.check_quota(
        tenant_id=tenant_id,
        user_id=user_id,
        tokens_to_use=1000
    )
    
    logger.info(f"Quota check result: {quota_check}")
    
    # 2. 根据配额选择模型
    if quota_check["should_use_local"]:
        logger.warning("Using local model due to quota limit")
        provider = "ollama"
        model = "llama2"
    else:
        logger.info("Using cloud model")
        provider = "openai"
        model = "gpt-3.5-turbo"
    
    # 3. 获取模型实例
    model_manager = ModelManager()
    model_instance = model_manager.get_model_instance(
        tenant_id=tenant_id,
        provider=provider,
        model_type=ModelType.LLM,
        model=model
    )
    
    logger.info(f"Using model: {model_instance.provider}/{model_instance.model}")
    
    # 4. 模拟调用并记录使用
    TokenQuotaService.record_token_usage(
        tenant_id=tenant_id,
        user_id=user_id,
        model_provider=model_instance.provider,
        model_name=model_instance.model,
        tokens_used=1500,
        input_tokens=1000,
        output_tokens=500
    )
    
    logger.info("Token usage recorded successfully")

if __name__ == "__main__":
    test_quota_integration()
```

运行测试：

```bash
cd api
python -m uv run python test_quota_integration.py
```

## 📊 监控和维护

### 1. 查看配额使用情况

```bash
# 当前使用情况
curl -X GET http://localhost:5001/console/api/token-quota/usage/current \
  -H "Authorization: Bearer YOUR_TOKEN"

# 历史统计
curl -X GET "http://localhost:5001/console/api/token-quota/usage/statistics?start_date=2026-05-01&end_date=2026-05-31" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 2. 调整配额

```bash
# 更新配额上限
curl -X PUT http://localhost:5001/console/api/token-quota/configs/{config_id} \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"token_limit": 200000}'
```

### 3. 日志监控

在 `api/extensions/ext_logging.py` 中添加配额相关日志：

```python
# 监控配额超限事件
logger.warning(f"Token quota exceeded: tenant={tenant_id}, user={user_id}")

# 监控模型切换事件
logger.info(f"Switched to local model: tenant={tenant_id}, model={model}")
```

## 🔍 故障排查

### 问题 1: 配额检查失败

**症状**: API 返回 500 错误

**解决方案**:
1. 检查数据库表是否创建：
   ```bash
   cd api
   python -m uv run flask db current
   ```

2. 检查是否有默认配额：
   ```bash
   python -m uv run python init_default_quota.py
   ```

### 问题 2: 模型切换不生效

**症状**: 超过配额后仍使用云端模型

**解决方案**:
1. 检查配额配置中是否设置了本地模型
2. 检查本地模型是否可用
3. 查看日志确认切换逻辑是否执行

### 问题 3: Token 使用未记录

**症状**: 使用统计为空

**解决方案**:
1. 检查 `record_token_usage` 是否被调用
2. 检查日志中是否有错误信息
3. 确认配额配置是否激活

## 📝 最佳实践

### 1. 配额设置建议

- **开发环境**: 每天 50,000 tokens
- **测试环境**: 每天 100,000 tokens
- **生产环境**: 根据实际需求设置，建议每天 500,000 - 1,000,000 tokens

### 2. 本地模型配置

确保配置了可用的本地模型：

```json
{
  "local_models": [
    {"provider": "ollama", "model": "llama2"},
    {"provider": "ollama", "model": "mistral"},
    {"provider": "ollama", "model": "codellama"}
  ]
}
```

### 3. 监控告警

建议设置以下告警：
- 配额使用超过 80%
- 配额使用超过 90%
- 配额已用完（切换到本地模型）

### 4. 定期审查

- 每周审查配额使用情况
- 每月分析模型使用趋势
- 根据实际使用调整配额设置

## 🎯 下一步

### 短期（可选）
1. ✅ 完成基础集成
2. ⬜ 添加前端配额显示
3. ⬜ 添加配额告警通知

### 中期（可选）
1. ⬜ 创建配额管理界面
2. ⬜ 添加配额使用趋势图表
3. ⬜ 支持配额共享

### 长期（可选）
1. ⬜ 集成到计费系统
2. ⬜ 添加配额预测功能
3. ⬜ 支持按成本计费

## 📞 技术支持

如有问题，请参考：
- **系统文档**: `TOKEN_QUOTA_SYSTEM.md`
- **快速开始**: `TOKEN_QUOTA_QUICK_START.md`
- **实施总结**: `TOKEN_QUOTA_IMPLEMENTATION_SUMMARY.md`

## ✅ 集成检查清单

- [ ] 执行数据库迁移
- [ ] 运行初始化脚本创建默认配额
- [ ] 在 LLM 调用前添加配额检查
- [ ] 在 LLM 调用后记录 Token 使用
- [ ] 配置本地模型列表
- [ ] 测试配额检查功能
- [ ] 测试模型自动切换
- [ ] 添加前端配额显示（可选）
- [ ] 设置监控和告警（可选）
- [ ] 文档更新

## 🎉 总结

Token 配额系统已完整实现，现在需要：

1. **必需步骤**:
   - 运行初始化脚本创建默认配额
   - 在 LLM 调用流程中集成配额检查和记录

2. **可选步骤**:
   - 添加前端配额显示
   - 创建配额管理界面
   - 设置监控告警

完成集成后，系统将自动：
- ✅ 在调用云端模型前检查配额
- ✅ 配额不足时自动切换到本地模型
- ✅ 记录每次 Token 使用
- ✅ 提供详细的使用统计

**系统已就绪，可以开始集成！** 🚀
