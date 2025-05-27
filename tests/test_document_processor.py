import pytest
import json
from pathlib import Path
from unittest.mock import Mock, patch
from src.ingestion.document_processor import DocumentProcessor, DocumentChunk


class TestDocumentProcessor:
    def setup_method(self):
        self.processor = DocumentProcessor(chunk_size=100, chunk_overlap=20)

    def test_chunk_text_simple(self):
        text = "This is a short text that should not be chunked."
        chunks = self.processor._chunk_text(text)
        assert len(chunks) == 1
        assert chunks[0] == text

    def test_chunk_text_long(self):
        text = "This is a longer text. " * 20
        chunks = self.processor._chunk_text(text)
        assert len(chunks) > 1
        assert all(len(chunk) <= self.processor.chunk_size for chunk in chunks)

    def test_json_to_text_simple(self):
        data = {"key1": "value1", "key2": "value2"}
        text = self.processor._json_to_text(data)
        assert "key1: value1" in text
        assert "key2: value2" in text

    def test_json_to_text_nested(self):
        data = {
            "level1": {
                "level2": "nested_value"
            },
            "array": [1, 2, 3]
        }
        text = self.processor._json_to_text(data)
        assert "level1.level2: nested_value" in text
        assert "array[0]: 1" in text

    @patch('builtins.open')
    @patch('json.load')
    def test_process_json_success(self, mock_json_load, mock_open):
        test_data = {"test": "data"}
        mock_json_load.return_value = test_data
        
        test_path = Path("test.json")
        chunks = self.processor.process_json(test_path)
        
        assert len(chunks) > 0
        assert chunks[0].metadata["type"] == "json"
        assert chunks[0].metadata["source"] == str(test_path)

    def test_process_directory_empty(self):
        with patch.object(Path, 'rglob') as mock_rglob:
            mock_rglob.return_value = []
            
            chunks = self.processor.process_directory(Path("test_dir"))
            assert len(chunks) == 0