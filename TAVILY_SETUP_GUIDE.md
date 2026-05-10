# 🚀 Tavily AI Search 集成指南

## 什么是 Tavily？

**Tavily AI Search** 是专门为 AI 应用设计的搜索 API：
- ✅ **专为 AI 优化**：返回的结果格式专门为 LLM 消费优化
- ✅ **免费额度充足**：每月免费 1,000 次搜索
- ✅ **非常可靠**：不会被屏蔽，速度快
- ✅ **包含 AI 答案**：自动生成答案摘要
- ✅ **相关度评分**：每个结果都有相关度分数

## 为什么选择 Tavily？

### 对比其他方案

| 特性 | Tavily | SearxNG | Google/Bing | SerpAPI |
|------|--------|---------|--------------|---------|
| 为 AI 优化 | ✅ 是 | ❌ 否 | ❌ 否 | ⚠️ 部分 |
| 免费额度 | ✅ 1000次/月 | ✅ 无限 | ❌ 无 | ⚠️ 100次/月 |
| 可靠性 | ✅ 非常高 | ⚠️ 依赖公共实例 | ❌ 经常被屏蔽 | ✅ 非常高 |
| 访问限制 | ✅ 无 | ⚠️ 部分实例限制 | ❌ 被屏蔽 | ✅ 无 |
| 答案摘要 | ✅ 内置 | ❌ 无 | ❌ 无 | ❌ 无 |
| 相关度评分 | ✅ 有 | ❌ 无 | ❌ 无 | ⚠️ 部分 |

## 🔧 设置步骤

### 1. 注册 Tavily 账号

