import logging
from pathlib import Path
from typing import List, Optional
from src.core.config import settings
from src.ingestion.document_processor import DocumentProcessor
from src.retrieval.vector_store import VectorStore


class IngestionPipeline:
    def __init__(self):
        self.document_processor = DocumentProcessor(
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap
        )
        self.vector_store = VectorStore()
        self.logger = logging.getLogger(__name__)

    def process_documents(self, documents_path: Optional[str] = None) -> bool:
        try:
            docs_path = Path(documents_path or settings.documents_path)
            
            if not docs_path.exists():
                self.logger.error(f"Documents path does not exist: {docs_path}")
                return False
            
            self.logger.info(f"Starting document processing from: {docs_path}")
            
            chunks = self.document_processor.process_directory(docs_path)
            
            if not chunks:
                self.logger.warning("No documents found or processed")
                return False
            
            self.logger.info(f"Processed {len(chunks)} document chunks")
            
            success = self.vector_store.add_documents(chunks)
            
            if success:
                self.logger.info("Successfully added documents to vector store")
                return True
            else:
                self.logger.error("Failed to add documents to vector store")
                return False
                
        except Exception as e:
            self.logger.error(f"Error in ingestion pipeline: {e}")
            return False

    def get_ingestion_status(self) -> dict:
        try:
            return {
                "collection_info": self.vector_store.get_collection_info(),
                "documents_path": settings.documents_path,
                "chunk_size": settings.chunk_size,
                "chunk_overlap": settings.chunk_overlap
            }
        except Exception as e:
            self.logger.error(f"Error getting ingestion status: {e}")
            return {"error": str(e)}

    def clear_vector_store(self) -> bool:
        try:
            self.vector_store.delete_collection()
            self.vector_store._ensure_collection()
            self.logger.info("Cleared vector store")
            return True
        except Exception as e:
            self.logger.error(f"Error clearing vector store: {e}")
            return False