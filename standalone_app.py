import streamlit as st
import logging
import json
import os
from pathlib import Path
from typing import List, Dict, Any
import uuid

# Simple in-memory storage for demo
class SimpleDocumentStore:
    def __init__(self):
        self.documents = []
        self.embeddings_cache = {}
    
    def add_document(self, content: str, metadata: dict):
        doc_id = str(uuid.uuid4())
        doc = {
            'id': doc_id,
            'content': content,
            'metadata': metadata
        }
        self.documents.append(doc)
        return doc_id
    
    def search(self, query: str, limit: int = 5) -> List[Dict]:
        # Simple text search (no embeddings for now)
        results = []
        query_lower = query.lower()
        
        for doc in self.documents:
            content_lower = doc['content'].lower()
            if any(word in content_lower for word in query_lower.split()):
                score = sum(1 for word in query_lower.split() if word in content_lower)
                results.append({
                    'content': doc['content'][:500] + '...' if len(doc['content']) > 500 else doc['content'],
                    'metadata': doc['metadata'],
                    'score': score / len(query_lower.split())
                })
        
        return sorted(results, key=lambda x: x['score'], reverse=True)[:limit]

class SimpleRAGBot:
    def __init__(self):
        self.document_store = SimpleDocumentStore()
        self.conversation_history = []
        
    def add_documents_from_text(self, text: str, filename: str):
        # Simple chunking
        chunks = [text[i:i+1000] for i in range(0, len(text), 800)]
        
        for i, chunk in enumerate(chunks):
            self.document_store.add_document(
                content=chunk,
                metadata={'source': filename, 'chunk': i}
            )
    
    def chat(self, user_message: str) -> str:
        # Search for relevant documents
        relevant_docs = self.document_store.search(user_message, limit=3)
        
        # Build context
        context = "\n\n".join([f"Document: {doc['content']}" for doc in relevant_docs])
        
        # Simple response generation (without LLM for now)
        if relevant_docs:
            response = f"Based on the documents, here's what I found:\n\n"
            for i, doc in enumerate(relevant_docs, 1):
                response += f"{i}. From {doc['metadata']['source']}: {doc['content'][:200]}...\n\n"
            response += f"This information relates to your question: '{user_message}'"
        else:
            response = f"I couldn't find relevant information about '{user_message}' in the uploaded documents. Please upload some documents first or try a different question."
        
        self.conversation_history.append({
            'user': user_message,
            'assistant': response
        })
        
        return response

# Streamlit app
st.set_page_config(
    page_title="Simple AI Document Chatbot",
    page_icon="🤖",
    layout="wide"
)

def init_session_state():
    if "bot" not in st.session_state:
        st.session_state.bot = SimpleRAGBot()
    if "messages" not in st.session_state:
        st.session_state.messages = []

def main():
    init_session_state()
    
    st.title("🤖 Simple AI Document Chatbot")
    st.markdown("**Standalone Demo Version** - Upload documents and ask questions!")
    
    # Sidebar for document upload
    with st.sidebar:
        st.header("📚 Document Upload")
        
        uploaded_files = st.file_uploader(
            "Upload text files, PDFs, or JSON files",
            type=['txt', 'pdf', 'json'],
            accept_multiple_files=True
        )
        
        if uploaded_files:
            for uploaded_file in uploaded_files:
                if st.button(f"Process {uploaded_file.name}"):
                    try:
                        if uploaded_file.type == "text/plain":
                            content = str(uploaded_file.read(), "utf-8")
                        elif uploaded_file.type == "application/json":
                            content = json.dumps(json.load(uploaded_file), indent=2)
                        elif uploaded_file.type == "application/pdf":
                            content = f"PDF file: {uploaded_file.name} (PDF processing requires additional setup)"
                        else:
                            content = str(uploaded_file.read(), "utf-8")
                        
                        st.session_state.bot.add_documents_from_text(content, uploaded_file.name)
                        st.success(f"Processed {uploaded_file.name}")
                        
                    except Exception as e:
                        st.error(f"Error processing {uploaded_file.name}: {e}")
        
        st.subheader("System Status")
        doc_count = len(st.session_state.bot.document_store.documents)
        st.metric("Documents Processed", doc_count)
        
        if st.button("Clear All Documents"):
            st.session_state.bot = SimpleRAGBot()
            st.session_state.messages = []
            st.success("All documents cleared!")
            st.rerun()
    
    # Main chat interface
    st.subheader("💬 Chat")
    
    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Chat input - must be at main level, not in columns or sidebar
    if prompt := st.chat_input("Ask a question about your documents..."):
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Get bot response
        with st.chat_message("assistant"):
            with st.spinner("Searching documents..."):
                response = st.session_state.bot.chat(prompt)
            st.markdown(response)
        
        # Add assistant message
        st.session_state.messages.append({"role": "assistant", "content": response})

if __name__ == "__main__":
    main()