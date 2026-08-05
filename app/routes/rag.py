from fastapi import APIRouter, HTTPException
from app.models.schemas import (
    IngestRequest,
    IngestResponse,
    RAGQueryRequest,
    RAGQueryResponse,
    ErrorResponse,
)
from app.services.ingestion_service import ingestion_service
from app.services.rag_service import rag_service
from app.services.vector_service import vector_service
from config.settings import settings
import logging
import uuid

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["RAG"])


# ============================
# INGEST ENDPOINT
# ============================

@router.post(
    "/ingest",
    response_model=IngestResponse,
    responses={
        200: {"model": IngestResponse},
        500: {"model": ErrorResponse},
    },
    summary="Ingest documents into vector store",
    description="Load PDFs/TXTs, chunk them, create embeddings, store in ChromaDB",
)
async def ingest_documents(request: IngestRequest = IngestRequest()):
    """
    Ingest documents from data/docs/ into ChromaDB.
    - PDFs are parsed page by page
    - Text is split into overlapping chunks
    - Embeddings are generated using HuggingFace (local, free)
    - Chunks are stored in ChromaDB for retrieval
    """
    try:
        if request.file_paths:
            # Ingest specific files
            docs_loaded, chunks_created, files_processed = (
                ingestion_service.ingest_files(
                    file_paths=request.file_paths,
                    chunk_size=request.chunk_size,
                    chunk_overlap=request.chunk_overlap,
                )
            )
        else:
            # Ingest all from default directory
            docs_loaded, chunks_created, files_processed = (
                ingestion_service.ingest_directory(
                    chunk_size=request.chunk_size,
                    chunk_overlap=request.chunk_overlap,
                )
            )

        return IngestResponse(
            status="success" if chunks_created > 0 else "no_documents_found",
            documents_loaded=docs_loaded,
            chunks_created=chunks_created,
            files_processed=files_processed,
        )

    except Exception as e:
        logger.error(f"❌ Ingestion endpoint error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================
# RAG QUERY ENDPOINT
# ============================

@router.post(
    "/rag-query",
    response_model=RAGQueryResponse,
    responses={
        200: {"model": RAGQueryResponse},
        400: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    },
    summary="Ask question over your documents",
    description="Retrieves relevant chunks from ChromaDB and generates answer with Gemini",
)
async def rag_query(request: RAGQueryRequest):
    """
    RAG-powered Q&A over ingested documents.
    1. Question is converted to embedding
    2. Similar chunks are retrieved from ChromaDB
    3. Chunks + Question are sent to Gemini
    4. Answer is returned with source citations
    """
    try:
        result = rag_service.query(
            question=request.question,
            k=request.k,
        )

        return RAGQueryResponse(
            answer=result["answer"],
            sources=result["sources"],
            model=settings.LLM_MODEL,
            chunks_retrieved=result["chunks_retrieved"],
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        logger.error(f"❌ RAG query error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================
# VECTOR STORE INFO ENDPOINT
# ============================

@router.get(
    "/vectorstore-info",
    summary="Get vector store statistics",
    description="Returns number of documents and embedding model info",
)
async def vectorstore_info():
    """Check ChromaDB status"""
    return {
        "status": "ready" if vector_service.has_vectorstore() else "empty",
        "document_count": vector_service.get_document_count(),
        "embedding_model": "all-MiniLM-L6-v2",
        "persist_directory": "data/chroma_db",
    }