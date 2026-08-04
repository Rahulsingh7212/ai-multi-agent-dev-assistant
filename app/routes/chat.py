from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from sse_starlette.sse import EventSourceResponse
from app.models.schemas import ChatRequest, ChatResponse, ErrorResponse
from app.services.llm_service import llm_service
from config.settings import settings
from typing import AsyncIterator
import json
import logging
import uuid

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["Chat"])


@router.post(
    "/chat",
    response_model=ChatResponse,
    responses={
        200: {"model": ChatResponse},
        400: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    },
    summary="Chat with AI Assistant",
    description="Send a message and get AI response. Set stream=true for SSE."
)
async def chat(request: ChatRequest):
    """
    Main chat endpoint.
    - stream=false → Returns full JSON response
    - stream=true  → Returns SSE streaming response
    """

    # Generate session ID if not provided
    session_id = request.session_id or str(uuid.uuid4())

    # ============================
    # STREAMING RESPONSE (SSE)
    # ============================
    if request.stream:
        return EventSourceResponse(
            _generate_sse(request.message, session_id),
            media_type="text/event-stream",
        )

    # ============================
    # NORMAL JSON RESPONSE
    # ============================
    try:
        reply = llm_service.chat(request.message)

        if isinstance(reply, list):
            reply = " ".join(str(x) for x in reply)

        return ChatResponse(
            reply=reply,
            model=llm_service.model_name,
            session_id=session_id,
            tokens_used=len(request.message.split()) + len(reply.split()),
        )

    except Exception as e:
        logger.error(f"❌ Chat endpoint error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"LLM processing error: {str(e)}"
        )


async def _generate_sse(
    message: str,
    session_id: str
) -> AsyncIterator[dict]:
    """
    Generator function for Server-Sent Events.
    Yields chunks of AI response in real-time.
    """

    # Send start event
    yield {
        "event": "start",
        "data": json.dumps({
            "session_id": session_id,
            "model": llm_service.model_name,
        })
    }

    try:
        full_response = ""

        async for chunk in llm_service.chat_stream(message):
            if isinstance(chunk, list):
                text = ""

                for item in chunk:
                    if isinstance(item, dict):
                        if item.get("type") == "text":
                            text += item.get("text", "")
                    elif isinstance(item, str):
                        text += item

                chunk = text
            full_response += chunk

            # Send content chunk
            yield {
                "event": "chunk",
                "data": json.dumps({"content": chunk})
            }

        # Send end event with full response summary
        yield {
            "event": "end",
            "data": json.dumps({
                "session_id": session_id,
                "total_chars": len(full_response),
                "model": llm_service.model_name,
            })
        }

    except Exception as e:
        logger.error(f"❌ SSE streaming error: {e}")
        yield {
            "event": "error",
            "data": json.dumps({"error": str(e)})
        }