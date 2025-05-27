import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    openai_api_key: Optional[str] = None
    
    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None
    aws_region: str = "us-east-1"
    s3_bucket_name: Optional[str] = None
    s3_endpoint_url: Optional[str] = None
    
    qdrant_host: str = "localhost"
    qdrant_port: int = 6333
    
    langfuse_public_key: Optional[str] = None
    langfuse_secret_key: Optional[str] = None
    langfuse_host: str = "http://localhost:3000"
    
    documents_path: str = "./documents"
    data_path: str = "./data"
    
    llm_provider: str = "openai"
    ollama_host: str = "http://localhost:11434"
    embedding_model: str = "text-embedding-ada-002"
    
    collection_name: str = "documents"
    chunk_size: int = 1000
    chunk_overlap: int = 200
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()