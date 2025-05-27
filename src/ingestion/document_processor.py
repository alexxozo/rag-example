import json
import logging
from pathlib import Path
from typing import List, Dict, Any
import PyPDF2
from pydantic import BaseModel


class DocumentChunk(BaseModel):
    content: str
    metadata: Dict[str, Any]
    chunk_id: str


class DocumentProcessor:
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.logger = logging.getLogger(__name__)

    def process_pdf(self, file_path: Path) -> List[DocumentChunk]:
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""
                
                for page_num, page in enumerate(pdf_reader.pages):
                    page_text = page.extract_text()
                    text += f"\n\nPage {page_num + 1}:\n{page_text}"
                
                chunks = self._chunk_text(text)
                
                return [
                    DocumentChunk(
                        content=chunk,
                        metadata={
                            "source": str(file_path),
                            "type": "pdf",
                            "total_pages": len(pdf_reader.pages),
                            "chunk_index": idx
                        },
                        chunk_id=f"{file_path.stem}_{idx}"
                    )
                    for idx, chunk in enumerate(chunks)
                ]
                
        except Exception as e:
            self.logger.error(f"Error processing PDF {file_path}: {e}")
            return []

    def process_json(self, file_path: Path) -> List[DocumentChunk]:
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
                
            text = self._json_to_text(data)
            chunks = self._chunk_text(text)
            
            return [
                DocumentChunk(
                    content=chunk,
                    metadata={
                        "source": str(file_path),
                        "type": "json",
                        "chunk_index": idx
                    },
                    chunk_id=f"{file_path.stem}_{idx}"
                )
                for idx, chunk in enumerate(chunks)
            ]
            
        except Exception as e:
            self.logger.error(f"Error processing JSON {file_path}: {e}")
            return []

    def _json_to_text(self, data: Any, path: str = "") -> str:
        if isinstance(data, dict):
            text_parts = []
            for key, value in data.items():
                current_path = f"{path}.{key}" if path else key
                if isinstance(value, (dict, list)):
                    text_parts.append(f"{current_path}:")
                    text_parts.append(self._json_to_text(value, current_path))
                else:
                    text_parts.append(f"{current_path}: {value}")
            return "\n".join(text_parts)
        
        elif isinstance(data, list):
            text_parts = []
            for idx, item in enumerate(data):
                current_path = f"{path}[{idx}]"
                text_parts.append(self._json_to_text(item, current_path))
            return "\n".join(text_parts)
        
        else:
            return str(data)

    def _chunk_text(self, text: str) -> List[str]:
        if len(text) <= self.chunk_size:
            return [text]
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + self.chunk_size
            
            if end >= len(text):
                chunks.append(text[start:])
                break
            
            chunk_end = text.rfind(' ', start, end)
            if chunk_end == -1:
                chunk_end = end
            
            chunks.append(text[start:chunk_end])
            start = chunk_end - self.chunk_overlap
            
            if start < 0:
                start = 0
        
        return [chunk.strip() for chunk in chunks if chunk.strip()]

    def process_directory(self, directory_path: Path) -> List[DocumentChunk]:
        all_chunks = []
        
        for file_path in directory_path.rglob("*"):
            if file_path.is_file():
                if file_path.suffix.lower() == '.pdf':
                    chunks = self.process_pdf(file_path)
                    all_chunks.extend(chunks)
                elif file_path.suffix.lower() == '.json':
                    chunks = self.process_json(file_path)
                    all_chunks.extend(chunks)
                else:
                    self.logger.info(f"Skipping unsupported file: {file_path}")
        
        return all_chunks