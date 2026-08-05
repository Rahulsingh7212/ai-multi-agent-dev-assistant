from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from app.services.vector_service import vector_service
from typing import List, Tuple
import logging
import os
import glob

logger = logging.getLogger(__name__)


class IngestionService:
    """
    Handles document loading, chunking, and ingestion into ChromaDB.
    Supports PDF and TXT files.
    """

    SUPPORTED_EXTENSIONS = {".pdf", ".txt"}

    def ingest_directory(
        self,
        directory: str = "data/docs",
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
    ) -> Tuple[int, int, List[str]]:
        """
        Ingest all supported documents from a directory.
        Returns: (documents_loaded, chunks_created, files_processed)
        """
        all_chunks = []
        files_processed = []
        docs_loaded = 0

        # Find all supported files
        for ext in self.SUPPORTED_EXTENSIONS:
            pattern = os.path.join(directory, f"*{ext}")
            files = glob.glob(pattern)

            for file_path in files:
                try:
                    # Load document
                    docs = self._load_file(file_path)
                    if docs:
                        docs_loaded += len(docs)

                        # Split into chunks
                        chunks = self._split_documents(
                            docs, chunk_size, chunk_overlap
                        )
                        all_chunks.extend(chunks)

                        filename = os.path.basename(file_path)
                        files_processed.append(filename)
                        logger.info(
                            f"📄 Processed: {filename} "
                            f"({len(docs)} pages → {len(chunks)} chunks)"
                        )

                except Exception as e:
                    logger.error(f"❌ Failed to process {file_path}: {e}")
                    continue

        if not all_chunks:
            logger.warning("⚠️  No documents found to ingest")
            return 0, 0, []

        # Add all chunks to vector store
        vector_service.add_documents(all_chunks)

        return docs_loaded, len(all_chunks), files_processed

    def ingest_files(
        self,
        file_paths: List[str],
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
    ) -> Tuple[int, int, List[str]]:
        """
        Ingest specific files.
        Returns: (documents_loaded, chunks_created, files_processed)
        """
        all_chunks = []
        files_processed = []
        docs_loaded = 0

        for file_path in file_paths:
            try:
                docs = self._load_file(file_path)
                if docs:
                    docs_loaded += len(docs)
                    chunks = self._split_documents(docs, chunk_size, chunk_overlap)
                    all_chunks.extend(chunks)
                    files_processed.append(os.path.basename(file_path))

            except Exception as e:
                logger.error(f"❌ Failed to process {file_path}: {e}")
                continue

        if all_chunks:
            vector_service.add_documents(all_chunks)

        return docs_loaded, len(all_chunks), files_processed

    def _load_file(self, file_path: str) -> List:
        """Load a single file based on extension"""
        ext = os.path.splitext(file_path)[1].lower()

        if ext == ".pdf":
            loader = PyPDFLoader(file_path)
            docs = loader.load()
            # Add source metadata
            for doc in docs:
                doc.metadata["source_file"] = os.path.basename(file_path)
            return docs

        elif ext == ".txt":
            loader = TextLoader(file_path, encoding="utf-8")
            docs = loader.load()
            for doc in docs:
                doc.metadata["source_file"] = os.path.basename(file_path)
            return docs

        else:
            logger.warning(f"⚠️  Unsupported file type: {ext}")
            return []

    def _split_documents(
        self,
        docs: List,
        chunk_size: int,
        chunk_overlap: int,
    ) -> List:
        """Split documents into chunks"""
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""],
        )

        chunks = text_splitter.split_documents(docs)
        return chunks


# ============================
# Singleton instance
# ============================
ingestion_service = IngestionService()