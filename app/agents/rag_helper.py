from app.services.vector_service import vector_service
from langchain_core.documents import Document
from typing import Optional, List
import logging

logger = logging.getLogger(__name__)


def get_rag_context(query: str, k: int = 3) -> dict:
    """
    Retrieve relevant document context for a query.
    Returns dict with context string and sources list.

    Used by agents to ground their responses in documentation.
    """
    if not vector_service.has_vectorstore():
        logger.info("ℹ️  No vectorstore available — skipping RAG context")
        return {"context": None, "sources": []}

    try:
        retriever = vector_service.get_retriever(k=k)
        docs: List[Document] = retriever.invoke(query)

        if not docs:
            return {"context": None, "sources": []}

        # Format context
        context_parts = []
        sources = []

        for i, doc in enumerate(docs, 1):
            source_file = doc.metadata.get("source_file", "Unknown")
            page = doc.metadata.get("page", "N/A")
            context_parts.append(
                f"[Doc {i}: {source_file}, Page {page}]\n{doc.page_content}"
            )
            sources.append(f"{source_file} (Page: {page})")

        context = "\n\n---\n\n".join(context_parts)

        logger.info(f"🔍 RAG context retrieved: {len(docs)} chunks for query")

        return {"context": context, "sources": sources}

    except Exception as e:
        logger.error(f"❌ RAG context retrieval failed: {e}")
        return {"context": None, "sources": []}