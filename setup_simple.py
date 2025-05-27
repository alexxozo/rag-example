#!/usr/bin/env python3

import subprocess
import sys
import os
from pathlib import Path

def run_command(command):
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {command}")
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"❌ {command}")
        print(f"Error: {e.stderr}")
        return None

def main():
    print("🚀 Setting up Simple AI Document Chatbot...")
    
    # Create .env file if it doesn't exist
    env_file = Path(".env")
    if not env_file.exists():
        print("📝 Creating .env file...")
        env_content = """# OpenAI API Key (optional for basic demo)
OPENAI_API_KEY=your_openai_api_key_here

# Basic settings
DOCUMENTS_PATH=./documents
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
"""
        env_file.write_text(env_content)
        print("✅ .env file created")
    
    # Install basic dependencies
    print("📦 Installing basic dependencies...")
    basic_deps = [
        "streamlit",
        "python-dotenv"
    ]
    
    for dep in basic_deps:
        run_command(f"pip install {dep}")
    
    # Create documents directory
    docs_dir = Path("documents")
    docs_dir.mkdir(exist_ok=True)
    print("📁 Created documents directory")
    
    print("\n✅ Setup complete!")
    print("\nTo start the simple chatbot:")
    print("  streamlit run standalone_app.py")
    print("\nFeatures available:")
    print("  - Upload text/JSON files")
    print("  - Simple document search")
    print("  - Basic Q&A functionality")
    print("\nTo use the full version with embeddings and LLM:")
    print("  1. Install full requirements: pip install -r requirements.txt")
    print("  2. Set up Docker services for vector database")
    print("  3. Add OpenAI API key to .env")
    print("  4. Run: streamlit run streamlit_app.py")

if __name__ == "__main__":
    main()