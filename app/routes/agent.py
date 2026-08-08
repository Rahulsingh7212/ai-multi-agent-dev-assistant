from fastapi import APIRouter, HTTPException, UploadFile, File
from app.models.schemas import (
    AgentRequest,
    AgentResponse,
    MultiAgentRequest,
    MultiAgentResponse,
    SessionInfoResponse,
    FileUploadResponse,
    ErrorResponse,
)
from app.services.agent_service import agent_service
from app.agents.persistent_memory import persistent_memory
from app.utils.pdf_parser import extract_text_from_file
from typing import List, Dict
import logging
import os
import uuid

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["Agent"])

UPLOAD_DIR = "data/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


# ============================================================
# MULTI-AGENT ENDPOINT (SUPERVISOR)
# ============================================================

@router.post(
    "/agent/run",
    response_model=MultiAgentResponse,
    summary="Run Multi-Agent (Supervisor)",
    description="Supervisor analyzes query and routes to the best agent automatically",
)
async def run_multi_agent(request: MultiAgentRequest):
    """
    Main multi-agent endpoint.

    Supervisor routes to:
    - code_agent: Code generation, debugging, explanation
    - resume_agent: Resume parsing, analysis, improvement
    - pdf_agent: Document Q&A, summarization
    - github_agent: GitHub repos, issues, PRs
    - web_agent: Web search, real-time info, news
    """
    try:
        result = agent_service.run_agent(
            query=request.query,
            session_id=request.session_id,
            user_id=request.user_id,
        )

        return MultiAgentResponse(**result)

    except Exception as e:
        logger.error(f"❌ Multi-agent endpoint error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# FILE UPLOAD
# ============================================================

@router.post(
    "/agent/upload",
    response_model=FileUploadResponse,
    summary="Upload file for agent processing",
    description="Upload a PDF/TXT file for resume or document analysis",
)
async def upload_file(file: UploadFile = File(...)):
    """Upload a file for agent processing."""
    try:
        file_id = str(uuid.uuid4())[:8]
        filename = f"{file_id}_{file.filename}"
        file_path = os.path.join(UPLOAD_DIR, filename)

        content = await file.read()

        with open(file_path, "wb") as f:
            f.write(content)

        extracted_text = extract_text_from_file(file_path)

        lower_name = (file.filename or "").lower()
        lower_text = extracted_text[:500].lower()

        resume_indicators = [
            "experience",
            "education",
            "skills",
            "objective",
            "summary",
            "work history",
        ]

        is_resume = any(
            indicator in lower_text
            for indicator in resume_indicators
        )

        if is_resume:
            detected_type = "resume"
        elif lower_name.endswith(".pdf"):
            detected_type = "pdf_document"
        else:
            detected_type = "text_document"

        return FileUploadResponse(
            filename=filename,
            file_size=len(content),
            content_length=len(extracted_text),
            detected_type=detected_type,
            message=(
                f"File uploaded as {detected_type}. "
                "Use /agent/run-with-file to process it."
            ),
        )

    except Exception as e:
        logger.error(f"❌ Upload error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# RUN AGENT WITH FILE
# ============================================================

@router.post(
    "/agent/run-with-file",
    response_model=MultiAgentResponse,
    summary="Run agent with uploaded file",
    description="Process an uploaded file with the appropriate agent",
)
async def run_agent_with_file(
    query: str = "",
    filename: str = "",
    session_id: str = None,
):
    """Run agent with an uploaded file's content."""
    try:
        file_path = os.path.join(UPLOAD_DIR, filename)

        if not os.path.exists(file_path):
            raise HTTPException(
                status_code=404,
                detail=f"File not found: {filename}",
            )

        file_content = extract_text_from_file(file_path)

        if not query:
            lower_content = file_content[:500].lower()

            resume_indicators = [
                "experience",
                "education",
                "skills",
            ]

            if any(
                indicator in lower_content
                for indicator in resume_indicators
            ):
                query = "Parse and analyze this resume"
            else:
                query = "Summarize this document"

        result = agent_service.run_agent(
            query=query,
            session_id=session_id,
            uploaded_file_path=file_path,
            uploaded_file_content=file_content,
        )

        return MultiAgentResponse(**result)

    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"❌ Run with file error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# CODE AGENT - BACKWARD COMPATIBILITY
# ============================================================

@router.post(
    "/agent/code",
    response_model=AgentResponse,
    summary="Run Code Agent directly",
    description="Execute Code Agent through the multi-agent system",
)
async def run_code_agent(request: AgentRequest):
    """Direct Code Agent access."""
    try:
        result = agent_service.run_agent(
            query=request.query,
            session_id=request.session_id,
        )

        return AgentResponse(
            response=result["response"],
            tool_used=result.get("tool_used", "unknown"),
            agent_type=result.get("agent_used", "code_agent"),
            session_id=result["session_id"],
            rag_sources=result.get("rag_sources", []),
            has_rag_context=result.get(
                "has_rag_context",
                False,
            ),
            iterations=result.get("iterations", 0),
        )

    except Exception as e:
        logger.error(f"❌ Code agent endpoint error: {e}")
        raise HTTPException(
            status_code=500,
            detail=str(e),
        )


# ============================================================
# SESSION MANAGEMENT
# ============================================================

@router.get(
    "/agent/sessions",
    summary="List active sessions",
    description="Get all active Redis conversation sessions",
)
async def list_sessions():
    """
    List all sessions stored in Redis.
    """
    try:
        sessions = persistent_memory.list_sessions()

        logger.info(
            f"📋 Found {len(sessions)} Redis sessions"
        )

        return {
            "sessions": sessions,
            "total": len(sessions),
        }

    except Exception as e:
        logger.error(
            f"❌ Failed to list sessions: {e}"
        )

        raise HTTPException(
            status_code=500,
            detail=str(e),
        )


# ============================================================
# GET SINGLE SESSION
# ============================================================

@router.get(
    "/agent/session/{session_id}",
    response_model=SessionInfoResponse,
    summary="Get session info",
    description="Get conversation history from Redis",
)
async def get_session(session_id: str):
    """
    Get a single conversation session from Redis.
    """
    try:
        logger.info(
            f"🔍 Loading Redis session: {session_id}"
        )

        history = persistent_memory.get_history(
            session_id=session_id,
            user_id=None,
        )

        logger.info(
            f"📚 Redis history found: {len(history)} messages"
        )

        if not history:
            raise HTTPException(
                status_code=404,
                detail=f"Session '{session_id}' not found",
            )

        formatted_history = []

        for msg in history:
            if hasattr(msg, "type") and msg.type == "human":
                role = "human"
            else:
                role = "ai"

            content = msg.content

            # LangChain/Gemini content can sometimes be a list
            if isinstance(content, list):
                content = "".join(
                    (
                        item.get("text", str(item))
                        if isinstance(item, dict)
                        else str(item)
                    )
                    for item in content
                )

            formatted_history.append(
                {
                    "role": role,
                    "content": content,
                }
            )

        return SessionInfoResponse(
            session_id=session_id,
            message_count=len(formatted_history),
            history=formatted_history,
        )

    except HTTPException:
        raise

    except Exception as e:
        logger.error(
            f"❌ Failed to get session '{session_id}': {e}"
        )

        raise HTTPException(
            status_code=500,
            detail=str(e),
        )


# ============================================================
# CLEAR SINGLE SESSION
# ============================================================

@router.delete(
    "/agent/session/{session_id}",
    summary="Clear session",
    description="Delete conversation history from Redis",
)
async def clear_session(session_id: str):
    """
    Clear a session from Redis.
    """
    try:
        logger.info(
            f"🗑️ Clearing Redis session: {session_id}"
        )

        cleared = persistent_memory.clear_session(
            session_id=session_id,
            user_id=None,
        )

        if not cleared:
            raise HTTPException(
                status_code=404,
                detail=f"Session '{session_id}' not found",
            )

        return {
            "status": "cleared",
            "session_id": session_id,
        }

    except HTTPException:
        raise

    except Exception as e:
        logger.error(
            f"❌ Failed to clear session: {e}"
        )

        raise HTTPException(
            status_code=500,
            detail=str(e),
        )