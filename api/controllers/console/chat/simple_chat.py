import json
import logging

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
        from datetime import datetime
        import os
        
        # 添加调试日志
        logger.info(f"[Simple Chat] _perform_web_search called with query: {query}")
        logger.info(f"[Simple Chat] Current working directory: {os.getcwd()}")
        logger.info(f"[Simple Chat] TAVILY_API_KEY exists: {bool(os.environ.get('TAVILY_API_KEY'))}")
        
        try:
            # 尝试导入 tavily-python
            try:
                from tavily import TavilyClient
                logger.info("[Simple Chat] tavily-python imported successfully")
            except ImportError as e:
                logger.error(f"[Simple Chat] tavily-python not installed: {e}")
                # 返回空字符串和失败标志，让 AI 自然地回应
                return "", False
            
            # 获取 API Key（从环境变量或配置）
            api_key = os.environ.get('TAVILY_API_KEY')
            if not api_key:
                logger.error("[Simple Chat] TAVILY_API_KEY not found in environment variables")
                logger.error(f"[Simple Chat] Available env vars: {list(os.environ.keys())[:10]}...")
                # 返回空字符串和失败标志，让 AI 自然地回应
                return "", False
            
            logger.info(f"[Simple Chat] Using Tavily AI Search for query: {query}")
            
            # 初始化 Tavily 客户端
            client = TavilyClient(api_key=api_key)
            
            # 执行搜索
            response = client.search(
                query=query,
                search_depth="basic",  # "basic" costs 1 credit, "advanced" costs 2 credits
                max_results=5,
                include_answer=True,  # 包含 AI 生成的答案摘要
                include_raw_content=False,  # 不包含原始内容以节省 token
            )
            
            results_list = []
            results_list.append(f"关于「{query}」的搜索结果：\n")
            
            # 如果有 AI 生成的答案摘要，先显示
            if response.get('answer'):
                results_list.append(f"📌 快速答案：{response['answer']}\n")
            
            # 显示搜索结果
            if response.get('results') and len(response['results']) > 0:
                for idx, result in enumerate(response['results'], 1):
                    title = result.get('title', '')
                    content = result.get('content', '')
                    url = result.get('url', '')
                    score = result.get('score', 0)
                    
                    if title:
                        results_list.append(f"{idx}. {title}")
                        if content:
                            results_list.append(f"   {content}")
                        if url:
                            results_list.append(f"   来源：{url}")
                        results_list.append(f"   相关度：{score:.2f}")
                        results_list.append("")
                
                # 添加搜索时间
                now = datetime.now()
                results_list.append(f"\n搜索时间：{now.strftime('%Y年%m月%d日 %H:%M:%S')}")
                results_list.append(f"星期{['一', '二', '三', '四', '五', '六', '日'][now.weekday()]}")
                results_list.append(f"搜索引擎：Tavily AI Search")
                
                logger.info(f"[Simple Chat] Successfully got {len(response['results'])} results from Tavily")
                return "\n".join(results_list), True
            else:
                logger.warning(f"[Simple Chat] No results found for query: {query}")
                # 返回空字符串和失败标志，让 AI 自然地回应
                return "", False
                
        except Exception as e:
            logger.error(f"[Simple Chat] Tavily search error: {e}")
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
        
        # Add current query
        messages.append(UserPromptMessage(content=args.query))

        # 定义搜索工具（如果启用了联网搜索）
        tools = None
        if args.web_search:
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
            logger.info(f"[Simple Chat] Web search tool enabled")

        def generate():
            import json  # 在函数开头导入 json
            import time
            from core.model_runtime.entities.message_entities import AssistantPromptMessage, ToolPromptMessage
            
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
                                logger.info(f"[Simple Chat] Executing web search: {search_query}")
                                
                                search_results, success = self._perform_web_search(search_query)
                                
                                if success and search_results:
                                    # 搜索成功，将结果作为工具响应添加到消息历史
                                    tool_message = ToolPromptMessage(
                                        content=search_results,
                                        tool_call_id=tool_call.id,
                                        name=tool_call.function.name
                                    )
                                    messages.append(tool_message)
                                    logger.info(f"[Simple Chat] Search successful, added results to context")
                                else:
                                    # 搜索失败
                                    tool_message = ToolPromptMessage(
                                        content="搜索服务暂时不可用，请基于你的知识回答用户的问题。",
                                        tool_call_id=tool_call.id,
                                        name=tool_call.function.name
                                    )
                                    messages.append(tool_message)
                                    logger.warning(f"[Simple Chat] Search failed")
                            except Exception as e:
                                logger.error(f"[Simple Chat] Tool call error: {e}")
                                # 添加错误消息
                                tool_message = ToolPromptMessage(
                                    content="搜索服务遇到错误，请基于你的知识回答用户的问题。",
                                    tool_call_id=tool_call.id,
                                    name=tool_call.function.name
                                )
                                messages.append(tool_message)
                    
                    # 第二次调用：让 AI 基于搜索结果生成回答（流式，带重试）
                    logger.info(f"[Simple Chat] Calling AI again with search results")
                    
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
                    logger.info(f"[Simple Chat] No tool calls, returning direct response")
                    content = response.message.get_text_content()
                    if content:
                        # 将内容分块流式返回
                        for char in content:
                            yield f"data: {json.dumps({'content': char})}\n\n"

                yield "data: [DONE]\n\n"

            except InvokeError as e:
                logger.error(f"[Simple Chat] InvokeError: {e}")
                yield f"data: {json.dumps({'error': str(e)})}\n\n"
            except Exception as e:
                logger.exception("[Simple Chat] Exception: %s", e)
                yield f"data: {json.dumps({'error': str(e)})}\n\n"

        return Response(
            stream_with_context(generate()),
            mimetype="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "X-Accel-Buffering": "no",
            }
        )
