# Token 配额系统 - 集成检查清单

## 📋 总览

本文档提供了一个详细的检查清单，帮助你逐步完成 Token 配额系统的集成。

---

## ✅ 阶段 1: 系统准备（已完成）

### 1.1 数据库准备
- [x] 创建数据库迁移文件
- [x] 执行 `flask db upgrade`
- [x] 验证表已创建
  - [x] `token_quota_configs`
  - [x] `token_quota_usages`
  - [x] `token_quota_logs`

### 1.2 代码实现
- [x] 实现数据库模型 (`api/models/token_quota.py`)
- [x] 实现服务层 (`api/services/token_quota_service.py`)
- [x] 实现 API 接口 (`api/controllers/console/token_quota.py`)
- [x] 创建初始化脚本 (`api/init_default_quota.py`)

### 1.3 文档准备
- [x] 系统文档 (`TOKEN_QUOTA_SYSTEM.md`)
- [x] 快速开始指南 (`TOKEN_QUOTA_QUICK_START.md`)
- [x] 实施总结 (`TOKEN_QUOTA_IMPLEMENTATION_SUMMARY.md`)
- [x] 集成指南 (`TOKEN_QUOTA_INTEGRATION_GUIDE.md`)
- [x] 流程图 (`TOKEN_QUOTA_FLOW_DIAGRAM.md`)
- [x] 检查清单 (`TOKEN_QUOTA_INTEGRATION_CHECKLIST.md`)

