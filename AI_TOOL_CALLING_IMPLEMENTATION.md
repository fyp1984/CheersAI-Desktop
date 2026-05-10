# AI 工具调用实现 - 让 AI 自己决定何时搜索

## 概念说明

你提出了一个非常好的问题！之前的实现有一个问题：

### 之前的方法（预先搜索）
```
用户勾选"联网搜索" → 后端立即搜索 → 将结果添加到提示 → AI 基于结果回答
```

**问题**：
- 即使用户问题不需要实时信息，也会执行搜索
- AI 无法控制搜索过程
- 搜索结果可能不相关

### 现在的方法（AI 工具调用）
```
用户勾选"联网搜索" → 告诉 AI 有搜索工具可用 → AI 决定是否需要搜索 → AI 调用搜索工具 → 获取结果 → AI 基于结果回答
```

**优势**：
- AI 自己决定是否需要搜索
- AI 可以根据问题构造更好的搜索查询
- 更智能、更灵活

## 技术实现

### 1. 定义搜索工具

```python
tools = [
    PromptMessageTool(
        name="web_search",
        description="Search the internet for current information, news, and real-time data.",
        parameters={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query to look up on the internet"
                }
            },
            "required": ["query"]
        }
    )
]
```

### 2. 将工具传递给 AI 模型

```python
response = model_instance.invoke_llm(
    prompt_messages=messages,
    model_parameters={"temperature": 0.7, "max_tokens": 2000},
    tools=tools,  # 告诉 AI 可以使用这些工具
    stream=True,
    user=str(account.id),
)
```

### 3. 处理 AI 的工具调用请求

```python
for chunk in response:
    if chunk.delta and chunk.delta.message:
        # 检查 AI 是否请求调用工具
        if hasattr(chunk.delta.message, 'tool_calls') and chunk.delta.message.tool_calls:
            for tool_call in chunk.delta.message.tool_calls:
                if tool_call.function.name == "web_search":
                    # AI 请求搜索，执行搜索
                    args_dict = json.loads(tool_call.function.arguments)
                    search_query = args_dict.get("query", "")
                    search_results = self._perform_web_search(search_query)
                    
                    # 将搜索结果返回给 AI
                    yield f"data: {json.dumps({'content': f'[搜索结果]\n{search_results}\n\n'})}\n\n"
```

## 工作流程示例

### 场景 1：需要实时信息

**用户**："今天娱乐圈有什么新闻？"

**AI 思考**：这个问题需要实时信息，我应该使用 web_search 工具

**AI 调用工具**：
```json
{
  "name": "web_search",
  "arguments": {
    "query": "今天娱乐圈新闻 2026年5月9日"
  }
}
```

**系统执行搜索** → 返回结果给 AI

**AI 回答**：基于搜索结果生成答案

### 场景 2：不需要实时信息

**用户**："什么是人工智能？"

**AI 思考**：这是一个概念性问题，我的训练数据足够回答，不需要搜索

**AI 直接回答**：不调用工具，直接基于知识回答

## 当前状态

### ✅ 已实现
1. 工具定义（web_search）
2. 工具传递给 AI 模型
3. 工具调用检测
4. 搜索执行
5. 结果返回给 AI

### ⚠️ 注意事项

**模型支持**：不是所有模型都支持工具调用（Function Calling）

支持的模型：
- ✅ OpenAI GPT-3.5/GPT-4
- ✅ Claude 3 系列
- ✅ Gemini Pro
- ❌ 部分开源模型可能不支持

**Moonshot（你当前使用的模型）**：
- 需要检查是否支持 Function Calling
- 如果不支持，工具调用功能将不会生效
- AI 会忽略工具定义，按普通方式回答

## 测试步骤

1. **刷新浏览器**（Ctrl+Shift+R）

2. **勾选"联网搜索"**

3. **输入需要实时信息的问题**：
   - "今天有什么新闻？"
   - "2026年5月9日发生了什么？"

4. **观察后端日志**：
   ```
   [Simple Chat] Web search tool enabled
   [Simple Chat] AI requested web search: [查询内容]
   ```

5. **查看 AI 回答**：
   - 如果模型支持工具调用：AI 会先调用搜索，然后基于结果回答
   - 如果模型不支持：AI 会说无法获取实时信息

## 如果 Moonshot 不支持工具调用

如果测试后发现 Moonshot 不支持 Function Calling，我们有两个选择：

### 选项 1：保留预先搜索方式
- 回退到之前的实现
- 用户勾选"联网搜索"时，后端预先搜索
- 但要改进：明确告诉 AI 不要编造信息

### 选项 2：使用支持工具调用的模型
- 切换到 OpenAI GPT-4
- 或使用 Claude 3
- 这样可以享受 AI 自主决定何时搜索的优势

## 下一步

请测试新实现，然后告诉我：
1. 后端日志中是否出现 `[Simple Chat] AI requested web search`
2. AI 是否真正调用了搜索工具
3. 如果没有，我们可以检查 Moonshot 是否支持工具调用

如果 Moonshot 不支持，我可以立即改回预先搜索的方式，但会加上防止 AI 编造信息的保护措施。
