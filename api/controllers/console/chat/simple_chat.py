import json

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

DEFAULT_REF_TEMPLATE_SWAGGER_2_0 = "#/definitions/{model}"


class SimpleChatPayload(BaseModel):
    query: str = Field(..., description="User query/message")
    provider: str | None = Field(default=None, description="Model provider")
    model: str | None = Field(default=None, description="Model name")
    history: list[dict] | None = Field(default=None, description="Conversation history")


def reg(cls: type[BaseModel]):
    console_ns.schema_model(cls.__name__, cls.model_json_schema(ref_template=DEFAULT_REF_TEMPLATE_SWAGGER_2_0))


reg(SimpleChatPayload)


@console_ns.route("/simple-chat")
class SimpleChatApi(Resource):
    """Simple chat API using configured models."""

    @setup_required
    @login_required
    @account_initialization_required
    @require_chat_use_capability
    @console_ns.expect(console_ns.models[SimpleChatPayload.__name__])
    def post(self):
        """Send a chat message using configured model."""
        account, tenant_id = current_account_with_tenant()
        args = SimpleChatPayload.model_validate(console_ns.payload)

        provider = args.provider
        model_name = args.model

        if not provider or not model_name:
            return {"error": "Model provider and name are required"}, 400

        # Build messages
        messages = [SystemPromptMessage(content="You are a helpful AI assistant.")]
        
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

        def generate():
            try:
                model_instance = ModelManager().get_model_instance(
                    tenant_id=tenant_id,
                    provider=provider,
                    model_type=ModelType.LLM,
                    model=model_name
                )

                response = model_instance.invoke_llm(
                    prompt_messages=messages,
                    model_parameters={
                        "temperature": 0.7,
                        "max_tokens": 2000,
                    },
                    stream=True,
                    user=str(account.id),
                )

                # Stream response
                for chunk in response:
                    if chunk.delta and chunk.delta.message:
                        content = chunk.delta.message.get_text_content()
                        if content:
                            yield f"data: {json.dumps({'content': content})}\n\n"

                yield "data: [DONE]\n\n"

            except InvokeError as e:
                yield f"data: {json.dumps({'error': str(e)})}\n\n"
            except Exception as e:
                yield f"data: {json.dumps({'error': str(e)})}\n\n"

        return Response(
            stream_with_context(generate()),
            mimetype="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "X-Accel-Buffering": "no",
            }
        )
