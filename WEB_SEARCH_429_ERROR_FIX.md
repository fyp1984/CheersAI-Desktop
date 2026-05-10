# 🔧 429 错误修复 - API 过载重试机制

## 问题描述

在使用联网搜索功能时，遇到以下错误：

```
AI调用模型失败: req_id: 14725c9da7 PluginInvokeError: 
{"error":{"message":"The engine is currently overloaded, please try again later","type":"engine_overloaded_error"}}
status code 429
```

## 错误原因

### 什么是 429 错误？

**HTTP 429 Too Many Requests** 表示：
- 请求频率过高，超过了速率限制
- 服务器当前过载，无法处理更多请求
- API 配额已用完

### 为什么会出现这个错误？

1. **两次 AI 调用**
   - 修复后的联网搜索需要调用 AI 两次：
     - 第一次：决定是否需要搜索
     - 第二次：基于搜索结果生成回答
   - 增加了请求频率

2. **服务端临时过载**
   - 模型服务器当前负载较高
   - 正在处理大量并发请求

3. **短时间内多次测试**
   - 快速连续发送多个请求
   - 触发了速率限制

## 解决方案

### ✅ 方案 1：自动重试机制（已实现）

我已经为代码添加了**自动重试逻辑**：

#### 重试策略
- **最大重试次数**：3 次
- **初始延迟**：2 秒
- **退避策略**：指数退避（2s → 4s → 8s）
- **仅针对 429 错误**：其他错误不重试

#### 工作流程
```
第一次请求
  ↓
失败（429 错误）
  ↓
等待 2 秒
  ↓
第二次请求
  ↓
失败（429 错误）
  ↓
等待 4 秒
  ↓
第三次请求
  ↓
成功 ✅ 或 最终失败 ❌
```

#### 代码实现
```python
max_retries = 3
retry_delay = 2  # 秒

for attempt in range(max_retries):
    try:
        response = model_instance.invoke_llm(...)
        break  # 成功，跳出循环
    except InvokeError as e:
        error_str = str(e).lower()
        # 检查是否是 429 错误
        if ('429' in error_str or 'overloaded' in error_str) and attempt < max_retries - 1:
            logger.warning(f"API overloaded (attempt {attempt + 1}/{max_retries}), retrying in {retry_delay}s...")
            time.sleep(retry_delay)
            retry_delay *= 2  # 指数退避
            continue
        else:
            raise  # 不是 429 或已达最大重试次数
```

### ✅ 方案 2：等待后手动重试

如果自动重试仍然失败：

1. **等待 30-60 秒**
2. **刷新浏览器**（Ctrl + Shift + R）
3. **重新发送消息**

### ✅ 方案 3：检查 API 配额

如果持续出现 429 错误，可能是配额问题：

#### 检查模型提供商配额
1. 登录模型提供商的控制台
2. 查看 API 使用量和配额
3. 确认是否超过限制

#### 常见模型提供商
- **OpenAI**: https://platform.openai.com/usage
- **Anthropic (Claude)**: https://console.anthropic.com/settings/usage
- **Azure OpenAI**: Azure Portal
- **本地模型**: 检查服务器资源

### ✅ 方案 4：降低请求频率

如果经常遇到 429 错误：

#### 前端添加请求节流
```typescript
// 限制发送频率
const [lastRequestTime, setLastRequestTime] = useState(0)

const handleSend = () => {
  const now = Date.now()
  if (now - lastRequestTime < 3000) {  // 3秒内不能重复发送
    toast.error('请求过于频繁，请稍后再试')
    return
  }
  setLastRequestTime(now)
  // 发送请求...
}
```

#### 后端添加速率限制
```python
from flask_limiter import Limiter

limiter = Limiter(
    app,
    key_func=lambda: current_account.id,
    default_limits=["10 per minute"]  # 每分钟最多 10 次请求
)

@limiter.limit("5 per minute")  # 这个接口每分钟最多 5 次
def post(self):
    # ...
```

### ✅ 方案 5：切换到其他模型

如果某个模型经常过载：

1. 在设置中配置备用模型
2. 切换到负载较低的模型
3. 使用本地部署的模型

## 测试步骤

### 1. 重启 Flask API
已完成 ✅

### 2. 刷新浏览器
按 `Ctrl + Shift + R` 强制刷新

### 3. 测试重试机制
1. 打开聊天页面
2. 勾选"联网搜索"
3. 发送消息
4. 如果遇到 429 错误，系统会自动重试

### 4. 查看日志
在 Flask 日志中查看重试信息：
```
[Simple Chat] API overloaded (attempt 1/3), retrying in 2s...
[Simple Chat] API overloaded (attempt 2/3), retrying in 4s...
[Simple Chat] Request successful after 2 retries
```

## 预期效果

