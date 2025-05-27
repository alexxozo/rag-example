#!/usr/bin/env python3

import sys
import logging
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from src.utils.s3_sync import S3Sync
from src.ingestion.pipeline import IngestionPipeline

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    logger.info("🔄 Starting S3 sync and document processing...")
    
    s3_sync = S3Sync()
    
    if not s3_sync.is_configured():
        logger.error("❌ S3 not configured. Please check your .env file.")
        return
    
    logger.info("📥 Syncing documents from S3...")
    success = s3_sync.sync_documents()
    
    if not success:
        logger.error("❌ Failed to sync documents from S3")
        return
    
    logger.info("🔄 Processing downloaded documents...")
    pipeline = IngestionPipeline()
    success = pipeline.process_documents()
    
    if success:
        logger.info("✅ Documents synced and processed successfully!")
        status = pipeline.get_ingestion_status()
        if "collection_info" in status:
            count = status["collection_info"].get("vectors_count", 0)
            logger.info(f"📊 Total documents in database: {count}")
    else:
        logger.error("❌ Failed to process documents")

if __name__ == "__main__":
    main()