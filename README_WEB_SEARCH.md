# 🌐 联网搜索功能 - 使用指南

## 🎯 功能说明

这是一个**真正的联网搜索功能**，使用 **Tavily AI Search API**：

- ✅ **真实搜索** - 从互联网获取最新信息
- ✅ **AI 智能** - AI 自己决定何时需要搜索
- ✅ **专为 AI 优化** - 返回的结果专门为 LLM 设计
- ✅ **免费使用** - 每月 1,000 次免费搜索
- ✅ **非常可靠** - 99.9% 可用性，不会被屏蔽

## 🚀 3 步启用

### 步骤 1️⃣：获取 API Key

```
访问 https://tavily.com
  ↓
注册账号（可用 Google 快速登录）
  ↓
在 Dashboard 获取 API Key
  ↓
复制 API Key（格式：tvly-xxxxxxxx）
```

### 步骤 2️⃣：配置 API Key

在 `api/.env` 文件中添加：

```bash
TAVILY_API_KEY=tvly-your-api-key-here
```

**重要**：替换为你的真实 API Key！

### 步骤 3️⃣：重启服务

```bash
# 在 Flask API 终端按 Ctrl+C 停止
# 然后重新启动
cd api
python app.py
```

## ✅ 测试功能

### 方法 1：运行测试脚本（推荐）

```bash
cd api
python test_tavily.py
```

**预期输出**：
```
============================================================
Tavily API 测试脚本
============================================================

1️⃣  检查 tavily-python 包...
   ✅ tavily-python 已安装

2️⃣  检查 TAVILY_API_KEY 环境变量...
   ✅ TAVILY_API_KEY 已配置: tvly-xxxxx...

3️⃣  测试 Tavily API 连接...
   ✅ Tavily 客户端初始化成功

4️⃣  执行测试搜索...
   搜索查询: Python programming language
   ✅ 搜索成功！

   📊 搜索结果：
   --------------------------------------------------------
   📌 快速答案: Python is a high-level programming...
   
   找到 3 个结果：
   1. Python (programming language) - Wikipedia
      URL: https://en.wikipedia.org/wiki/Python_(programming_language)
      相关度: 0.98
   ...

============================================================
✅ 所有测试通过！Tavily API 配置正确且工作正常。
============================================================
```

### 方法 2：在聊天页面测试

1. 打开 http://localhost:3000/chat
2. 勾选 **"联网搜索"** 复选框
3. 输入问题：**"今天娱乐圈有什么新闻？"**
4. 查看 AI 的回答

**预期回答**：
```
关于「今天娱乐圈有什么新闻」的搜索结果：

📌 快速答案：今天娱乐圈的主要新闻包括...

1. [真实新闻标题]
   [真实新闻摘要内容]
   来源：https://example.com/news
   相关度：0.95

2. [真实新闻标题]
   [真实新闻摘要内容]
   来源：https://example.com/news2
   相关度：0.88

搜索时间：2026年05月09日 18:30:00
星期六
搜索引擎：Tavily AI Search
```

## 💡 使用建议

### 适合使用联网搜索的问题

✅ **实时信息**
- "今天有什么新闻？"
- "最新的 AI 技术进展"
- "今天的天气怎么样？"

✅ **当前事件**
- "2026年5月9日发生了什么？"
- "最近的科技新闻"
- "今天娱乐圈有什么消息？"

✅ **最新数据**
- "比特币现在的价格"
- "最新的 Python 版本"
- "今天的股市行情"

### 不需要联网搜索的问题

❌ **概念性问题**
- "什么是人工智能？"
- "如何学习编程？"

❌ **历史事件**
- "第二次世界大战何时结束？"
- "谁发明了电话？"

❌ **编程语法**
- "Python 如何定义函数？"
- "JavaScript 的闭包是什么？"

### 智能决策

勾选"联网搜索"后，**AI 会自己判断**是否需要搜索：
- 需要实时信息 → AI 自动搜索
- 不需要实时信息 → AI 直接回答
- 更智能、更节省配额

## 🛠️ 故障排查

### ❌ 显示"未配置 TAVILY_API_KEY"

**原因**：环境变量未设置

**解决方案**：
1. 检查 `api/.env` 文件
2. 确保包含：`TAVILY_API_KEY=tvly-...`
3. 确保 API Key 以 `tvly-` 开头
4. 重启 Flask API

### ❌ 显示"tavily-python not installed"

**原因**：Python 包未安装

