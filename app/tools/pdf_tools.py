from langchain_core.tools import tool
from typing import Optional
import logging

logger = logging.getLogger(__name__)


@tool
def pdf_query(question: str, context: str) -> str:
    """
    Answer a question based on PDF document content using RAG context.

    Args:
        question: User's question about the document
        context: RAG-retrieved context from the document

    Returns:
        Prompt for LLM to answer the question
    """
    logger.info(f"🔧 pdf_query called: {question[:50]}...")

    prompt = f"""Answer the following question based ONLY on the provided document context.

DOCUMENT CONTEXT:
{context}

QUESTION: {question}

Provide a thorough, accurate answer with specific references to the document.
If the context doesn't contain enough information, say so clearly."""

    return prompt


@tool
def pdf_summarize(context: str, focus_area: Optional[str] = None) -> str:
    """
    Summarize document content, optionally focusing on a specific area.

    Args:
        context: RAG-retrieved context from the document
        focus_area: Optional area to focus the summary on

    Returns:
        Prompt for LLM to generate summary
    """
    logger.info(f"🔧 pdf_summarize called (focus: {focus_area})")

    focus_section = ""
    if focus_area:
        focus_section = f"\nFocus the summary specifically on: {focus_area}"

    prompt = f"""Summarize the following document content:

DOCUMENT CONTEXT:
{context}
{focus_section}

Provide:
1. **Executive Summary**: 2-3 sentence overview
2. **Key Points**: Main points in bullet format
3. **Important Details**: Specific numbers, dates, names mentioned
4. **Topics Covered**: Main topics/sections in the document"""

    return prompt


@tool
def pdf_compare(context_a: str, context_b: str) -> str:
    """
    Compare two documents or document sections.

    Args:
        context_a: First document's content
        context_b: Second document's content

    Returns:
        Prompt for LLM to compare documents
    """
    logger.info("🔧 pdf_compare called")

    prompt = f"""Compare the following two document sections:

DOCUMENT A:
{context_a}

DOCUMENT B:
{context_b}

Provide:
1. **Similarities**: What both documents share
2. **Differences**: Key differences between them
3. **Unique to A**: Content only in Document A
4. **Unique to B**: Content only in Document B
5. **Recommendation**: Which is better and why (if applicable)"""

    return prompt


# ============================
# TOOL REGISTRY
# ============================
PDF_AGENT_TOOLS = [pdf_query, pdf_summarize, pdf_compare]

PDF_TOOL_MAP = {
    "pdf_query": pdf_query,
    "pdf_summarize": pdf_summarize,
    "pdf_compare": pdf_compare,
}