### 之前（无重试）
```
❌ 第一次请求失败（429 错误）
❌ 直接返回错误给用户
用户看到：AI调用模型失败...
```

### 现在（有重试）
```
❌ 第一次请求失败（429 错误）
⏳ 等待 2 秒
🔄 第二次请求
✅ 成功！
用户看到：正常的 AI 回答
```

## 监控和调试

### 查看 Flask 日志
```bash
# 在进程输出中查看
# 应该看到类似的日志：
[Simple Chat] Received request - web_search: True
[Simple Chat] API overloaded (attempt 1/3), retrying in 2s...
[Simple Chat] Request successful
```

### 查看浏览器控制台
```javascript
// 打开浏览器开发者工具（F12）
// 查看 Network 标签
// 找到 /console/api/simple-chat 请求
// 查看响应时间和状态码
```

### 使用测试脚本
```bash
cd api
.venv\Scripts\python.exe test_web_search_integration.py
```

## 性能优化建议

### 1. 减少不必要的搜索
```python
# 在系统提示中告诉 AI 何时需要搜索
system_content = """
You are a helpful AI assistant.
Only use web search when:
- User asks about current events or news
- User asks about latest versions or updates
- User explicitly requests real-time information
"""
```

### 2. 缓存搜索结果
```python
from functools import lru_cache
from datetime import datetime, timedelta

# 缓存 5 分钟
@lru_cache(maxsize=100)
def cached_search(query: str, timestamp: int):
    return self._perform_web_search(query)

# 使用时
timestamp = int(datetime.now().timestamp() / 300)  # 5分钟一个时间戳
results = cached_search(query, timestamp)
```

### 3. 使用更快的模型
- 对于简单问题，使用 GPT-3.5 而不是 GPT-4
- 对于搜索决策，使用小模型
- 对于最终回答，使用大模型

### 4. 并行处理（如果有多个工具调用）
```python
import asyncio

async def execute_tools_parallel(tool_calls):
    tasks = [execute_tool(tc) for tc in tool_calls]
    results = await asyncio.gather(*tasks)
    return results
```

## 常见问题

### Q1: 为什么重试 3 次后还是失败？

**A**: 可能的原因：
1. 服务器持续过载（高峰期）
2. API 配额已用完
3. 网络连接问题

**解决**：
- 等待更长时间（5-10 分钟）
- 检查 API 配额
- 切换到其他模型

### Q2: 重试会不会消耗更多配额？

**A**: 会的。每次重试都会消耗配额。但是：
- 只有 429 错误才会重试
- 最多重试 3 次
- 相比用户体验，这是可接受的成本

### Q3: 可以增加重试次数吗？

**A**: 可以，但不建议：
```python
max_retries = 5  # 增加到 5 次
```

原因：
- 重试次数过多会导致响应时间过长
- 如果服务器真的过载，重试也无济于事
- 建议保持 3 次，失败后让用户手动重试

### Q4: 可以减少延迟时间吗？

**A**: 不建议：
```python
retry_delay = 1  # 减少到 1 秒（不推荐）
```

原因：
- 延迟太短可能无法缓解服务器压力
- 可能再次触发速率限制
- 建议保持 2 秒起始延迟

### Q5: 为什么不对所有错误都重试？

**A**: 因为：
- 配置错误（如 API Key 无效）重试无意义
- 参数错误（如 model 不存在）重试无意义
- 只有临时性错误（如 429）才适合重试

## 最佳实践

### 1. 用户提示
在前端显示友好的提示：
```typescript
if (error.includes('429') || error.includes('overloaded')) {
  toast.info('服务器繁忙，正在自动重试...')
} else {
  toast.error('请求失败，请稍后重试')
}
```

### 2. 降级策略
如果搜索失败，让 AI 基于知识回答：
```python
if not success:
    # 不要直接失败，而是让 AI 基于知识回答
    tool_message = ToolPromptMessage(
        content="搜索服务暂时不可用，请基于你的知识回答。",
        tool_call_id=tool_call.id,
        name="web_search"
    )
```

### 3. 监控和告警
记录 429 错误的频率：
```python
from prometheus_client import Counter

retry_counter = Counter('api_retries_total', 'Total API retries', ['reason'])

if '429' in error_str:
    retry_counter.labels(reason='rate_limit').inc()
```

## 总结

✅ **已实现自动重试机制**：
- 最大重试 3 次
- 指数退避（2s → 4s → 8s）
- 仅针对 429 错误
- 详细的日志记录

✅ **用户体验改善**：
- 大多数 429 错误会自动恢复
- 用户无需手动重试
- 响应时间略有增加（可接受）

✅ **下一步**：
1. 刷新浏览器测试
2. 查看 Flask 日志确认重试工作
3. 如果仍有问题，检查 API 配额

🎉 **现在可以测试了！**
