import json
import logging
import os
import re
import subprocess
import urllib.request
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)

SEARCH_SNIPPET_MAX_CHARS = 220
ZHIPUAI_PROVIDER_ID = "bdim/zhipuai_web_search/zhipuai"
ZHIPUAI_TOOL_NAME = "zhipuai_web_search"


class WebSearchService:
    @classmethod
    def perform_web_search(cls, query: str, tenant_id: str | None = None, user_id: str | None = None) -> tuple[str, bool]:
        logger.info("[Web Search] search requested, query=%s", query)

        if tenant_id and user_id:
            zhipu_results, zhipu_success = cls._perform_zhipuai_plugin_search(query, tenant_id, user_id)
            if zhipu_success and zhipu_results:
                return zhipu_results, True
            logger.warning("[Web Search] ZhipuAI search unavailable or empty, falling back to Tavily")
        else:
            logger.warning("[Web Search] Missing tenant/user context, skipping ZhipuAI plugin search")

        return cls._perform_tavily_search(query)

    @classmethod
    def build_augmented_query(cls, query: str, tenant_id: str | None, user_id: str | None) -> tuple[str, str, bool]:
        search_results, search_success = cls.perform_web_search(query, tenant_id=tenant_id, user_id=user_id)
        if search_success and search_results:
            return (
                (
                    f"{query}\n\n"
                    "请基于下面的联网搜索结果回答。优先引用搜索结果中的最新信息；"
                    "如果结果与问题相关性不足，请明确说明。\n\n"
                    f"{search_results}"
                ),
                search_results,
                True,
            )

        return (
            (
                f"{query}\n\n"
                "联网搜索已开启，但搜索服务本次没有返回可用结果。"
                "请说明这一点，并基于已有知识给出有限回答。"
            ),
            "",
            False,
        )

    @classmethod
    def _perform_zhipuai_plugin_search(cls, query: str, tenant_id: str, user_id: str) -> tuple[str, bool]:
        try:
            from core.plugin.backwards_invocation.tool import PluginToolBackwardsInvocation
            from core.tools.entities.tool_entities import ToolInvokeMessage, ToolProviderType

            messages = PluginToolBackwardsInvocation.invoke_tool(
                tenant_id=tenant_id,
                user_id=user_id,
                tool_type=ToolProviderType.BUILT_IN,
                provider=ZHIPUAI_PROVIDER_ID,
                tool_name=ZHIPUAI_TOOL_NAME,
                tool_parameters={
                    "search_query": query,
                    "search_engine": "search_pro",
                    "count": 5,
                    "search_recency_filter": "noLimit",
                    "content_size": "medium",
                },
            )

            json_payload: dict[str, Any] | None = None
            text_messages: list[str] = []
            for message in messages:
                if message.type == ToolInvokeMessage.MessageType.JSON:
                    payload = getattr(message.message, "json_object", None)
                    if isinstance(payload, dict):
                        json_payload = payload
                elif message.type == ToolInvokeMessage.MessageType.TEXT:
                    text = getattr(message.message, "text", "")
                    if text:
                        text_messages.append(text)

            if json_payload:
                formatted, success = cls._format_zhipuai_response(query, json_payload)
                if success:
                    return formatted, True

            joined_text = "\n".join(text_messages).strip()
            if joined_text:
                logger.warning("[Web Search] ZhipuAI plugin returned text without usable JSON: %s", joined_text[:200])
            return "", False
        except Exception as e:
            logger.warning("[Web Search] ZhipuAI plugin search failed: %s", e, exc_info=True)
            return "", False

    @classmethod
    def _format_zhipuai_response(cls, query: str, response: dict[str, Any]) -> tuple[str, bool]:
        results = response.get("results")
        if not isinstance(results, list) or not results:
            return "", False

        lines = [f"## 关于「{query}」的联网搜索结果", "\n**来源**"]
        usable_count = 0

        for idx, result in enumerate(results, 1):
            if not isinstance(result, dict):
                continue

            title = cls._clean_search_text(str(result.get("title") or ""))
            content = cls._clean_search_text(str(result.get("content") or ""))
            url = str(result.get("link") or result.get("url") or "")

            if not title and not content:
                continue

            usable_count += 1
            title_text = f"[{title}]({url})" if title and url else title or url or f"结果 {idx}"
            lines.append(f"\n{usable_count}. **{title_text}**")
            if content:
                lines.append(f"   {content}")

        if usable_count == 0:
            return "", False

        lines.append(cls._format_footer("智谱AI网页搜索"))
        logger.info("[Web Search] Successfully got %s results from ZhipuAI", usable_count)
        return "\n".join(lines), True

    @classmethod
    def _perform_tavily_search(cls, query: str) -> tuple[str, bool]:
        def _format_tavily_response(response: dict[str, Any]) -> tuple[str, bool]:
            def _format_score(score: object) -> str:
                try:
                    return f"{float(score):.2f}"
                except Exception:
                    return ""

            results_list = [f"## 关于「{query}」的联网搜索结果"]

            if response.get("answer"):
                results_list.append(f"\n**快速摘要**：{cls._clean_search_text(str(response['answer']))}")

            results = response.get("results")
            if isinstance(results, list) and results:
                results_list.append("\n**来源**")
                usable_count = 0
                for result in results:
                    if not isinstance(result, dict):
                        continue

                    title = cls._clean_search_text(str(result.get("title") or ""))
                    content = cls._clean_search_text(str(result.get("content") or ""))
                    url = str(result.get("url") or "")
                    score = _format_score(result.get("score", ""))

                    if title:
                        usable_count += 1
                        title_text = f"[{title}]({url})" if url else title
                        results_list.append(f"\n{usable_count}. **{title_text}**")
                        if content:
                            results_list.append(f"   {content}")
                        if score:
                            results_list.append(f"   相关度：{score}")

                if usable_count:
                    results_list.append(cls._format_footer("Tavily AI Search"))
                    logger.info("[Web Search] Successfully got %s results from Tavily", usable_count)
                    return "\n".join(results_list), True

            logger.warning("[Web Search] No Tavily results found for query: %s", query)
            return "", False

        def _search_with_rest_api(api_key: str) -> dict[str, Any]:
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
                logger.warning("[Web Search] Tavily curl request failed, falling back to urllib: %s", e)

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
            api_key = os.environ.get("TAVILY_API_KEY")
            if not api_key:
                logger.error("[Web Search] TAVILY_API_KEY not found in environment variables")
                return "", False

            logger.info("[Web Search] Using Tavily AI Search for query: %s", query)

            try:
                from tavily import TavilyClient

                client = TavilyClient(api_key=api_key)
                response = client.search(
                    query=query,
                    search_depth="basic",
                    max_results=5,
                    include_answer=True,
                    include_raw_content=False,
                )
            except ImportError as e:
                logger.warning("[Web Search] tavily-python not installed, using REST API fallback: %s", e)
                response = _search_with_rest_api(api_key)

            return _format_tavily_response(response)
        except Exception as e:
            logger.error("[Web Search] Tavily search error: %s", e, exc_info=True)
            return "", False

    @staticmethod
    def _clean_search_text(value: str) -> str:
        cleaned = re.sub(r"!\[[^\]]*]\([^)]+\)", "", value)
        cleaned = re.sub(r"\[[^\]]*]\([^)]+\)", "", cleaned)
        cleaned = re.sub(r"#{1,6}\s*", " ", cleaned)
        cleaned = re.sub(r"\* Use Alt \+ Down Arrow to expand\.", " ", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"Image\s+\d+", " ", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"(?:\.\s*){4,}", " ", cleaned)
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        if not re.search(r"[\w\u4e00-\u9fff]", cleaned):
            return ""
        if len(cleaned) > SEARCH_SNIPPET_MAX_CHARS:
            return f"{cleaned[:SEARCH_SNIPPET_MAX_CHARS].rstrip()}..."
        return cleaned

    @staticmethod
    def _format_footer(engine: str) -> str:
        now = datetime.now()
        return (
            f"\n_搜索时间：{now.strftime('%Y年%m月%d日 %H:%M:%S')}，"
            f"星期{['一', '二', '三', '四', '五', '六', '日'][now.weekday()]}，"
            f"搜索引擎：{engine}_"
        )
