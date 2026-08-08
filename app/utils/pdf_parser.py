import pymupdf  # PyMuPDF
from typing import Optional
import logging
import os

logger = logging.getLogger(__name__)


def extract_text_from_pdf(file_path: str) -> str:
    """
    Extract all text content from a PDF file using PyMuPDF.

    Args:
        file_path: Path to the PDF file

    Returns:
        Extracted text content
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"PDF not found: {file_path}")

    try:
        doc = pymupdf.open(file_path)
        text_parts = []

        for page_num, page in enumerate(doc):
            text = page.get_text()
            if text.strip():
                text_parts.append(f"--- Page {page_num + 1} ---\n{text}")

        doc.close()

        full_text = "\n\n".join(text_parts)
        logger.info(f"✅ Extracted {len(full_text)} chars from {os.path.basename(file_path)} ({doc.page_count} pages)")

        return full_text

    except Exception as e:
        logger.error(f"❌ PDF extraction failed: {e}")
        raise


def extract_text_from_file(file_path: str) -> str:
    """
    Extract text from a file (PDF or TXT).

    Args:
        file_path: Path to the file

    Returns:
        Extracted text content
    """
    ext = os.path.splitext(file_path)[1].lower()

    if ext == ".pdf":
        return extract_text_from_pdf(file_path)
    elif ext == ".txt":
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    else:
        raise ValueError(f"Unsupported file type: {ext}")