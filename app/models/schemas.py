from email.policy import default

from pydantic import BaseModel, Field
from typing import Any, List, Optional, Dict
from enum import Enum


# ============================
# STAGE 1 SCHEMAS (Keep existing)
# ============================

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=5000, description="User message")
    session_id: Optional[str] = Field(default=None)
    stream: bool = Field(default=False)
    class Config:
        json_schema_extra = {"example": {"message": "Explain multi-agent systems", "stream": False}}

class ChatResponse(BaseModel):
    reply: str = Field(..., description="AI assistant reply")
    model: str = Field(..., description="LLM model used")
    session_id: Optional[str] = Field(default=None)
    tokens_used: Optional[int] = Field(default=None)

class HealthResponse(BaseModel):
    status: str
    api_keys: Dict[str, bool]
    model: str
    version: str

class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None


# ============================
# STAGE 2 SCHEMAS (NEW)
# ============================

class IngestRequest(BaseModel):
    """Request to trigger document ingestion"""
    file_paths: Optional[List[str]] = Field(
        default=None,
        description="Specific files to ingest. If None, ingests all from data/docs/"
    )
    chunk_size: int = Field(
        default=1000,
        description="Size of each text chunk in characters"
    )
    chunk_overlap: int = Field(
        default=200,
        description="Overlap between chunks in characters"
    )
    class Config:
        json_schema_extra = {
            "example": {
                "chunk_size": 1000,
                "chunk_overlap": 200
            }
        }

class IngestResponse(BaseModel):
    """Response after document ingestion"""
    status: str = Field(..., description="Ingestion status")
    documents_loaded: int = Field(..., description="Number of documents loaded")
    chunks_created: int = Field(..., description="Number of chunks created")
    files_processed: List[str] = Field(..., description="List of processed files")

class RAGQueryRequest(BaseModel):
    """Request for RAG-powered Q&A"""
    question: str = Field(
        ...,
        min_length=1,
        max_length=5000,
        description="Question to ask over your documents"
    )
    k: int = Field(
        default=4,
        description="Number of relevant chunks to retrieve"
    )
    session_id: Optional[str] = Field(default=None)
    class Config:
        json_schema_extra = {
            "example": {
                "question": "What are the main features discussed in the document?",
                "k": 4
            }
        }

class RAGQueryResponse(BaseModel):
    """Response from RAG Q&A"""
    answer: str = Field(..., description="AI answer based on retrieved context")
    sources: List[str] = Field(..., description="Source document chunks used")
    model: str = Field(..., description="LLM model used")
    chunks_retrieved: int = Field(..., description="Number of chunks retrieved")

    # ============================
# STAGE 3 SCHEMAS (NEW)
# ============================

class AgentRequest(BaseModel):
    """Request for agent execution"""
    query: str = Field(
        ...,
        min_length=1,
        max_length=5000,
        description="User query for the code agent"
    )
    session_id: Optional[str] = Field(
        default=None,
        description="Session ID for conversation memory (auto-generated if None)"
    )
    class Config:
        json_schema_extra = {
            "example": {
                "query": "Generate a Python function to fetch data from an API",
                "session_id": "my-session-001"
            }
        }

class AgentResponse(BaseModel):
    """Response from agent execution"""
    response: str = Field(..., description="Agent's response")
    tool_used: str = Field(..., description="Tool that was selected and executed")
    agent_type: str = Field(..., description="Agent type that handled the query")
    session_id: str = Field(..., description="Session ID for memory tracking")
    rag_sources: List[str] = Field(default_factory=list, description="RAG source citations")
    has_rag_context: bool = Field(..., description="Whether RAG context was used")
    iterations: int = Field(..., description="Number of graph iterations")

class SessionInfoResponse(BaseModel):
    """Response for session info"""
    session_id: str
    message_count: int
    history: List[Dict[str, str]]

    # ============================
# STAGE 4 SCHEMAS (NEW)
# ============================

class MultiAgentRequest(BaseModel):
    """Request for multi-agent execution"""
    query: str = Field(
        ...,
        min_length=1,
        max_length=5000,
        description="User query — supervisor will route to the right agent"
    )
    session_id: Optional[str] = Field(
        default=None,
        description="Session ID for conversation memory"
    )
    class Config:
        json_schema_extra = {
            "example": {
                "query": "Search GitHub for popular FastAPI repositories",
                "session_id": "my-session-001"
            }
        }

class MultiAgentResponse(BaseModel):
    """Response from multi-agent execution"""
    response: str = Field(..., description="Agent's response")
    agent_used: str = Field(..., description="Agent that handled the request")
    tool_used: str = Field(..., description="Tool that was executed")
    supervisor_reasoning: str = Field(..., description="Why supervisor chose this agent")
    session_id: str = Field(..., description="Session ID")
    rag_sources: List[str] = Field(default_factory=list)
    has_rag_context: bool = Field(..., description="Whether RAG context was used")
    iterations: int = Field(..., description="Graph iterations")

class FileUploadResponse(BaseModel):
    """Response after file upload"""
    filename: str
    file_size: int
    content_length: int
    detected_type: str
    message: str

    # ============================
# STAGE 5 SCHEMAS (NEW)
# ============================

class MemoryStatsResponse(BaseModel):
    """Response for memory statistics"""
    backend: str
    redis_connected: bool
    total_sessions: int
    total_user_mappings: int
    max_conversation_turns: int
    ttl_seconds: int

class ToolRegistryResponse(BaseModel):
    """Response for tool registry info"""
    total_tools: int
    total_agents: int
    tools_per_agent: Dict[str, int]
    categories: Dict[str, int]
    tools: List[Dict[str, Any]]

class RedisInfoResponse(BaseModel):
    """Response for Redis info"""
    status: str
    version: Optional[str] = None
    used_memory_human: Optional[str] = None
    connected_clients: Optional[int] = None
    total_keys: Optional[int] = None
    uptime_in_seconds: Optional[int] = None

class MultiAgentRequest(BaseModel):
    """Request for multi-agent execution"""
    query: str = Field(..., min_length=1, max_length=5000)
    session_id: Optional[str] = Field(default=None)
    user_id: Optional[str] = Field(default=None, description="User ID for memory isolation")