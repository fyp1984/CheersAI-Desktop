import json
import logging
import re

from flask import Response, stream_with_context
from flask_restx import Resource
from pydantic import BaseModel, Field

from controllers.console import console_ns
from controllers.console.workspace import require_chat_use_capability
from controllers.console.wraps import account_initialization_required, setup_required
from core.model_manager import ModelManager
from core.model_runtime.entities.message_entities import SystemPromptMessage, UserPromptMessage
from core.model_runtime.entities.model_entities import ModelType
from core.model_runtime.errors.invoke import InvokeError
from libs.login import current_account_with_tenant, login_required

logger = logging.getLogger(__name__)
DEFAULT_REF_TEMPLATE_SWAGGER_2_0 = "#/definitions/{model}"
SEARCH_SNIPPET_MAX_CHARS = 220


class SimpleChatPayload(BaseModel):
    query: str = Field(..., description="User query/message")
    provider: str | None = Field(default=None, description="Model provider")
    model: str | None = Field(default=None, description="Model name")
    history: list[dict] | None = Field(default=None, description="Conversation history")
    web_search: bool = Field(default=False, description="Enable web search")


def reg(cls: type[BaseModel]):
    console_ns.schema_model(cls.__name__, cls.model_json_schema(ref_template=DEFAULT_REF_TEMPLATE_SWAGGER_2_0))


reg(SimpleChatPayload)


