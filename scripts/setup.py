#!/usr/bin/env python3

import os
import sys
import subprocess
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_command(command: str, cwd: Path = None):
    try:
        result = subprocess.run(
            command.split(),
            cwd=cwd,
            check=True,
            capture_output=True,
            text=True
        )
        logger.info(f"✅ {command}")
        return result.stdout
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ {command}")
        logger.error(f"Error: {e.stderr}")
        return None

def main():
    project_root = Path(__file__).parent.parent
    
    logger.info("🚀 Setting up AI Document Chatbot...")
    
    if not (project_root / ".env").exists():
        logger.info("📝 Creating .env file from template...")
        env_example = project_root / ".env.example"
        env_file = project_root / ".env"
        
        if env_example.exists():
            env_file.write_text(env_example.read_text())
            logger.info("✅ .env file created. Please update it with your API keys.")
        else:
            logger.error("❌ .env.example not found")
    
    logger.info("📦 Installing Python dependencies...")
    run_command("pip install -r requirements.txt", cwd=project_root)
    
    logger.info("🐳 Starting Docker services...")
    run_command("docker-compose up -d", cwd=project_root)
    
    logger.info("📁 Creating necessary directories...")
    (project_root / "documents").mkdir(exist_ok=True)
    (project_root / "data" / "qdrant").mkdir(parents=True, exist_ok=True)
    (project_root / "data" / "minio").mkdir(parents=True, exist_ok=True)
    (project_root / "data" / "n8n").mkdir(parents=True, exist_ok=True)
    (project_root / "data" / "postgres").mkdir(parents=True, exist_ok=True)
    
    logger.info("✅ Setup complete!")
    logger.info("\nNext steps:")
    logger.info("1. Update .env file with your OpenAI API key")
    logger.info("2. Upload documents via MinIO console or place in 'documents' folder")
    logger.info("3. Run: streamlit run streamlit_app.py")
    logger.info("4. Access services:")
    logger.info("   - Streamlit Chat: http://localhost:8501")
    logger.info("   - MinIO Console: http://localhost:9001 (minioadmin/minioadmin123)")
    logger.info("   - Qdrant Dashboard: http://localhost:6333/dashboard")
    logger.info("   - n8n Workflows: http://localhost:5678 (admin/admin123)")
    logger.info("   - Langfuse: http://localhost:3000 (optional)")
    logger.info("\n📝 Note: MinIO is configured as local S3 storage")

if __name__ == "__main__":
    main()