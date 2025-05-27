import pytest
from unittest.mock import Mock, patch, MagicMock
from src.retrieval.vector_store import VectorStore
from src.ingestion.document_processor import DocumentChunk


class TestVectorStore:
    def setup_method(self):
        with patch('src.retrieval.vector_store.QdrantClient'), \
             patch.object(VectorStore, '_ensure_collection'):
            self.vector_store = VectorStore()
            self.vector_store.client = Mock()

    def test_get_embedding_openai(self):
        with patch('src.retrieval.vector_store.settings') as mock_settings, \
             patch('src.retrieval.vector_store.openai') as mock_openai:
            
            mock_settings.llm_provider = "openai"
            mock_openai.Embedding.create.return_value = {
                'data': [{'embedding': [0.1, 0.2, 0.3]}]
            }
            
            embedding = self.vector_store._get_embedding("test text")
            assert embedding == [0.1, 0.2, 0.3]

    def test_search_success(self):
        mock_result = [
            Mock(
                payload={"content": "test content", "source": "test.pdf"},
                score=0.9
            )
        ]
        self.vector_store.client.search.return_value = mock_result
        
        with patch.object(self.vector_store, '_get_embedding', return_value=[0.1, 0.2]):
            results = self.vector_store.search("test query")
            
            assert len(results) == 1
            assert results[0]["content"] == "test content"
            assert results[0]["score"] == 0.9

    def test_add_documents_success(self):
        chunk = DocumentChunk(
            content="test content",
            metadata={"source": "test.pdf"},
            chunk_id="test_chunk_1"
        )
        
        self.vector_store.client.upsert.return_value = True
        
        with patch.object(self.vector_store, '_get_embedding', return_value=[0.1, 0.2]):
            result = self.vector_store.add_documents([chunk])
            assert result is True