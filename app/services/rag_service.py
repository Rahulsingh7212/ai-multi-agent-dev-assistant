from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langchain_core.messages import SystemMessage, HumanMessage
from app.services.llm_service import llm_service
from app.services.vector_service import vector_service
from typing import List
import logging

logger = logging.getLogger(__name__)


class RAGService:
    """
    Retrieval-Augmented Generation service.
    Combines document retrieval with LLM generation.
    """

    def __init__(self):
        self._llm = llm_service._llm  # Use non-streaming LLM

        # RAG Prompt Template
        self._prompt = ChatPromptTemplate.from_template(
            """You are an expert AI Developer Assistant with access to the user's documentation.
Answer the question based ONLY on the provided context.
If the context does not contain enough information to answer, say:
"I don't have enough information in the provided documents to answer this question."

Always cite which source file the information comes from.

====================
CONTEXT:
{context}
====================

QUESTION: {question}

ANSWER:"""
        )

    def query(self, question: str, k: int = 4) -> dict:
        """
        Perform RAG query.
        Returns dict with answer, sources, and metadata.
        """
        if not vector_service.has_vectorstore():
            raise ValueError(
                "No documents ingested yet. Please call /api/v1/ingest first."
            )

        # Step 1: Retrieve relevant chunks
        retriever = vector_service.get_retriever(k=k)
        retrieved_docs = retriever.invoke(question)

        # Step 2: Format context from retrieved chunks
        context_text = self._format_docs(retrieved_docs)
        sources = self._extract_sources(retrieved_docs)

        logger.info(f"🔍 Retrieved {len(retrieved_docs)} chunks for query")

        # Step 3: Generate answer using LLM
        chain = self._prompt | self._llm | StrOutputParser()

        answer = chain.invoke({
            "context": context_text,
            "question": question,
        })

        logger.info(f"💬 RAG answer generated ({len(answer)} chars)")

        return {
            "answer": answer,
            "sources": sources,
            "chunks_retrieved": len(retrieved_docs),
        }

    def _format_docs(self, docs: List) -> str:
        """Format retrieved documents into context string"""
        formatted = []
        for i, doc in enumerate(docs, 1):
            source = doc.metadata.get("source_file", "Unknown")
            page = doc.metadata.get("page", "N/A")
            formatted.append(
                f"[Source {i}: {source} (Page: {page})]\n{doc.page_content}"
            )
        return "\n\n---\n\n".join(formatted)

    def _extract_sources(self, docs: List) -> List[str]:
        """Extract unique source file names"""
        sources = []
        for doc in docs:
            source = doc.metadata.get("source_file", "Unknown")
            page = doc.metadata.get("page", "N/A")
            sources.append(f"{source} (Page: {page})")
        return sources


# ============================
# Singleton instance
# ============================
rag_service = RAGService()