1. 访问 [Tavily 官网](https://tavily.com)
2. 点击 "Sign Up" 注册账号
3. 验证邮箱
4. 登录后进入 Dashboard

### 2. 获取 API Key

1. 在 Dashboard 中找到 "API Keys" 部分
2. 复制你的 API Key（格式：`tvly-xxxxxxxxxxxxxxxxxxxxxxxx`）
3. **重要**：妥善保管 API Key，不要泄露

### 3. 配置环境变量

#### 方法 1：在 `.env` 文件中添加（推荐）

在 `api/.env` 文件中添加：

```bash
# Tavily AI Search API
TAVILY_API_KEY=tvly-your-api-key-here
```

#### 方法 2：在系统环境变量中设置

**Windows (PowerShell)**:
```powershell
$env:TAVILY_API_KEY="tvly-your-api-key-here"
```

**Linux/Mac**:
```bash
export TAVILY_API_KEY="tvly-your-api-key-here"
```

### 4. 重启 Flask API

配置完成后，重启 Flask API 服务：

```bash
# 停止当前服务（Ctrl+C）
# 然后重新启动
cd api
python app.py
```

## ✅ 测试搜索功能

### 1. 打开聊天页面

访问：http://localhost:3000/chat

### 2. 勾选"联网搜索"

在输入框上方勾选"联网搜索"复选框

### 3. 输入需要实时信息的问题

测试问题示例：
- "今天娱乐圈有什么新闻？"
- "2026年5月9日发生了什么？"
- "最新的 AI 技术进展"
- "今天的天气怎么样？"

### 4. 查看结果

AI 会：
1. 自动判断是否需要搜索
2. 调用 Tavily 搜索 API
3. 基于真实搜索结果生成回答

**预期输出示例**：

```
关于「今天娱乐圈有什么新闻」的搜索结果：

📌 快速答案：今天娱乐圈的主要新闻包括...

1. [新闻标题]
   [新闻摘要内容]
   来源：https://example.com/news
   相关度：0.95

2. [新闻标题]
   [新闻摘要内容]
   来源：https://example.com/news2
   相关度：0.88

...

搜索时间：2026年05月09日 18:30:00
星期六
搜索引擎：Tavily AI Search
```

## 📊 使用配额

### 免费计划

- **每月 1,000 次搜索**
- 每次搜索消耗 1 个 credit（使用 `search_depth="basic"`）
- 如果使用 `search_depth="advanced"`，每次消耗 2 个 credits

### 查看使用情况

1. 登录 [Tavily Dashboard](https://app.tavily.com)
2. 查看 "Usage" 部分
3. 可以看到当前月份的使用量

### 升级计划

如果免费额度不够用，可以升级到付费计划：
- **Starter**: $29/月，5,000 次搜索
- **Pro**: $99/月，20,000 次搜索
- **Enterprise**: 自定义价格

## 🔍 工作原理

### AI 工具调用流程

```
用户输入问题 + 勾选"联网搜索"
  ↓
前端发送请求（web_search: true）
  ↓
后端告诉 AI 有 web_search 工具可用
  ↓
AI 自己决定是否需要搜索
  ↓
如果需要：AI 调用 web_search("搜索查询")
  ↓
后端执行 Tavily API 搜索
  ↓
返回搜索结果给 AI
  ↓
AI 基于真实搜索结果生成回答
```

### 关键特性

1. **AI 自主决策**
   - AI 自己判断是否需要搜索
   - 不是每次都搜索，只在需要时搜索
   - 更智能、更节省配额

2. **优化的结果**
   - Tavily 返回的结果专门为 LLM 优化
   - 包含标题、摘要、URL、相关度评分
   - 还包含 AI 生成的快速答案

3. **可靠性高**
   - 不会被屏蔽
   - 响应速度快（通常 1-2 秒）
   - 99.9% 可用性

## 🛠️ 高级配置

### 调整搜索深度

在 `api/controllers/console/chat/simple_chat.py` 中修改：

```python
response = client.search(
    query=query,
    search_depth="advanced",  # "basic" (1 credit) 或 "advanced" (2 credits)
    max_results=10,           # 增加结果数量
    include_answer=True,
    include_raw_content=False,
)
```

### 添加域名过滤

只搜索特定网站：

```python
response = client.search(
    query=query,
    include_domains=["wikipedia.org", "news.com"],  # 只搜索这些域名
    max_results=5,
)
```

排除特定网站：

```python
response = client.search(
    query=query,
    exclude_domains=["reddit.com", "quora.com"],  # 排除这些域名
    max_results=5,
)
```

### 按时间过滤

只搜索最近的结果：

```python
response = client.search(
    query=query,
    days=7,  # 只搜索最近 7 天的结果
    max_results=5,
)
```

## 🐛 故障排查

### 问题 1：显示"未配置 TAVILY_API_KEY"

**原因**：环境变量未设置

**解决方案**：
1. 检查 `api/.env` 文件是否包含 `TAVILY_API_KEY=tvly-...`
2. 确保 API Key 格式正确（以 `tvly-` 开头）
3. 重启 Flask API 服务

### 问题 2：显示"tavily-python not installed"

**原因**：Python 包未安装

**解决方案**：
```bash
cd api
pip install tavily-python
```

### 问题 3：搜索失败，显示 401 错误

**原因**：API Key 无效或过期

**解决方案**：
1. 登录 Tavily Dashboard 检查 API Key
2. 重新生成新的 API Key
3. 更新 `.env` 文件
4. 重启服务

### 问题 4：搜索失败，显示 429 错误

**原因**：超过配额限制

**解决方案**：
1. 登录 Tavily Dashboard 查看使用量
2. 等待下个月配额重置
3. 或升级到付费计划

### 问题 5：AI 没有调用搜索工具

**原因**：AI 模型可能不支持 Function Calling

**解决方案**：
1. 检查后端日志是否有 `[Simple Chat] AI requested web search`
2. 确认使用的模型支持 Function Calling（如 Moonshot、GPT-4、Claude 3）
3. 如果模型不支持，考虑切换模型

## 📚 参考资源

- **Tavily 官网**: https://tavily.com
- **API 文档**: https://docs.tavily.com
- **Python SDK**: https://github.com/tavily-ai/tavily-python
- **定价**: https://tavily.com/pricing
- **Dashboard**: https://app.tavily.com

## 🎯 最佳实践

1. **合理使用配额**
   - 只在需要实时信息时勾选"联网搜索"
   - 使用 `search_depth="basic"` 节省配额
   - 监控每月使用量

2. **优化搜索查询**
   - 让 AI 自己决定搜索查询（不要预先搜索）
   - AI 会根据用户问题构造更好的搜索查询

3. **处理搜索失败**
   - 代码已包含错误处理
   - 搜索失败时会显示友好的错误消息
   - 不会影响正常对话功能

4. **保护 API Key**
   - 不要将 API Key 提交到 Git
   - 使用 `.env` 文件（已在 `.gitignore` 中）
   - 定期轮换 API Key

## ✨ 总结

Tavily AI Search 是目前最适合 AI 应用的搜索解决方案：
- ✅ 专门为 AI 设计
- ✅ 免费额度充足
- ✅ 非常可靠
- ✅ 易于集成
- ✅ 结果质量高

相比之前尝试的 SearxNG、DuckDuckGo、Google 等方案，Tavily 是最稳定、最可靠的选择！

---

**现在就开始使用吧！** 🚀