### 1.4 服务状态
- [x] Docker 中间件服务运行中
- [x] Celery Worker 运行中
- [x] Celery Beat 运行中
- [x] Flask API 运行中 (http://localhost:5001)
- [x] Next.js 前端运行中 (http://localhost:3000)

---

## 🎯 阶段 2: 初始化配置（必需）

### 2.1 创建默认配额
- [ ] 运行初始化脚本
  ```bash
  cd api
  python -m uv run python init_default_quota.py --token-limit 100000 --interval-type daily
  ```

- [ ] 验证配额已创建
  ```bash
  # 方法 1: 通过 API 验证
  curl -X GET http://localhost:5001/console/api/token-quota/configs \
    -H "Authorization: Bearer YOUR_TOKEN"
  
  # 方法 2: 通过数据库验证
  psql -d your_database -c "SELECT * FROM token_quota_configs;"
  ```

### 2.2 配置本地模型
- [ ] 确认 Ollama 已安装并运行
  ```bash
  ollama list
  ```

- [ ] 下载必要的本地模型
  ```bash
  ollama pull llama2
  ollama pull mistral
  ```

- [ ] 验证本地模型可用
  ```bash
  ollama run llama2 "Hello, world!"
  ```

### 2.3 配置云端模型
- [ ] 确认 OpenAI API Key 已配置
- [ ] 测试云端模型连接
- [ ] 记录可用的云端模型列表

---

## 🔧 阶段 3: 代码集成（核心）

### 3.1 方式 A: LLM Node 集成（推荐）

#### 3.1.1 修改 `api/core/workflow/nodes/llm/node.py`

- [ ] 在 `invoke_llm` 方法中添加 `tenant_id` 参数
  ```python
  @staticmethod
  def invoke_llm(
      *,
      node_data_model: ModelConfig,
      model_instance: ModelInstance,
      prompt_messages: Sequence[PromptMessage],
      stop: Sequence[str] | None = None,
      user_id: str,
      tenant_id: str,  # 添加这个参数
      # ... 其他参数
  ):
  ```

- [ ] 在 `invoke_llm` 方法开始处添加配额检查逻辑
  ```python
  # 导入服务
  from services.token_quota_service import TokenQuotaService
  
  # 预估 Token 使用量
  estimated_tokens = sum(len(msg.content) // 4 for msg in prompt_messages if hasattr(msg, 'content'))
  
  # 检查配额
  quota_check = TokenQuotaService.check_quota(
      tenant_id=tenant_id,
      user_id=user_id,
      tokens_to_use=estimated_tokens
  )
  
  # 根据配额选择模型
  if quota_check["should_use_local"]:
      # 切换到本地模型的逻辑
      pass
  ```

- [ ] 在 `_run` 方法中调用 `invoke_llm` 时传入 `tenant_id`
  ```python
  generator = LLMNode.invoke_llm(
      # ... 其他参数
      tenant_id=self.tenant_id,  # 添加这一行
  )
  ```

- [ ] 测试修改后的代码
  ```bash
  # 运行单元测试
  cd api
  python -m pytest tests/unit/core/workflow/nodes/llm/test_node.py -v
  ```

#### 3.1.2 修改 `api/core/workflow/nodes/llm/llm_utils.py`

- [ ] 在 `deduct_llm_quota` 函数中添加 Token 使用记录
  ```python
  def deduct_llm_quota(
      tenant_id: str,
      model_instance: ModelInstance,
      usage: LLMUsage,
      user_id: str | None = None,
      request_id: str | None = None,
  ) -> None:
      # 原有逻辑
      # ...
      
      # 添加 Token 配额记录
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
          )
      except Exception as e:
          logger.error(f"Failed to record token usage: {e}")
  ```

- [ ] 测试记录功能
  ```bash
  # 查看日志确认记录成功
  tail -f api/logs/app.log | grep "token usage"
  ```

### 3.2 方式 B: ModelManager 集成（可选）

- [ ] 在 `api/core/model_manager.py` 中添加新方法
  ```python
  def get_model_instance_with_quota_check(
      self,
      tenant_id: str,
      user_id: str,
      provider: str,
      model_type: ModelType,
      model: str,
      estimated_tokens: int = 1000,
  ) -> ModelInstance:
      # 实现配额检查和模型选择逻辑
      pass
  ```

- [ ] 更新调用方使用新方法

---

## 🧪 阶段 4: 测试验证

### 4.1 API 测试

- [ ] 测试配额检查 API
  ```bash
  curl -X POST http://localhost:5001/console/api/token-quota/check \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer YOUR_TOKEN" \
    -d '{"tokens_to_use": 1000}'
  ```
  **期望结果**: 返回配额信息，`within_quota: true`

- [ ] 测试记录使用 API
  ```bash
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
  ```
  **期望结果**: 返回 201，记录成功

- [ ] 测试查看当前使用 API
  ```bash
  curl -X GET http://localhost:5001/console/api/token-quota/usage/current \
    -H "Authorization: Bearer YOUR_TOKEN"
  ```
  **期望结果**: 返回当前时间窗口的使用情况

- [ ] 测试统计 API
  ```bash
  curl -X GET "http://localhost:5001/console/api/token-quota/usage/statistics?start_date=2026-05-01&end_date=2026-05-31" \
    -H "Authorization: Bearer YOUR_TOKEN"
  ```
  **期望结果**: 返回统计信息

### 4.2 集成测试

- [ ] 创建测试脚本 `api/test_quota_integration.py`
  ```python
  # 参考 TOKEN_QUOTA_INTEGRATION_GUIDE.md 中的测试脚本
  ```

- [ ] 运行集成测试
  ```bash
  cd api
  python -m uv run python test_quota_integration.py
  ```

- [ ] 验证测试结果
  - [ ] 配额检查正常
  - [ ] 模型选择正确
  - [ ] 使用记录成功
  - [ ] 日志输出正确

### 4.3 端到端测试

- [ ] 测试场景 1: 配额充足时使用云端模型
  1. [ ] 确认配额充足
  2. [ ] 发起 LLM 请求
  3. [ ] 验证使用了云端模型（如 openai/gpt-4）
  4. [ ] 验证使用已记录

- [ ] 测试场景 2: 配额不足时切换到本地模型
  1. [ ] 手动设置配额为较小值（如 1000 tokens）
  2. [ ] 发起多个 LLM 请求直到超过配额
  3. [ ] 验证自动切换到本地模型（如 ollama/llama2）
  4. [ ] 验证使用已记录

- [ ] 测试场景 3: 配额重置
  1. [ ] 等待时间窗口结束（或手动重置）
  2. [ ] 验证配额已重置
  3. [ ] 验证可以再次使用云端模型

### 4.4 性能测试

- [ ] 测试配额检查性能
  ```bash
  # 使用 ab 或 wrk 进行压力测试
  ab -n 1000 -c 10 -p check_quota.json -T application/json \
    http://localhost:5001/console/api/token-quota/check
  ```
  **期望结果**: 响应时间 < 100ms

- [ ] 测试记录使用性能
  ```bash
  ab -n 1000 -c 10 -p record_usage.json -T application/json \
    http://localhost:5001/console/api/token-quota/usage/record
  ```
  **期望结果**: 响应时间 < 200ms

---

## 🎨 阶段 5: 前端集成（可选）

### 5.1 创建配额显示组件

- [ ] 创建 `web/app/components/header/TokenQuotaIndicator.tsx`
  ```typescript
  // 参考 TOKEN_QUOTA_INTEGRATION_GUIDE.md 中的代码
  ```

- [ ] 在 Header 中使用组件
  ```typescript
  import TokenQuotaIndicator from './TokenQuotaIndicator'
  ```

- [ ] 测试组件显示
  - [ ] 配额充足时显示绿色
  - [ ] 配额不足时显示黄色/红色
  - [ ] 配额用完时显示警告

### 5.2 创建配额管理页面（可选）

- [ ] 创建页面路由 `web/app/(commonLayout)/token-quota/page.tsx`

- [ ] 实现功能
  - [ ] 查看配额配置列表
  - [ ] 创建新配额配置
  - [ ] 编辑配额配置
  - [ ] 删除配额配置
  - [ ] 查看使用统计
  - [ ] 查看历史记录

- [ ] 添加图表展示
  - [ ] 配额使用趋势图
  - [ ] 模型使用分布图
  - [ ] 时间窗口使用对比

---

## 📊 阶段 6: 监控和告警（可选）

### 6.1 日志监控

- [ ] 配置日志级别
  ```python
  # api/extensions/ext_logging.py
  logger.setLevel(logging.INFO)
  ```

- [ ] 添加关键日志
  - [ ] 配额检查日志
  - [ ] 模型切换日志
  - [ ] 配额超限日志
  - [ ] 使用记录日志

- [ ] 配置日志聚合（可选）
  - [ ] ELK Stack
  - [ ] Grafana Loki
  - [ ] CloudWatch Logs

### 6.2 指标监控

- [ ] 配置 Prometheus 指标（可选）
  ```python
  from prometheus_client import Counter, Histogram
  
  quota_check_counter = Counter('token_quota_checks_total', 'Total quota checks')
  quota_exceeded_counter = Counter('token_quota_exceeded_total', 'Total quota exceeded')
  model_switch_counter = Counter('model_switches_total', 'Total model switches')
  ```

- [ ] 创建 Grafana 仪表板（可选）
  - [ ] 配额使用率
  - [ ] 模型切换次数
  - [ ] API 响应时间
  - [ ] 错误率

### 6.3 告警配置

- [ ] 配置告警规则
  - [ ] 配额使用超过 80%
  - [ ] 配额使用超过 90%
  - [ ] 配额已用完
  - [ ] API 错误率过高

- [ ] 配置告警通知
  - [ ] 邮件通知
  - [ ] Slack 通知
  - [ ] 钉钉通知
  - [ ] 企业微信通知

---

## 📝 阶段 7: 文档和培训

### 7.1 更新文档

- [ ] 更新 API 文档
  - [ ] Swagger/OpenAPI 规范
  - [ ] API 使用示例
  - [ ] 错误码说明

- [ ] 更新用户文档
  - [ ] 配额系统介绍
  - [ ] 使用指南
  - [ ] 常见问题

- [ ] 更新开发文档
  - [ ] 架构设计
  - [ ] 集成指南
  - [ ] 故障排查

### 7.2 团队培训

- [ ] 准备培训材料
  - [ ] PPT 演示
  - [ ] 演示视频
  - [ ] 实操手册

- [ ] 组织培训会议
  - [ ] 系统概述
  - [ ] 功能演示
  - [ ] Q&A 环节

- [ ] 收集反馈
  - [ ] 功能建议
  - [ ] 问题反馈
  - [ ] 改进意见

---

## 🚀 阶段 8: 上线部署

### 8.1 预发布检查

- [ ] 代码审查
  - [ ] 代码质量
  - [ ] 安全性检查
  - [ ] 性能优化

- [ ] 测试覆盖
  - [ ] 单元测试通过
  - [ ] 集成测试通过
  - [ ] 端到端测试通过

- [ ] 数据库准备
  - [ ] 备份现有数据
  - [ ] 执行迁移脚本
  - [ ] 验证数据完整性

### 8.2 灰度发布

- [ ] 选择灰度用户
  - [ ] 内部测试用户
  - [ ] 友好用户

- [ ] 监控灰度期间
  - [ ] 错误率
  - [ ] 性能指标
  - [ ] 用户反馈

- [ ] 逐步扩大范围
  - [ ] 10% 用户
  - [ ] 50% 用户
  - [ ] 100% 用户

### 8.3 全量发布

- [ ] 发布公告
  - [ ] 功能介绍
  - [ ] 使用指南
  - [ ] 注意事项

- [ ] 监控系统
  - [ ] 实时监控
  - [ ] 告警响应
  - [ ] 问题处理

- [ ] 收集反馈
  - [ ] 用户满意度
  - [ ] 功能建议
  - [ ] Bug 报告

---

## 🔍 阶段 9: 持续优化

### 9.1 性能优化

- [ ] 数据库优化
  - [ ] 索引优化
  - [ ] 查询优化
  - [ ] 分区策略

- [ ] 缓存优化
  - [ ] Redis 缓存配额配置
  - [ ] 缓存使用记录
  - [ ] 缓存失效策略

- [ ] 代码优化
  - [ ] 减少数据库查询
  - [ ] 批量操作
  - [ ] 异步处理

### 9.2 功能增强

- [ ] 短期优化
  - [ ] 配额告警通知
  - [ ] 配额使用趋势预测
  - [ ] 多租户配额共享

- [ ] 中期优化
  - [ ] 按成本计费
  - [ ] 配额购买和充值
  - [ ] 配额转移和赠送

- [ ] 长期优化
  - [ ] AI 驱动的配额优化
  - [ ] 智能模型推荐
  - [ ] 成本优化建议

### 9.3 数据分析

- [ ] 使用分析
  - [ ] 配额使用趋势
  - [ ] 模型使用分布
  - [ ] 用户行为分析

- [ ] 成本分析
  - [ ] Token 成本统计
  - [ ] 模型成本对比
  - [ ] ROI 分析

- [ ] 优化建议
  - [ ] 配额调整建议
  - [ ] 模型选择建议
  - [ ] 成本节约建议

---

## ✅ 完成标准

### 必需项（核心功能）
- [ ] 数据库表已创建
- [ ] 默认配额已初始化
- [ ] LLM 调用前检查配额
- [ ] LLM 调用后记录使用
- [ ] 配额不足时自动切换模型
- [ ] API 接口可用
- [ ] 基本测试通过

### 可选项（增强功能）
- [ ] 前端配额显示
- [ ] 配额管理界面
- [ ] 监控和告警
- [ ] 性能优化
- [ ] 文档完善

---

## 📞 支持和帮助

### 文档资源
- `TOKEN_QUOTA_SYSTEM.md` - 完整系统文档
- `TOKEN_QUOTA_QUICK_START.md` - 快速开始指南
- `TOKEN_QUOTA_INTEGRATION_GUIDE.md` - 集成指南
- `TOKEN_QUOTA_FLOW_DIAGRAM.md` - 流程图

### 常见问题
1. **配额检查失败** - 检查数据库连接和表是否存在
2. **模型切换不生效** - 检查本地模型是否可用
3. **使用未记录** - 检查 `record_token_usage` 是否被调用

### 技术支持
- 查看日志: `tail -f api/logs/app.log`
- 查看数据库: `psql -d your_database`
- 运行测试: `python -m pytest tests/ -v`

---

## 🎉 总结

完成这个检查清单后，你将拥有一个完整的 Token 配额管理系统，能够：

✅ 自动检查配额并选择合适的模型  
✅ 详细记录每次 Token 使用  
✅ 提供完整的统计和分析功能  
✅ 支持灵活的配额配置  
✅ 实现成本控制和资源管理  

**祝你集成顺利！** 🚀
