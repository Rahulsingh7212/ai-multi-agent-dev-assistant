import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)

try:
    import fitz  # PyMuPDF
except ImportError:
    fitz = None


def extract_text_from_file(file_path: str) -> str:
    """
    Extract text from PDF or plain text files.

    PDF documents are kept open while all pages are processed,
    avoiding 'document closed' errors.
    """

    if not file_path:
        raise ValueError("File path is required")

    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    extension = os.path.splitext(file_path)[1].lower()

    # ============================
    # PDF
    # ============================
    if extension == ".pdf":
        if fitz is None:
            raise RuntimeError(
                "PyMuPDF is not installed. Run: pip install pymupdf"
            )

        try:
            text_parts = []

            # IMPORTANT:
            # Keep the PDF document open while reading every page.
            with fitz.open(file_path) as document:
                logger.info(
                    f"📄 Reading PDF: {os.path.basename(file_path)} "
                    f"({document.page_count} pages)"
                )

                for page_number in range(document.page_count):
                    page = document.load_page(page_number)
                    page_text = page.get_text("text")

                    if page_text:
                        text_parts.append(page_text)

            extracted_text = "\n\n".join(text_parts).strip()

            logger.info(
                f"✅ PDF extraction complete: {len(extracted_text)} chars"
            )

            return extracted_text

        except Exception as e:
            logger.error(f"❌ PDF extraction failed: {e}")
            raise

    # ============================
    # TXT
    # ============================
    if extension == ".txt":
        try:
            with open(
                file_path,
                "r",
                encoding="utf-8",
                errors="ignore",
            ) as file:
                text = file.read()

            logger.info(
                f"✅ TXT extraction complete: {len(text)} chars"
            )

            return text.strip()

        except Exception as e:
            logger.error(f"❌ TXT extraction failed: {e}")
            raise

    # ============================
    # Unsupported
    # ============================
    raise ValueError(
        f"Unsupported file type: {extension}. "
        f"Supported types: .pdf, .txt"
    )