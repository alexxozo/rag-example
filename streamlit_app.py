import streamlit as st
import logging
from pathlib import Path
import uuid
from src.chat.chatbot import RAGChatbot
from src.ingestion.pipeline import IngestionPipeline
from src.utils.s3_sync import S3Sync
from src.core.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

st.set_page_config(
    page_title="AI Document Chatbot",
    page_icon="🤖",
    layout="wide"
)

def init_session_state():
    if "chatbot" not in st.session_state:
        st.session_state.chatbot = RAGChatbot()
    if "session_id" not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())
    if "messages" not in st.session_state:
        st.session_state.messages = []

def display_chat_interface():
    st.title("🤖 AI Document Chatbot")
    st.markdown("Ask questions about your documents and get AI-powered answers!")
    
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    if prompt := st.chat_input("Ask a question about your documents..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                response = st.session_state.chatbot.chat(
                    prompt, 
                    session_id=st.session_state.session_id
                )
            st.markdown(response)
        
        st.session_state.messages.append({"role": "assistant", "content": response})

def display_sidebar():
    with st.sidebar:
        st.header("📚 Document Management")
        
        pipeline = IngestionPipeline()
        
        st.subheader("Upload Documents")
        uploaded_files = st.file_uploader(
            "Choose PDF or JSON files",
            type=['pdf', 'json'],
            accept_multiple_files=True
        )
        
        if uploaded_files:
            if st.button("Process Uploaded Files"):
                docs_path = Path(settings.documents_path)
                docs_path.mkdir(exist_ok=True)
                
                for uploaded_file in uploaded_files:
                    file_path = docs_path / uploaded_file.name
                    with open(file_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())
                
                with st.spinner("Processing documents..."):
                    success = pipeline.process_documents()
                
                if success:
                    st.success("Documents processed successfully!")
                    st.rerun()
                else:
                    st.error("Failed to process documents")
        
        st.subheader("Sync from S3/MinIO")
        s3_sync = S3Sync()
        
        if s3_sync.is_configured():
            if st.button("Sync from S3/MinIO"):
                with st.spinner("Syncing from S3/MinIO..."):
                    sync_success = s3_sync.sync_documents()
                    if sync_success:
                        process_success = pipeline.process_documents()
                        if process_success:
                            st.success("Documents synced and processed successfully!")
                        else:
                            st.warning("Documents synced but processing failed")
                    else:
                        st.error("Failed to sync documents")
                st.rerun()
        else:
            st.info("Configure S3/MinIO credentials in .env to enable sync")
        
        st.subheader("Process Existing Documents")
        if st.button("Process Documents Folder"):
            with st.spinner("Processing documents..."):
                success = pipeline.process_documents()
            
            if success:
                st.success("Documents processed successfully!")
                st.rerun()
            else:
                st.error("Failed to process documents")
        
        st.subheader("System Status")
        status = pipeline.get_ingestion_status()
        
        if "collection_info" in status:
            collection_info = status["collection_info"]
            st.metric("Documents in Database", collection_info.get("vectors_count", 0))
            st.text(f"Status: {collection_info.get('status', 'Unknown')}")
        
        st.subheader("Settings")
        st.text(f"Documents Path: {settings.documents_path}")
        st.text(f"Chunk Size: {settings.chunk_size}")
        st.text(f"LLM Provider: {settings.llm_provider}")
        
        if settings.s3_endpoint_url:
            st.text(f"S3 Storage: MinIO ({settings.s3_endpoint_url})")
        else:
            st.text("S3 Storage: AWS S3")
        
        # Show MinIO console link if using local MinIO
        if settings.s3_endpoint_url and "localhost:9000" in settings.s3_endpoint_url:
            st.markdown("🗂️ [MinIO Console](http://localhost:9001) (minioadmin/minioadmin123)")
        
        if st.button("Clear Chat History"):
            st.session_state.messages = []
            st.session_state.chatbot.clear_history()
            st.rerun()
        
        if st.button("Clear Vector Database"):
            with st.spinner("Clearing database..."):
                success = pipeline.clear_vector_store()
            
            if success:
                st.success("Database cleared!")
                st.rerun()
            else:
                st.error("Failed to clear database")

def main():
    init_session_state()
    
    # Sidebar
    display_sidebar()
    
    # Main chat interface
    display_chat_interface()

if __name__ == "__main__":
    main()