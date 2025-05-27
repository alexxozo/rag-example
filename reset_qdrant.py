#!/usr/bin/env python3

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from src.retrieval.vector_store import VectorStore
import logging

logging.basicConfig(level=logging.INFO)

def main():
    print("🔄 Resetting Qdrant collection...")
    
    try:
        vector_store = VectorStore()
        vector_store.delete_collection()
        print("✅ Collection deleted and recreated with correct dimensions")
        
        # Test the collection
        info = vector_store.get_collection_info()
        print(f"📊 Collection info: {info}")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()