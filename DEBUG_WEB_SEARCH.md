# 联网搜索功能调试指南

## 当前状态

已完成的实现：
1. ✅ 前端：添加了"联网搜索"复选框开关
2. ✅ 前端：添加了 `enableWebSearch` 状态管理
3. ✅ 前端：修改了 `sendSimpleChatMessage` 函数，支持 `webSearch` 参数
4. ✅ 后端：在 `SimpleChatPayload` 中添加了 `web_search` 字段
5. ✅ 后端：实现了 `_perform_web_search` 方法
6. ✅ 后端：添加了搜索结果集成到系统提示的逻辑
7. ✅ 添加了详细的调试日志（前端和后端）

## 问题

用户测试后发现联网搜索功能没有生效：
- AI 回答仍然说"我无法直接获取实时新闻"
- 后端日志中没有看到 `/console/api/simple-chat` 的请求

## 调试步骤

### 1. 打开浏览器开发者工具

1. 在浏览器中打开 http://localhost:3000/chat
2. 按 F12 打开开发者工具
3. 切换到 "Console" 标签

### 2. 测试联网搜索功能

1. 勾选"联网搜索"复选框
   - 应该在控制台看到：`[Chat Page] Web search toggled: true`

2. 输入一个需要实时信息的问题，例如：
   - "今天有什么新闻？"
   - "2026年5月9日发生了什么？"

3. 点击"发送回复"

### 3. 检查控制台日志

应该看到以下日志（按顺序）：

```
[Chat Page] Web search toggled: true
[Chat Page - Send] Calling sendSimpleChatMessage with webSearch: true
[Simple Chat] Sending request: {url: "...", webSearch: true, body: {...}}
[Simple Chat] Response status: 200 OK
[Chat Page - Send] sendSimpleChatMessage completed
```

### 4. 检查网络请求

1. 切换到 "Network" 标签
2. 找到 `simple-chat` 请求
3. 点击查看详情：
   - **Request Headers**: 检查是否包含正确的 CSRF token
   - **Request Payload**: 检查 `web_search` 字段是否为 `true`
   - **Response**: 检查返回的内容

### 5. 检查后端日志

在后端终端（Flask API 进程）中应该看到：

```
INFO [Simple Chat] Received request - web_search: True, query: 今天有什么新闻...
INFO [Simple Chat] Web search enabled, performing search...
INFO [Simple Chat] Search results: ...
INFO [Simple Chat] Added search results to system prompt
```

## 可能的问题和解决方案

### 问题 1: 前端没有发送请求

**症状**: 控制台没有 `[Simple Chat] Sending request` 日志

**可能原因**:
- 代码没有编译
- 浏览器缓存了旧代码

**解决方案**:
1. 硬刷新浏览器：Ctrl+Shift+R (Windows) 或 Cmd+Shift+R (Mac)
2. 清除浏览器缓存
3. 检查 Next.js 编译输出

### 问题 2: CSRF Token 错误

**症状**: 控制台显示 403 或 401 错误

**解决方案**:
1. 刷新页面重新获取 CSRF token
2. 检查 Cookie 设置

### 问题 3: 后端没有收到请求

**症状**: 前端发送了请求，但后端日志中没有记录

**可能原因**:
- API 路由配置错误
- CORS 问题
- 代理配置问题

**解决方案**:
1. 检查 API_PREFIX 配置：应该是 `http://localhost:5001/console/api`
2. 检查后端路由注册：`/console/api/simple-chat`
3. 检查 Flask 是否正在运行

### 问题 4: 搜索结果为空

**症状**: 后端执行了搜索，但返回空结果

**可能原因**:
- DuckDuckGo API 限制
- 网络连接问题
- 查询格式不支持

**解决方案**:
1. 检查网络连接
2. 尝试不同的查询
3. 考虑使用其他搜索 API（如 SerpAPI、Google Custom Search）

### 问题 5: AI 没有使用搜索结果

**症状**: 搜索成功，但 AI 回答中没有体现搜索结果

**可能原因**:
- 搜索结果没有正确添加到系统提示
- 模型忽略了系统提示中的信息

**解决方案**:
1. 检查后端日志，确认搜索结果已添加到系统提示
2. 尝试更明确的提示词，例如："请根据以上搜索结果回答..."
3. 检查模型是否支持系统提示

## 当前文件位置

- 前端服务层: `web/service/chat.ts`
- 前端页面: `web/app/(commonLayout)/chat/page.tsx`
- 后端 API: `api/controllers/console/chat/simple_chat.py`
- 配置文件: `web/config/index.ts`

## 下一步

1. 按照上述步骤进行调试
2. 收集控制台日志和网络请求信息
3. 根据日志确定问题所在
4. 如果需要，可以考虑：
   - 使用更可靠的搜索 API
   - 改进搜索结果的格式化
   - 优化系统提示的构建方式
