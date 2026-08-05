from fastapi import APIRouter, HTTPException
from app.models.schemas import (
    AgentRequest,
    AgentResponse,
    SessionInfoResponse,
    ErrorResponse,
)
from app.services.agent_service import agent_service
from app.agents.memory import conversation_memory
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["Agent"])


# ============================
# CODE AGENT ENDPOINT
# ============================

@router.post(
    "/agent/code",
    response_model=AgentResponse,
    responses={
        200: {"model": AgentResponse},
        500: {"model": ErrorResponse},
    },
    summary="Run Code Agent",
    description="Execute the Code Agent with LangGraph: route → tool → generate response",
)
async def run_code_agent(request: AgentRequest):
    """
    Code Agent powered by LangGraph.

    Tools available:
    - code_generate: Generate code in any language
    - code_debug: Debug and fix buggy code
    - code_explain: Explain what code does
    - code_execute: Safely run Python snippets

    Automatically uses RAG context if documents are ingested.
    Maintains conversation memory per session.
    """
    try:
        result = agent_service.run_code_agent(
            query=request.query,
            session_id=request.session_id,
        )

        return AgentResponse(**result)

    except Exception as e:
        logger.error(f"❌ Code agent endpoint error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================
# SESSION MANAGEMENT
# ============================

@router.get(
    "/agent/sessions",
    summary="List active sessions",
    description="Get all active conversation sessions",
)
async def list_sessions():
    """List all active conversation sessions"""
    sessions = conversation_memory.list_sessions()
    return {
        "sessions": sessions,
        "total": len(sessions),
    }


@router.get(
    "/agent/session/{session_id}",
    response_model=SessionInfoResponse,
    summary="Get session info",
    description="Get conversation history for a specific session",
)
async def get_session(session_id: str):
    """Get session details and conversation history"""
    history = conversation_memory.get_history(session_id)

    if not history:
        raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found")

    formatted_history = []
    for msg in history:
        role = "human" if hasattr(msg, 'type') and msg.type == "human" else "ai"
        formatted_history.append({
            "role": role,
            "content": msg.content,
        })

    return SessionInfoResponse(
        session_id=session_id,
        message_count=len(history),
        history=formatted_history,
    )


@router.delete(
    "/agent/session/{session_id}",
    summary="Clear session",
    description="Delete a conversation session's memory",
)
async def clear_session(session_id: str):
    """Clear a session's conversation memory"""
    conversation_memory.clear_session(session_id)
    return {
        "status": "cleared",
        "session_id": session_id,
    }