# Token 配额系统集成说明

## 完成时间
2026-05-09

## 集成内容

### 1. 配额统计集成到模型调用流程

**修改文件**: `api/services/model_usage_record_service.py`

**集成位置**: `ModelUsageRecordService._insert_record()` 方法

**功能说明**:
- 每次模型调用（LLM 或 Embedding）完成后，自动记录 Token 使用到配额系统
- 配额系统会自动：
  - 累计当前时间窗口的 Token 使用量
  - 检查是否超过配额限制
  - 记录详细的使用日志
  - 更新模型使用详情

### 2. 集成代码

```python
# 在 _insert_record 方法中添加
try:
    TokenQuotaService.record_token_usage(
        tenant_id=tenant_id,
        model_provider=provider,
        model_name=model_instance.model,
        tokens_used=total_tokens,
        user_id=user_id,
        request_id=record.id,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        extra_info={
            "model_type": model_type,
            "is_cloud": cls._is_cloud_model(provider),
            "total_price": str(total_price),
            "currency": currency or "USD",
        },
    )
except Exception:
    logger.exception("Failed to record token usage to quota system")
```

### 3. 工作流程

```
用户调用模型
    ↓
ModelManager.invoke_llm()
    ↓
ModelUsageRecordService.record_llm_usage()
    ↓
ModelUsageRecordService._insert_record()
    ↓
1. 插入 ModelUsageRecord（计费系统）
2. 调用 TokenQuotaService.record_token_usage()（配额系统）
    ↓
配额系统自动：
- 获取当前配额配置
- 更新当前时间窗口的使用量
- 检查是否超额
- 记录使用日志
```

### 4. 前端显示

**位置**: Token 计费页面 → 配额状态卡片

**显示内容**:
- 剩余 Token 数量
- 配额限制（每天 100,000 tokens）
- 使用进度条
- 重置时间倒计时
- 配额状态（配额充足/配额已用完）

### 5. 测试方法

1. **发起模型调用**:
   - 在应用中使用任何 LLM 功能（聊天、工作流等）
   - 系统会自动记录 Token 使用

2. **查看配额状态**:
   - 进入"设置" → "Token 计费"页面
   - 查看配额状态卡片
   - 点击刷新按钮更新数据

3. **验证统计**:
   - 配额卡片应该显示已使用的 Token 数
   - 进度条应该反映使用百分比
   - 剩余 Token 数应该正确计算

### 6. 注意事项

1. **错误处理**: 配额记录失败不会影响模型调用，只会记录日志
2. **性能影响**: 配额记录是同步操作，但非常快速（数据库插入/更新）
3. **时间窗口**: 配额按照配置的时间间隔（每小时/每天/每周/每月）自动重置
4. **优先级**: 用户级配额优先于租户级配额

### 7. 后续优化建议

1. **异步记录**: 可以考虑将配额记录改为异步任务，进一步提升性能
2. **缓存优化**: 可以缓存配额配置，减少数据库查询
3. **批量更新**: 可以考虑批量更新使用记录，减少数据库写入次数
4. **告警通知**: 当配额接近限制时，发送通知给管理员

## 相关文件

- `api/services/model_usage_record_service.py` - 模型使用记录服务（已修改）
- `api/services/token_quota_service.py` - Token 配额服务
- `api/models/token_quota.py` - 配额数据模型
- `api/controllers/console/token_quota.py` - 配额 API 接口
- `web/app/components/header/account-setting/token-billing-page/quota-status-card.tsx` - 配额状态卡片组件

## 数据库表

- `token_quota_configs` - 配额配置表
- `token_quota_usages` - 配额使用记录表
- `token_quota_logs` - 配额使用日志表

## API 接口

- `POST /console/api/token-quota/check` - 检查配额状态
- `GET /console/api/token-quota/usage/current` - 获取当前使用情况
- `GET /console/api/token-quota/usage/statistics` - 获取统计信息
- `POST /console/api/token-quota/usage/record` - 手动记录使用（已自动集成）
