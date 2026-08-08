from fastapi import APIRouter, HTTPException
from app.models.schemas import (
    MemoryStatsResponse,
    ToolRegistryResponse,
    RedisInfoResponse,
)
from app.agents.persistent_memory import persistent_memory
from app.tools.registry import tool_registry
from app.services.redis_service import redis_service
from config.settings import settings
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["Monitoring"])


# ============================
# MEMORY ENDPOINTS
# ============================

@router.get(
    "/memory/stats",
    response_model=MemoryStatsResponse,
    summary="Memory statistics",
    description="Get persistent memory statistics",
)
async def get_memory_stats():
    """Get memory backend stats"""
    stats = persistent_memory.get_stats()
    return MemoryStatsResponse(**stats)


@router.get(
    "/memory/sessions",
    summary="List all sessions",
    description="List all conversation sessions with metadata",
)
async def list_all_sessions(user_id: str = None):
    """List sessions from persistent memory"""
    sessions = persistent_memory.list_sessions(user_id=user_id)
    return {
        "sessions": sessions,
        "total": len(sessions),
        "backend": settings.MEMORY_BACKEND,
    }


@router.get(
    "/memory/session/{session_id}",
    summary="Get session history",
    description="Get conversation history for a session from persistent memory",
)
async def get_session_history(
    session_id: str,
    user_id: str = None,
    limit: int = None,
):
    """Get session history from persistent memory"""
    messages = persistent_memory.get_history(
        session_id=session_id,
        user_id=user_id,
        limit=limit,
    )

    if not messages:
        raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found")

    formatted = []
    for msg in messages:
        role = "human" if hasattr(msg, 'type') and msg.type == "human" else "ai"
        formatted.append({"role": role, "content": msg.content})

    meta = persistent_memory.get_session_meta(session_id, user_id)

    return {
        "session_id": session_id,
        "message_count": len(formatted),
        "history": formatted,
        "metadata": meta,
        "backend": settings.MEMORY_BACKEND,
    }


@router.delete(
    "/memory/session/{session_id}",
    summary="Clear session",
    description="Clear a session's persistent memory",
)
async def clear_session(session_id: str, user_id: str = None):
    """Clear session from persistent memory"""
    success = persistent_memory.clear_session(session_id, user_id)
    return {
        "status": "cleared" if success else "failed",
        "session_id": session_id,
        "backend": settings.MEMORY_BACKEND,
    }


# ============================
# TOOL REGISTRY ENDPOINTS
# ============================

@router.get(
    "/tools",
    response_model=ToolRegistryResponse,
    summary="Tool registry",
    description="Get all registered tools and their metadata",
)
async def get_tool_registry():
    """Get tool registry info"""
    stats = tool_registry.get_stats()
    tools_info = [dict(info) for info in tool_registry.get_all_tool_info()]

    return ToolRegistryResponse(
        total_tools=stats["total_tools"],
        total_agents=stats["total_agents"],
        tools_per_agent=stats["tools_per_agent"],
        categories=stats["categories"],
        tools=tools_info,
    )


@router.get(
    "/tools/agent/{agent_name}",
    summary="Agent tools",
    description="Get all tools for a specific agent",
)
async def get_agent_tools(agent_name: str):
    """Get tools for a specific agent"""
    tools_info = tool_registry.get_agent_tool_info(agent_name)
    if not tools_info:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_name}' not found")
    return {"agent": agent_name, "tools": [dict(info) for info in tools_info]}


@router.get(
    "/tools/search",
    summary="Search tools",
    description="Search tools by name, description, or category",
)
async def search_tools(query: str):
    """Search tools"""
    results = tool_registry.search_tools(query)
    return {"query": query, "results": [dict(info) for info in results], "total": len(results)}


# ============================
# REDIS ENDPOINTS
# ============================

@router.get(
    "/redis/info",
    response_model=RedisInfoResponse,
    summary="Redis info",
    description="Get Redis server information",
)
async def get_redis_info():
    """Get Redis server info"""
    info = redis_service.get_info()
    return RedisInfoResponse(**info)


@router.get(
    "/redis/health",
    summary="Redis health check",
    description="Check if Redis is connected and responsive",
)
async def redis_health():
    """Redis health check"""
    is_connected = redis_service.is_connected
    return {
        "status": "healthy" if is_connected else "disconnected",
        "host": settings.REDIS_HOST,
        "port": settings.REDIS_PORT,
        "db": settings.REDIS_DB,
    }