@console_ns.route("/simple-chat")
class SimpleChatApi(Resource):
    """Simple chat API using configured models."""

    def _perform_web_search(self, query: str) -> tuple[str, bool]:
        """
        Perform web search using Tavily AI Search API.
        Tavily is specifically designed for AI applications with optimized results for LLM consumption.
        Returns (search_results, success) tuple.
        """
        import os
        import subprocess
        import urllib.request
        from datetime import datetime
        
        # 添加调试日志
        logger.info("[Simple Chat] _perform_web_search called with query: %s", query)
        logger.info(f"[Simple Chat] Current working directory: {os.getcwd()}")
        logger.info(f"[Simple Chat] TAVILY_API_KEY exists: {bool(os.environ.get('TAVILY_API_KEY'))}")
        
        def _format_tavily_response(response: dict) -> tuple[str, bool]:
            def _clean_search_text(value: str) -> str:
                cleaned = re.sub(r'!\[[^\]]*]\([^)]+\)', '', value)
                cleaned = re.sub(r'\[[^\]]*]\([^)]+\)', '', cleaned)
                cleaned = re.sub(r'#{1,6}\s*', ' ', cleaned)
                cleaned = re.sub(r'\* Use Alt \+ Down Arrow to expand\.', ' ', cleaned, flags=re.IGNORECASE)
                cleaned = re.sub(r'Image\s+\d+', ' ', cleaned, flags=re.IGNORECASE)
                cleaned = re.sub(r'(?:\.\s*){4,}', ' ', cleaned)
                cleaned = re.sub(r'\s+', ' ', cleaned).strip()
                if not re.search(r'[\w\u4e00-\u9fff]', cleaned):
                    return ''
                if len(cleaned) > SEARCH_SNIPPET_MAX_CHARS:
                    return f'{cleaned[:SEARCH_SNIPPET_MAX_CHARS].rstrip()}...'
                return cleaned

            def _format_score(score: object) -> str:
                try:
                    return f'{float(score):.2f}'
                except Exception:
                    return ''
            
            results_list = []
            results_list.append(f"## 关于「{query}」的联网搜索结果")
            
            # 如果有 AI 生成的答案摘要，先显示
            if response.get('answer'):
                results_list.append(f"\n**快速摘要**：{_clean_search_text(str(response['answer']))}")
            
            # 显示搜索结果
            if response.get('results') and len(response['results']) > 0:
                results_list.append("\n**来源**")
                for idx, result in enumerate(response['results'], 1):
                    title = _clean_search_text(result.get('title', ''))
                    content = _clean_search_text(result.get('content', ''))
                    url = result.get('url', '')
                    score = _format_score(result.get('score', ''))
                    
                    if title:
                        title_text = f"[{title}]({url})" if url else title
                        results_list.append(f"\n{idx}. **{title_text}**")
                        if content:
                            results_list.append(f"   {content}")
                        if score:
                            results_list.append(f"   相关度：{score}")
                
                # 添加搜索时间
                now = datetime.now()
                results_list.append(
                    f"\n_搜索时间：{now.strftime('%Y年%m月%d日 %H:%M:%S')}，"
                    f"星期{['一', '二', '三', '四', '五', '六', '日'][now.weekday()]}，"
                    "搜索引擎：Tavily AI Search_"
                )
                
                logger.info("[Simple Chat] Successfully got %s results from Tavily", len(response['results']))
                return "\n".join(results_list), True
            else:
                logger.warning("[Simple Chat] No results found for query: %s", query)
                return "", False

        def _search_with_rest_api(api_key: str) -> dict:
            payload = json.dumps({
                "api_key": api_key,
                "query": query,
                "search_depth": "basic",
                "max_results": 5,
                "include_answer": True,
                "include_raw_content": False,
            }).encode("utf-8")

            try:
                completed = subprocess.run(
                    [
                        "curl",
                        "-sS",
                        "--fail-with-body",
                        "--retry",
                        "2",
                        "--retry-delay",
                        "1",
                        "--connect-timeout",
                        "10",
                        "--max-time",
                        "35",
                        "-H",
                        "Content-Type: application/json",
                        "-H",
                        "Accept: application/json",
                        "--data-binary",
                        "@-",
                        "https://api.tavily.com/search",
                    ],
                    input=payload,
                    capture_output=True,
                    check=True,
                    timeout=45,
                )
                return json.loads(completed.stdout.decode("utf-8"))
            except Exception as e:
                logger.warning("[Simple Chat] Tavily curl request failed, falling back to urllib: %s", e)

            req = urllib.request.Request(
                "https://api.tavily.com/search",
                data=payload,
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                },
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read().decode("utf-8"))

        try:
            # 获取 API Key（从环境变量或配置）
            api_key = os.environ.get('TAVILY_API_KEY')
            if not api_key:
                logger.error("[Simple Chat] TAVILY_API_KEY not found in environment variables")
                logger.error(f"[Simple Chat] Available env vars: {list(os.environ.keys())[:10]}...")
                return "", False
            
            logger.info("[Simple Chat] Using Tavily AI Search for query: %s", query)

            try:
                from tavily import TavilyClient
                logger.info("[Simple Chat] tavily-python imported successfully")
                client = TavilyClient(api_key=api_key)
                response = client.search(
                    query=query,
                    search_depth="basic",
                    max_results=5,
                    include_answer=True,
                    include_raw_content=False,
                )
            except ImportError as e:
                logger.warning("[Simple Chat] tavily-python not installed, using REST API fallback: %s", e)
                response = _search_with_rest_api(api_key)

            return _format_tavily_response(response)
                
        except Exception as e:
            logger.error("[Simple Chat] Tavily search error: %s", e)
            # 返回空字符串和失败标志，让 AI 自然地回应
            return "", False

    @setup_required
    @login_required
    @account_initialization_required
    @require_chat_use_capability
    @console_ns.expect(console_ns.models[SimpleChatPayload.__name__])
    def post(self):
        """Send a chat message using configured model."""
        account, tenant_id = current_account_with_tenant()
        args = SimpleChatPayload.model_validate(console_ns.payload)

        # 添加调试日志
        logger.info(f"[Simple Chat] Received request - web_search: {args.web_search}, query: {args.query[:50]}...")

        provider = args.provider
        model_name = args.model

        if not provider or not model_name:
            return {"error": "Model provider and name are required"}, 400

        # Build messages
        system_content = "You are a helpful AI assistant."
        messages = [SystemPromptMessage(content=system_content)]
        
        # Add history if provided
        if args.history:
            for msg in args.history:
                if msg.get("type") == "user":
                    messages.append(UserPromptMessage(content=msg.get("content", "")))
                elif msg.get("type") == "assistant":
                    from core.model_runtime.entities.message_entities import AssistantPromptMessage
                    messages.append(AssistantPromptMessage(content=msg.get("content", "")))
        
        # Add current query. When web search is enabled, search first and pass
        # the retrieved context as normal prompt text instead of relying on a
        # second tool-call round-trip, which is not consistently supported by
        # all model providers.
        current_query = args.query
        web_search_context = ""
        if args.web_search:
            search_results, search_success = self._perform_web_search(args.query)
            if search_success and search_results:
                web_search_context = search_results
                current_query = (
                    f"{args.query}\n\n"
                    "请基于下面的联网搜索结果回答。优先引用搜索结果中的最新信息；"
                    "如果结果与问题相关性不足，请明确说明。\n\n"
                    f"{web_search_context}"
                )
                logger.info("[Simple Chat] Web search context attached to direct prompt")
            else:
                current_query = (
                    f"{args.query}\n\n"
                    "联网搜索已开启，但搜索服务本次没有返回可用结果。"
                    "请说明这一点，并基于已有知识给出有限回答。"
                )
                logger.warning("[Simple Chat] Web search enabled but no usable context returned")

        messages.append(UserPromptMessage(content=current_query))

        # 定义搜索工具（保留结构；当前联网搜索走直接上下文注入）
        tools = None
        use_direct_response = True
        if False and args.web_search:
            from core.model_runtime.entities.message_entities import PromptMessageTool
            
            tools = [
                PromptMessageTool(
                    name="web_search",
                    description="Search the internet for current information, news, and real-time data. Use this tool when you need up-to-date information that you don't have in your training data.",
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
            logger.info("[Simple Chat] Web search tool enabled")

        def generate():
            import time

            from core.model_runtime.entities.message_entities import ToolPromptMessage
            
            try:
                model_instance = ModelManager().get_model_instance(
                    tenant_id=tenant_id,
                    provider=provider,
                    model_type=ModelType.LLM,
                    model=model_name,
                    usage_metadata={
                        "source": "simple_chat",
                    },
                )

                # 第一次调用：让 AI 决定是否需要搜索（带重试）
                max_retries = 3
                retry_delay = 2  # 秒

                if use_direct_response:
                    logger.info("[Simple Chat] Streaming direct response")
                    for attempt in range(max_retries):
                        try:
                            response = model_instance.invoke_llm(
                                prompt_messages=messages,
                                model_parameters={
                                    "temperature": 0.7,
                                    "max_tokens": 2000,
                                },
                                tools=None,
                                stream=True,
                                user=str(account.id),
                            )
                            break
                        except InvokeError as e:
                            error_str = str(e).lower()
                            if ('429' in error_str or 'overloaded' in error_str or 'rate limit' in error_str) and attempt < max_retries - 1:
                                logger.warning(f"[Simple Chat] API overloaded (attempt {attempt + 1}/{max_retries}), retrying in {retry_delay}s...")
                                time.sleep(retry_delay)
                                retry_delay *= 2
                                continue
                            raise

                    emitted_content = False
                    try:
                        for chunk in response:
                            if chunk.delta and chunk.delta.message:
                                content = chunk.delta.message.get_text_content()
                                if content:
                                    emitted_content = True
                                    yield f"data: {json.dumps({'content': content})}\n\n"
                    except Exception as e:
                        error_str = str(e).lower()
                        if args.web_search and web_search_context and ('content_filter' in error_str or 'high risk' in error_str):
                            logger.warning("[Simple Chat] Model rejected web search prompt; returning Tavily context directly")
                            fallback_content = (
                                "以下为联网搜索结果摘要：\n\n"
                                f"{web_search_context}"
                            )
                            yield f"data: {json.dumps({'content': fallback_content})}\n\n"
                            yield "data: [DONE]\n\n"
                            return
                        raise

                    if not emitted_content:
                        logger.warning("[Simple Chat] Model stream completed without text content")
                        fallback_content = "模型本次没有返回正文，请稍后重试或切换模型。"
                        if args.web_search:
                            fallback_content = "联网搜索已完成，但模型本次没有返回正文，请稍后重试或切换模型。"
                        yield f"data: {json.dumps({'content': fallback_content})}\n\n"

                    yield "data: [DONE]\n\n"
                    return
                
                for attempt in range(max_retries):
                    try:
                        response = model_instance.invoke_llm(
                            prompt_messages=messages,
                            model_parameters={
                                "temperature": 0.7,
                                "max_tokens": 2000,
                            },
                            tools=tools,
                            stream=False,  # 第一次不流式，等待工具调用
                            user=str(account.id),
                        )
                        break  # 成功，跳出重试循环
                    except InvokeError as e:
                        error_str = str(e).lower()
                        # 检查是否是 429 错误或过载错误
                        if ('429' in error_str or 'overloaded' in error_str or 'rate limit' in error_str) and attempt < max_retries - 1:
                            logger.warning(f"[Simple Chat] API overloaded (attempt {attempt + 1}/{max_retries}), retrying in {retry_delay}s...")
                            time.sleep(retry_delay)
                            retry_delay *= 2  # 指数退避
                            continue
                        else:
                            # 不是 429 错误，或者已经重试了最大次数
                            raise

                # 检查是否有工具调用
                tool_calls = []
                if hasattr(response.message, 'tool_calls') and response.message.tool_calls:
                    tool_calls = response.message.tool_calls
                
                # 如果有工具调用，执行搜索并让 AI 基于结果回答
                if tool_calls:
                    logger.info(f"[Simple Chat] AI requested {len(tool_calls)} tool call(s)")
                    
                    # 将 AI 的工具调用请求添加到消息历史
                    messages.append(response.message)
                    
                    # 执行每个工具调用
                    for tool_call in tool_calls:
                        if tool_call.function.name == "web_search":
                            try:
                                args_dict = json.loads(tool_call.function.arguments)
                                search_query = args_dict.get("query", "")
                                logger.info("[Simple Chat] Executing web search: %s", search_query)
                                
                                search_results, success = self._perform_web_search(search_query)
                                
                                if success and search_results:
                                    # 搜索成功，将结果作为工具响应添加到消息历史
                                    tool_message = ToolPromptMessage(
                                        content=search_results,
                                        tool_call_id=tool_call.id,
                                        name=tool_call.function.name
                                    )
                                    messages.append(tool_message)
                                    logger.info("[Simple Chat] Search successful, added results to context")
                                else:
                                    # 搜索失败
                                    tool_message = ToolPromptMessage(
                                        content="搜索服务暂时不可用，请基于你的知识回答用户的问题。",
                                        tool_call_id=tool_call.id,
                                        name=tool_call.function.name
                                    )
                                    messages.append(tool_message)
                                    logger.warning("[Simple Chat] Search failed")
                            except Exception as e:
                                logger.error("[Simple Chat] Tool call error: %s", e)
                                # 添加错误消息
                                tool_message = ToolPromptMessage(
                                    content="搜索服务遇到错误，请基于你的知识回答用户的问题。",
                                    tool_call_id=tool_call.id,
                                    name=tool_call.function.name
                                )
                                messages.append(tool_message)
                    
                    # 第二次调用：让 AI 基于搜索结果生成回答（流式，带重试）
                    logger.info("[Simple Chat] Calling AI again with search results")
                    
                    for attempt in range(max_retries):
                        try:
                            response = model_instance.invoke_llm(
                                prompt_messages=messages,
                                model_parameters={
                                    "temperature": 0.7,
                                    "max_tokens": 2000,
                                },
                                tools=None,  # 第二次不需要工具
                                stream=True,
                                user=str(account.id),
                            )
                            break  # 成功，跳出重试循环
                        except InvokeError as e:
                            error_str = str(e).lower()
                            if ('429' in error_str or 'overloaded' in error_str or 'rate limit' in error_str) and attempt < max_retries - 1:
                                logger.warning(f"[Simple Chat] API overloaded in second call (attempt {attempt + 1}/{max_retries}), retrying in {retry_delay}s...")
                                time.sleep(retry_delay)
                                retry_delay *= 2
                                continue
                            else:
                                raise
                    
                    # 流式返回 AI 的回答
                    for chunk in response:
                        if chunk.delta and chunk.delta.message:
                            content = chunk.delta.message.get_text_content()
                            if content:
                                yield f"data: {json.dumps({'content': content})}\n\n"
                else:
                    # 没有工具调用，直接返回 AI 的回答
                    logger.info("[Simple Chat] No tool calls, returning direct response")
                    content = response.message.get_text_content()
                    if content:
                        # 将内容分块流式返回
                        for char in content:
                            yield f"data: {json.dumps({'content': char})}\n\n"

                yield "data: [DONE]\n\n"

            except InvokeError as e:
                logger.error("[Simple Chat] InvokeError: %s", e)
                yield f"data: {json.dumps({'error': str(e)})}\n\n"
            except Exception as e:
                logger.error("[Simple Chat] Exception: %s", e)
                import traceback
                traceback.print_exc()
                yield f"data: {json.dumps({'error': str(e)})}\n\n"

        return Response(
            stream_with_context(generate()),
            mimetype="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "X-Accel-Buffering": "no",
            }
        )
