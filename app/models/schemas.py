from pydantic import BaseModel, Field
from typing import Optional, List
from enum import Enum


class ChatRequest(BaseModel):
    """Request model for /chat endpoint"""
    message: str = Field(
        ...,
        min_length=1,
        max_length=5000,
        description="User message to the AI assistant"
    )
    session_id: Optional[str] = Field(
        default=None,
        description="Optional session ID for conversation tracking"
    )
    stream: bool = Field(
        default=False,
        description="Set true for SSE streaming response"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "message": "Explain what a multi-agent system is",
                "session_id": "session-123",
                "stream": False
            }
        }


class ChatResponse(BaseModel):
    """Response model for /chat endpoint"""
    reply: str = Field(..., description="AI assistant reply")
    model: str = Field(..., description="LLM model used")
    session_id: Optional[str] = Field(
        default=None,
        description="Session ID for conversation tracking"
    )
    tokens_used: Optional[int] = Field(
        default=None,
        description="Approximate tokens used"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "reply": "A multi-agent system is...",
                "model": "gemini-1.5-flash",
                "session_id": "session-123",
                "tokens_used": 150
            }
        }


class HealthResponse(BaseModel):
    """Response model for /health endpoint"""
    status: str
    api_keys: dict
    model: str
    version: str


class ErrorResponse(BaseModel):
    """Response model for errors"""
    error: str
    detail: Optional[str] = None