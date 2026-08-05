from pydantic import BaseModel, Field
from typing import Optional, List
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
    api_keys: dict
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