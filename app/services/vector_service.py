from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from config.settings import settings
from typing import List, Optional
import logging
import os

logger = logging.getLogger(__name__)


class VectorService:
    """
    Manages ChromaDB vector store and HuggingFace embeddings.
    Uses local embeddings (FREE) — no API key needed.
    """

    def __init__(self):
        self._embeddings = None
        self._vectorstore = None
        self._persist_directory = os.path.join("data", "chroma_db")
        self._initialize_embeddings()
        self._load_existing_vectorstore()

    def _initialize_embeddings(self):
        """Initialize HuggingFace local embeddings"""
        try:
            self._embeddings = HuggingFaceEmbeddings(
                model_name="all-MiniLM-L6-v2",
                model_kwargs={"device": "cpu"},
                encode_kwargs={"normalize_embeddings": True},
            )

            
            logger.info("✅ HuggingFace embeddings initialized (all-MiniLM-L6-v2)")

        except Exception as e:
            logger.error(f"❌ Embeddings initialization failed: {e}")
            raise

    def _load_existing_vectorstore(self):
        """Load existing ChromaDB if it exists"""
        try:
            if os.path.exists(self._persist_directory):
                files = os.listdir(self._persist_directory)
                if files:
                    self._vectorstore = Chroma(
                        persist_directory=self._persist_directory,
                        embedding_function=self._embeddings,
                    )
                    count = self._vectorstore._collection.count()
                    logger.info(f"✅ Loaded existing ChromaDB ({count} vectors)")
                    return

            logger.info("ℹ️  No existing ChromaDB found — will create on first ingestion")

        except Exception as e:
            logger.warning(f"⚠️  Could not load existing ChromaDB: {e}")

    @property
    def vectorstore(self) -> Optional[Chroma]:
        return self._vectorstore

    @property
    def embeddings(self):
        return self._embeddings

    def has_vectorstore(self) -> bool:
        return self._vectorstore is not None

    def get_document_count(self) -> int:
        """Get number of documents in vector store"""
        if self._vectorstore:
            return self._vectorstore._collection.count()
        return 0

    def add_documents(self, chunks: List) -> None:
        """Add document chunks to ChromaDB"""
        try:
            if self._vectorstore is None:
                # Create new vectorstore
                self._vectorstore = Chroma.from_documents(
                    documents=chunks,
                    embedding=self._embeddings,
                    persist_directory=self._persist_directory,
                )
            else:
                # Add to existing vectorstore
                self._vectorstore.add_documents(chunks)

            # Persist to disk
            self._vectorstore.persist()

            count = self._vectorstore._collection.count()
            logger.info(f"✅ Added {len(chunks)} chunks to ChromaDB (total: {count})")

        except Exception as e:
            logger.error(f"❌ Failed to add documents: {e}")
            raise

    def get_retriever(self, k: int = 4):
        """Get a retriever from the vector store"""
        if not self._vectorstore:
            raise ValueError("No documents ingested yet. Call /api/v1/ingest first.")

        return self._vectorstore.as_retriever(
            search_type="similarity",
            search_kwargs={"k": k},
        )


# ============================
# Singleton instance
# ============================
vector_service = VectorService()