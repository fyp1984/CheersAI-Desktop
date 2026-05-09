# 🚀 Tavily 联网搜索 - 快速开始

## 3 步启用联网搜索

### 第 1 步：获取 API Key（2 分钟）

1. 访问 https://tavily.com
2. 点击 "Sign Up" 注册（可以用 Google 账号快速登录）
3. 登录后在 Dashboard 找到 API Key
4. 复制 API Key（格式：`tvly-xxxxxxxxxxxxxxxxxxxxxxxx`）

### 第 2 步：配置 API Key（1 分钟）

在 `api/.env` 文件中添加一行：

```bash
TAVILY_API_KEY=tvly-your-api-key-here
```

**重要**：替换 `tvly-your-api-key-here` 为你的真实 API Key

### 第 3 步：重启服务（1 分钟）

在终端中按 `Ctrl+C` 停止 Flask API，然后重新启动：

```bash
cd api
python app.py
```

## ✅ 测试搜索功能

### 方法 1：使用测试脚本（推荐）

```bash
cd api
python test_tavily.py
```

如果看到 "✅ 所有测试通过！"，说明配置成功！

### 方法 2：在聊天页面测试

1. 打开 http://localhost:3000/chat
2. 勾选"联网搜索"复选框
3. 输入问题："今天娱乐圈有什么新闻？"
4. 查看 AI 基于真实搜索结果的回答

## 📊 预期结果

AI 会返回类似这样的回答：

```
关于「今天娱乐圈有什么新闻」的搜索结果：

📌 快速答案：今天娱乐圈的主要新闻包括...

1. [真实新闻标题]
   [真实新闻摘要]
   来源：https://example.com/news
   相关度：0.95

2. [真实新闻标题]
   [真实新闻摘要]
   来源：https://example.com/news2
   相关度：0.88

搜索时间：2026年05月09日 18:30:00
星期六
搜索引擎：Tavily AI Search
```

## 🎯 关键特性

- ✅ **真正的联网搜索** - 不是假的，是真实的网络搜索
- ✅ **AI 自主决策** - AI 自己判断何时需要搜索
- ✅ **免费额度充足** - 每月 1,000 次搜索
- ✅ **非常可靠** - 不会被屏蔽，99.9% 可用性
- ✅ **专为 AI 优化** - 返回的结果专门为 LLM 设计

## 🛠️ 故障排查

### 问题：显示"未配置 TAVILY_API_KEY"

**解决方案**：
1. 检查 `api/.env` 文件是否包含 `TAVILY_API_KEY=tvly-...`
2. 确保 API Key 以 `tvly-` 开头
3. 重启 Flask API 服务

### 问题：显示"tavily-python not installed"

**解决方案**：
```bash
cd api
pip install tavily-python
```

### 问题：搜索失败，401 错误

**解决方案**：
1. API Key 无效或过期
2. 登录 https://app.tavily.com 检查 API Key
3. 重新生成新的 API Key

### 问题：AI 没有调用搜索

**解决方案**：
1. 确保勾选了"联网搜索"复选框
2. 尝试更明确的问题（如"今天的新闻"）
3. 检查后端日志是否有错误

## 📚 更多信息

- **完整设置指南**: 查看 `TAVILY_SETUP_GUIDE.md`
- **实现细节**: 查看 `WEB_SEARCH_IMPLEMENTATION_COMPLETE.md`
- **测试脚本**: 运行 `python api/test_tavily.py`

## 💡 使用建议

1. **只在需要实时信息时使用**
   - 今天的新闻、天气、股票等
   - 最新的技术进展、产品发布等
   - 当前的事件、趋势等

2. **不需要搜索的问题**
   - 概念性问题（"什么是人工智能？"）
   - 历史事件（"第二次世界大战何时结束？"）
   - 编程语法（"Python 如何定义函数？"）

3. **让 AI 自己决定**
   - 勾选"联网搜索"后，AI 会自己判断是否需要搜索
   - 不需要每次都搜索，更智能、更节省配额

## 🎉 完成！

现在你有了一个真正的、可靠的联网搜索功能！

**开始使用吧！** 🚀

---

**问题或反馈？**
- 查看完整文档：`TAVILY_SETUP_GUIDE.md`
- 运行测试脚本：`python api/test_tavily.py`
- 访问 Tavily 文档：https://docs.tavily.com
