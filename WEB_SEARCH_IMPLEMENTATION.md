# 联网搜索功能实现说明

## 完成时间
2026-05-09

## 功能概述

成功实现了聊天页面的联网搜索功能，用户可以通过勾选"联网搜索"复选框来启用网络搜索，AI 将基于搜索结果提供更准确、更新的回答。

## 实现内容

### 1. 前端修改

#### 1.1 服务层 (`web/service/chat.ts`)

**修改内容**:
- 在 `sendSimpleChatMessage` 函数中添加 `options` 参数
- 支持传递 `webSearch` 标志到后端

```typescript
export const sendSimpleChatMessage = async (
  query: string,
  provider: string,
  model: string,
  history?: Array<{ type: 'user' | 'assistant', content: string }>,
  onData?: (data: string) => void,
  onError?: (error: string) => void,
  options?: { webSearch?: boolean },  // 新增参数
) => {
  // ...
  body: JSON.stringify({
    query,
    provider,
    model,
    history,
    web_search: options?.webSearch || false,  // 传递给后端
  }),
}
```

#### 1.2 聊天页面 (`web/app/(commonLayout)/chat/page.tsx`)

**修改内容**:
- 在两处调用 `sendSimpleChatMessage` 的地方添加 `{ webSearch: enableWebSearch }` 参数
- `handleRegenerateMessage` 函数（重新生成回复）
- `performSend` 函数（发送新消息）

```typescript
await sendSimpleChatMessage(
  queryWithFiles,
  resolvedSelectedModel.provider,
  resolvedSelectedModel.model,
  history,
  (content) => { /* ... */ },
  (error) => { /* ... */ },
  { webSearch: enableWebSearch },  // 传递联网搜索状态
)
```

### 2. 后端修改

#### 2.1 API 接口 (`api/controllers/console/chat/simple_chat.py`)

**主要修改**:

1. **添加 web_search 字段到请求模型**:
```python
class SimpleChatPayload(BaseModel):
    query: str = Field(..., description="User query/message")
    provider: str | None = Field(default=None, description="Model provider")
    model: str | None = Field(default=None, description="Model name")
    history: list[dict] | None = Field(default=None, description="Conversation history")
    web_search: bool = Field(default=False, description="Enable web search")  # 新增
```

2. **实现网络搜索方法**:
```python
def _perform_web_search(self, query: str) -> str:
    """
    Perform web search using DuckDuckGo.
    Returns formatted search results as a string.
    """
    try:
        import requests
        from urllib.parse import quote
        
        # Use DuckDuckGo Instant Answer API
        encoded_query = quote(query)
        url = f"https://api.duckduckgo.com/?q={encoded_query}&format=json&no_html=1&skip_disambig=1"
        
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()
        
        # 处理搜索结果...
        return formatted_results
    except Exception as e:
        logger.error(f"Web search error: {e}")
        return "网络搜索暂时不可用。"
```

3. **集成搜索结果到 AI 提示**:
```python
# Perform web search if enabled
search_results = ""
if args.web_search:
    try:
        search_results = self._perform_web_search(args.query)
    except Exception as e:
        logger.warning(f"Web search failed: {e}")

# Build messages with search results
system_content = "You are a helpful AI assistant."
if search_results:
    system_content += f"\n\n以下是从互联网搜索到的相关信息，请参考这些信息回答用户的问题：\n\n{search_results}"

messages = [SystemPromptMessage(content=system_content)]
```

## 工作流程

```
用户输入问题 + 勾选"联网搜索"
    ↓
前端发送请求（包含 web_search: true）
    ↓
后端接收请求
    ↓
调用 DuckDuckGo API 进行搜索
    ↓
获取搜索结果（摘要、相关信息、链接）
    ↓
将搜索结果添加到系统提示中
    ↓
调用 LLM 生成回答（基于搜索结果）
    ↓
流式返回回答给前端
    ↓
前端显示 AI 回答
```

## 搜索引擎选择

**当前使用**: DuckDuckGo Instant Answer API

**优点**:
- ✅ 免费，无需 API Key
- ✅ 无请求限制
- ✅ 隐私友好
- ✅ 返回结构化数据
- ✅ 支持中英文

**返回内容**:
- 摘要（Abstract）
- 相关主题（Related Topics）
- 来源链接（URLs）

## 使用方法

### 用户操作

1. **进入聊天页面** (`/chat`)
2. **勾选"联网搜索"复选框**（输入框顶部）
3. **输入问题**（例如："今天的天气怎么样？"）
4. **点击"发送回复"**
5. **查看 AI 回答**（基于搜索结果）

### 示例场景

**场景 1：查询实时信息**
```
用户：今天北京的天气怎么样？
[勾选联网搜索]
AI：根据最新的天气信息，今天北京...（基于搜索结果）
```

**场景 2：查询最新技术**
```
用户：Next.js 16 有哪些新特性？
[勾选联网搜索]
AI：根据最新的文档，Next.js 16 的主要新特性包括...
```

**场景 3：事实核查**
```
用户：2024年奥运会在哪里举办？
[勾选联网搜索]
AI：根据搜索结果，2024年奥运会在巴黎举办...
```

## 技术细节

### 搜索 API 调用

**API 端点**:
```
https://api.duckduckgo.com/?q={query}&format=json&no_html=1&skip_disambig=1
```

**参数说明**:
- `q`: 搜索查询（URL 编码）
- `format=json`: 返回 JSON 格式
- `no_html=1`: 不包含 HTML 标签
- `skip_disambig=1`: 跳过消歧义页面

