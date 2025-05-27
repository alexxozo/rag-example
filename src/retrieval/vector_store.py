import logging
from typing import List, Dict, Any, Optional
import uuid
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance, VectorParams, PointStruct, 
    Filter, FieldCondition, Range, MatchValue
)
from sentence_transformers import SentenceTransformer
from openai import OpenAI
from src.core.config import settings
from src.ingestion.document_processor import DocumentChunk


class VectorStore:
    def __init__(self):
        self.client = QdrantClient(
            host=settings.qdrant_host, 
            port=settings.qdrant_port
        )
        self.collection_name = settings.collection_name
        self.logger = logging.getLogger(__name__)
        
        if settings.llm_provider == "openai" and settings.openai_api_key:
            self.openai_client = OpenAI(api_key=settings.openai_api_key)
            self.embedding_model = None
        else:
            self.openai_client = None
            self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        
        self._ensure_collection()

    def _ensure_collection(self):
        try:
            collections = self.client.get_collections()
            collection_names = [col.name for col in collections.collections]
            
            if self.collection_name not in collection_names:
                # Determine vector size based on embedding model
                if settings.llm_provider == "openai" and self.openai_client:
                    vector_size = 1536  # OpenAI text-embedding-ada-002
                else:
                    vector_size = 384   # all-MiniLM-L6-v2
                
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=vector_size, 
                        distance=Distance.COSINE
                    )
                )
                self.logger.info(f"Created collection: {self.collection_name} with vector size {vector_size}")
            else:
                # Check if existing collection has correct dimensions
                try:
                    collection_info = self.client.get_collection(self.collection_name)
                    existing_size = collection_info.config.params.vectors.size
                    expected_size = 1536 if (settings.llm_provider == "openai" and self.openai_client) else 384
                    
                    if existing_size != expected_size:
                        self.logger.warning(f"Collection has wrong vector size. Expected: {expected_size}, Got: {existing_size}")
                        self.logger.info("Deleting and recreating collection with correct dimensions...")
                        self.client.delete_collection(self.collection_name)
                        self.client.create_collection(
                            collection_name=self.collection_name,
                            vectors_config=VectorParams(
                                size=expected_size, 
                                distance=Distance.COSINE
                            )
                        )
                        self.logger.info(f"Recreated collection with vector size {expected_size}")
                    else:
                        self.logger.info(f"Collection {self.collection_name} exists with correct dimensions")
                except Exception as info_error:
                    self.logger.warning(f"Could not verify collection info: {info_error}")
                
        except Exception as e:
            self.logger.error(f"Error ensuring collection: {e}")
            raise

    def _get_embedding(self, text: str) -> List[float]:
        try:
            if settings.llm_provider == "openai" and self.openai_client:
                response = self.openai_client.embeddings.create(
                    model=settings.embedding_model,
                    input=text
                )
                return response.data[0].embedding
            else:
                return self.embedding_model.encode(text).tolist()
        except Exception as e:
            self.logger.error(f"Error generating embedding: {e}")
            raise

    def add_documents(self, chunks: List[DocumentChunk]) -> bool:
        try:
            points = []
            
            for chunk in chunks:
                embedding = self._get_embedding(chunk.content)
                
                point = PointStruct(
                    id=str(uuid.uuid4()),
                    vector=embedding,
                    payload={
                        "content": chunk.content,
                        "chunk_id": chunk.chunk_id,
                        **chunk.metadata
                    }
                )
                points.append(point)
            
            self.client.upsert(
                collection_name=self.collection_name,
                points=points
            )
            
            self.logger.info(f"Added {len(points)} documents to vector store")
            return True
            
        except Exception as e:
            self.logger.error(f"Error adding documents: {e}")
            return False

    def search(self, query: str, limit: int = 5, score_threshold: float = 0.5) -> List[Dict[str, Any]]:
        try:
            query_embedding = self._get_embedding(query)
            
            search_result = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding,
                limit=limit,
                score_threshold=score_threshold
            )
            
            results = []
            for scored_point in search_result:
                result = {
                    "content": scored_point.payload["content"],
                    "metadata": {k: v for k, v in scored_point.payload.items() if k != "content"},
                    "score": scored_point.score
                }
                results.append(result)
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error searching: {e}")
            return []

    def get_collection_info(self) -> Dict[str, Any]:
        try:
            info = self.client.get_collection(self.collection_name)
            return {
                "name": self.collection_name,
                "vectors_count": getattr(info, 'vectors_count', 0),
                "status": getattr(info, 'status', 'unknown')
            }
        except Exception as e:
            self.logger.error(f"Error getting collection info: {e}")
            return {
                "name": self.collection_name,
                "vectors_count": 0,
                "status": "error"
            }

    def delete_collection(self):
        try:
            self.client.delete_collection(self.collection_name)
            self.logger.info(f"Deleted collection: {self.collection_name}")
        except Exception as e:
            self.logger.error(f"Error deleting collection: {e}")
            raise