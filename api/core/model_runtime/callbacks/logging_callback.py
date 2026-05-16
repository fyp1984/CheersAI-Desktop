import json
import logging
import string
from collections.abc import Sequence
from typing import Any

from core.model_runtime.callbacks.base_callback import Callback
from core.model_runtime.entities.llm_entities import LLMResult, LLMResultChunk
from core.model_runtime.entities.message_entities import PromptMessage, PromptMessageTool
from core.model_runtime.model_providers.__base.ai_model import AIModel

logger = logging.getLogger(__name__)
_PREVIEW_LIMIT = 120


def _preview_text(value: str, max_chars: int = _PREVIEW_LIMIT) -> str:
    sanitized = value.replace("\r", "\\r").replace("\n", "\\n")
    if any(char not in string.printable and char not in "\t" for char in value):
        return f"<str {len(value)} chars, non-printable omitted>"
    if len(sanitized) > max_chars:
        return f"{sanitized[:max_chars]}... ({len(value)} chars)"
    return f"{sanitized} ({len(value)} chars)"


def _summarize_content(value: Any) -> str:
    if value is None:
        return "<none>"
    if isinstance(value, str):
        return _preview_text(value)
    if isinstance(value, bytes):
        return f"<bytes {len(value)} bytes>"
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return f"<{type(value).__name__} {len(value)} items>"

    try:
        serialized = json.dumps(value, ensure_ascii=False, default=str)
    except TypeError:
        return f"<{type(value).__name__}>"

    return _preview_text(serialized)


class LoggingCallback(Callback):
    def on_before_invoke(
        self,
        llm_instance: AIModel,
        model: str,
        credentials: dict,
        prompt_messages: list[PromptMessage],
        model_parameters: dict,
        tools: list[PromptMessageTool] | None = None,
        stop: Sequence[str] | None = None,
        stream: bool = True,
        user: str | None = None,
    ):
        """
        Before invoke callback

        :param llm_instance: LLM instance
        :param model: model name
        :param credentials: model credentials
        :param prompt_messages: prompt messages
        :param model_parameters: model parameters
        :param tools: tools for tool calling
        :param stop: stop words
        :param stream: is stream response
        :param user: unique user id
        """
        self.print_text("\n[on_llm_before_invoke]\n", color="blue")
        self.print_text(f"Model: {model}\n", color="blue")
        self.print_text("Parameters:\n", color="blue")
        for key, value in model_parameters.items():
            self.print_text(f"\t{key}: {value}\n", color="blue")

        if stop:
            self.print_text(f"\tstop: {stop}\n", color="blue")

        if tools:
            self.print_text("\tTools:\n", color="blue")
            for tool in tools:
                self.print_text(f"\t\t{tool.name}\n", color="blue")

        self.print_text(f"Stream: {stream}\n", color="blue")

        if user:
            self.print_text(f"User: {user}\n", color="blue")

        self.print_text("Prompt messages:\n", color="blue")
        for index, prompt_message in enumerate(prompt_messages, start=1):
            self.print_text(f"\tmessage[{index}]\n", color="blue")
            if prompt_message.name:
                self.print_text(f"\tname: {prompt_message.name}\n", color="blue")

            self.print_text(f"\trole: {prompt_message.role.value}\n", color="blue")
            self.print_text(f"\tcontent: {_summarize_content(prompt_message.content)}\n", color="blue")

        if stream:
            self.print_text("\n[on_llm_new_chunk] output omitted in logs\n")

    def on_new_chunk(
        self,
        llm_instance: AIModel,
        chunk: LLMResultChunk,
        model: str,
        credentials: dict,
        prompt_messages: Sequence[PromptMessage],
        model_parameters: dict,
        tools: list[PromptMessageTool] | None = None,
        stop: Sequence[str] | None = None,
        stream: bool = True,
        user: str | None = None,
    ):
        """
        On new chunk callback

        :param llm_instance: LLM instance
        :param chunk: chunk
        :param model: model name
        :param credentials: model credentials
        :param prompt_messages: prompt messages
        :param model_parameters: model parameters
        :param tools: tools for tool calling
        :param stop: stop words
        :param stream: is stream response
        :param user: unique user id
        """
        return

    def on_after_invoke(
        self,
        llm_instance: AIModel,
        result: LLMResult,
        model: str,
        credentials: dict,
        prompt_messages: Sequence[PromptMessage],
        model_parameters: dict,
        tools: list[PromptMessageTool] | None = None,
        stop: Sequence[str] | None = None,
        stream: bool = True,
        user: str | None = None,
    ):
        """
        After invoke callback

        :param llm_instance: LLM instance
        :param result: result
        :param model: model name
        :param credentials: model credentials
        :param prompt_messages: prompt messages
        :param model_parameters: model parameters
        :param tools: tools for tool calling
        :param stop: stop words
        :param stream: is stream response
        :param user: unique user id
        """
        self.print_text("\n[on_llm_after_invoke]\n", color="yellow")
        self.print_text(f"Content: {_summarize_content(result.message.content)}\n", color="yellow")

        if result.message.tool_calls:
            self.print_text("Tool calls:\n", color="yellow")
            for tool_call in result.message.tool_calls:
                self.print_text(f"\t{tool_call.id}\n", color="yellow")
                self.print_text(f"\t{tool_call.function.name}\n", color="yellow")
                self.print_text(f"\t{json.dumps(tool_call.function.arguments)}\n", color="yellow")

        self.print_text(f"Model: {result.model}\n", color="yellow")
        self.print_text(f"Usage: {result.usage}\n", color="yellow")
        self.print_text(f"System Fingerprint: {result.system_fingerprint}\n", color="yellow")

    def on_invoke_error(
        self,
        llm_instance: AIModel,
        ex: Exception,
        model: str,
        credentials: dict,
        prompt_messages: list[PromptMessage],
        model_parameters: dict,
        tools: list[PromptMessageTool] | None = None,
        stop: Sequence[str] | None = None,
        stream: bool = True,
        user: str | None = None,
    ):
        """
        Invoke error callback

        :param llm_instance: LLM instance
        :param ex: exception
        :param model: model name
        :param credentials: model credentials
        :param prompt_messages: prompt messages
        :param model_parameters: model parameters
        :param tools: tools for tool calling
        :param stop: stop words
        :param stream: is stream response
        :param user: unique user id
        """
        self.print_text("\n[on_llm_invoke_error]\n", color="red")
        logger.exception("LLM invoke failed: %s", type(ex).__name__)