**超时设置**: 5 秒

**错误处理**:
- 搜索失败时返回友好提示
- 不影响正常对话流程
- 记录错误日志便于调试

### 搜索结果格式化

```python
results = []

# 主要摘要
if data.get("Abstract"):
    results.append(f"摘要：{data['Abstract']}")
    if data.get("AbstractURL"):
        results.append(f"来源：{data['AbstractURL']}")

# 相关信息（最多3条）
if data.get("RelatedTopics"):
    results.append("\n相关信息：")
    for i, topic in enumerate(data["RelatedTopics"][:3], 1):
        if isinstance(topic, dict) and topic.get("Text"):
            results.append(f"{i}. {topic['Text']}")
            if topic.get("FirstURL"):
                results.append(f"   链接：{topic['FirstURL']}")

return "\n".join(results)
```

## 性能优化

### 1. 超时控制
- 搜索请求设置 5 秒超时
- 避免长时间等待影响用户体验

### 2. 错误容错
- 搜索失败不影响正常对话
- 优雅降级，继续使用 LLM 回答

### 3. 结果限制
- 只返回前 3 条相关信息
- 避免上下文过长影响 LLM 性能

## 后续优化建议

### 1. 多搜索引擎支持

添加更多搜索引擎选项：

```python
SEARCH_ENGINES = {
    'duckduckgo': 'https://api.duckduckgo.com/',
    'google': 'https://www.googleapis.com/customsearch/v1',  # 需要 API Key
    'bing': 'https://api.bing.microsoft.com/v7.0/search',    # 需要 API Key
}
```

### 2. 搜索结果缓存

```python
from functools import lru_cache

@lru_cache(maxsize=100)
def _perform_web_search_cached(self, query: str) -> str:
    # 缓存搜索结果，避免重复请求
    pass
```

### 3. 搜索结果展示优化

在前端显示搜索来源：

```typescript
type Message = {
  // ... 现有字段
  searchSources?: Array<{
    title: string
    url: string
    snippet: string
  }>
}
```

### 4. 高级搜索选项

```typescript
const [searchOptions, setSearchOptions] = useState({
  enabled: false,
  engine: 'duckduckgo',  // 搜索引擎选择
  resultCount: 5,         // 结果数量
  timeRange: 'all',       // 时间范围
  language: 'zh-CN',      // 搜索语言
  safeSearch: true,       // 安全搜索
})
```

### 5. 搜索历史记录

```python
# 记录搜索历史
class SearchHistory(db.Model):
    id = db.Column(db.String(36), primary_key=True)
    user_id = db.Column(db.String(36))
    query = db.Column(db.Text)
    results = db.Column(db.JSON)
    created_at = db.Column(db.DateTime)
```

## 安全考虑

### 1. 输入验证
- 查询长度限制（最大 500 字符）
- 特殊字符过滤
- SQL 注入防护

### 2. 速率限制
```python
from flask_limiter import Limiter

limiter = Limiter(
    key_func=lambda: current_user.id,
    default_limits=["100 per hour"]
)

@limiter.limit("10 per minute")
def post(self):
    # 限制每分钟最多 10 次搜索
    pass
```

### 3. 内容过滤
- 过滤敏感内容
- 验证搜索结果来源
- 防止恶意注入

## 测试建议

### 功能测试
1. ✅ 测试启用/禁用联网搜索
2. ✅ 测试不同类型的查询
3. ✅ 测试搜索失败的情况
4. ✅ 测试网络超时
5. ✅ 测试特殊字符查询

### 性能测试
1. ✅ 测试搜索响应时间
2. ✅ 测试并发搜索请求
3. ✅ 测试大量查询的性能

### 集成测试
1. ✅ 测试与现有功能的兼容性
2. ✅ 测试不同模型的表现
3. ✅ 测试历史对话的影响

## 相关文件

### 前端
- `web/service/chat.ts` - 聊天服务（已修改）
- `web/app/(commonLayout)/chat/page.tsx` - 聊天页面（已修改）

### 后端
- `api/controllers/console/chat/simple_chat.py` - 简单聊天 API（已修改）

### 文档
- `CHAT_PAGE_ENHANCEMENT.md` - 聊天页面优化文档
- `WEB_SEARCH_IMPLEMENTATION.md` - 本文档

## 依赖项

### Python 依赖
- `requests` - HTTP 请求库（已包含在项目中）

### 可选依赖
- `beautifulsoup4` - HTML 解析（用于更复杂的搜索）
- `selenium` - 浏览器自动化（用于 JavaScript 渲染的页面）

## 故障排除

### 问题 1：搜索无结果
**原因**: DuckDuckGo API 可能没有相关结果
**解决**: 优化查询关键词，或尝试其他搜索引擎

### 问题 2：搜索超时
**原因**: 网络连接问题或 API 响应慢
**解决**: 增加超时时间或使用备用搜索引擎

### 问题 3：搜索结果不准确
**原因**: 查询关键词不够精确
**解决**: 优化查询提取逻辑，提取关键词

## 总结

成功实现了完整的联网搜索功能：

1. ✅ **前端开关** - 用户可以轻松启用/禁用
2. ✅ **后端搜索** - 使用 DuckDuckGo API 获取实时信息
3. ✅ **结果集成** - 将搜索结果融入 AI 回答
4. ✅ **错误处理** - 优雅降级，不影响正常使用
5. ✅ **性能优化** - 超时控制，结果限制

用户现在可以通过勾选"联网搜索"复选框来获取基于最新网络信息的 AI 回答！