**解决方案**：
```bash
cd api
pip install tavily-python
```

### ❌ 搜索失败，401 错误

**原因**：API Key 无效或过期

**解决方案**：
1. 登录 https://app.tavily.com
2. 检查 API Key 是否正确
3. 重新生成新的 API Key
4. 更新 `.env` 文件
5. 重启服务

### ❌ 搜索失败，429 错误

**原因**：超过每月 1,000 次配额

**解决方案**：
1. 登录 https://app.tavily.com 查看使用量
2. 等待下个月配额重置
3. 或升级到付费计划

### ❌ AI 没有调用搜索

**原因**：AI 判断不需要搜索，或模型不支持

**解决方案**：
1. 确保勾选了"联网搜索"复选框
2. 使用更明确需要实时信息的问题
3. 检查后端日志是否有错误
4. 确认模型支持 Function Calling

## 📊 使用配额

### 免费计划

- **每月 1,000 次搜索**
- 每次搜索消耗 1 个 credit
- 足够个人和小团队使用

### 查看使用量

登录 https://app.tavily.com 查看：
- 当前月份使用量
- 剩余配额
- 使用历史

### 付费计划

如果免费额度不够：
- **Starter**: $29/月，5,000 次
- **Pro**: $99/月，20,000 次
- **Enterprise**: 自定义

## 📚 更多文档

| 文档 | 说明 |
|------|------|
| `QUICK_START_TAVILY.md` | 快速开始指南 |
| `TAVILY_SETUP_GUIDE.md` | 完整设置和使用指南 |
| `WEB_SEARCH_IMPLEMENTATION_COMPLETE.md` | 技术实现细节 |
| `IMPLEMENTATION_SUMMARY.md` | 实现总结 |
| `api/test_tavily.py` | API 测试脚本 |

## 🔍 工作原理

```
用户输入问题 + 勾选"联网搜索"
         ↓
    前端发送请求
         ↓
  后端告诉 AI 有搜索工具可用
         ↓
   AI 自己判断是否需要搜索
         ↓
  如果需要：AI 调用 web_search()
         ↓
   后端执行 Tavily API 搜索
         ↓
    返回真实搜索结果给 AI
         ↓
  AI 基于搜索结果生成回答
         ↓
      显示给用户
```

## 🎯 关键特性

### 1. AI 自主决策

AI 自己判断是否需要搜索，不是每次都搜索：
- 更智能
- 更节省配额
- 更好的用户体验

### 2. 专为 AI 优化

Tavily 返回的结果专门为 LLM 设计：
- 包含标题、摘要、URL
- 包含相关度评分（0-1）
- 包含 AI 生成的快速答案
- 格式清晰，易于理解

### 3. 非常可靠

- 99.9% 可用性
- 不会被屏蔽
- 响应速度快（1-2 秒）
- 全球 CDN 加速

## 📞 获取帮助

### 测试脚本

```bash
cd api
python test_tavily.py
```

### 查看日志

后端日志会显示：
```
[Simple Chat] Web search tool enabled
[Simple Chat] AI requested web search: [查询内容]
[Simple Chat] Using Tavily AI Search for query: [查询内容]
[Simple Chat] Successfully got 5 results from Tavily
```

### 参考资源

- **Tavily 官网**: https://tavily.com
- **API 文档**: https://docs.tavily.com
- **Dashboard**: https://app.tavily.com
- **Python SDK**: https://github.com/tavily-ai/tavily-python

## ✨ 总结

### 已实现的功能

✅ 真正的联网搜索（不是假的）
✅ AI 自主决策何时搜索
✅ 专为 AI 优化的搜索结果
✅ 免费额度充足（1000次/月）
✅ 非常可靠（99.9% 可用性）
✅ 完整的错误处理
✅ 详细的日志记录
✅ 测试工具和文档

### 用户需要做的

1️⃣ 获取 Tavily API Key（2 分钟）
2️⃣ 配置环境变量（1 分钟）
3️⃣ 重启 Flask API（1 分钟）
4️⃣ 开始使用！

---

## 🚀 现在就开始使用吧！

1. 访问 https://tavily.com 获取 API Key
2. 在 `api/.env` 中配置 `TAVILY_API_KEY`
3. 运行 `python api/test_tavily.py` 测试
4. 重启 Flask API
5. 打开聊天页面，勾选"联网搜索"，开始使用！

**这是一个真正的、可靠的、为 AI 优化的联网搜索解决方案！** 🎉
