# AI Document Chatbot with Memory Layer

A prototype system that enables conversational Q&A over a corpus of documents using retrieval-augmented generation (RAG), vector search, and AI-powered chat.

## Features

- 📚 **Document Processing**: Supports PDF and JSON files with automated text extraction and chunking
- 🔍 **Vector Search**: Uses Qdrant for efficient semantic search over document embeddings
- 🤖 **AI Chat**: RAG-powered chatbot with conversational memory
- 📊 **Observability**: Integrated Langfuse for LLM monitoring and tracing
- ☁️ **S3 Integration**: Automated document sync from AWS S3 or local MinIO
- 🔄 **Workflow Automation**: n8n for document processing workflows
- 🎨 **User Interface**: Clean Streamlit-based chat interface

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ S3/MinIO Storage│────│  Document Sync  │────│ Local Documents │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                        │
                                                        ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Streamlit     │────│   RAG Chatbot   │────│ Document Processor│
│   Interface     │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │                        │
                                ▼                        ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│    Langfuse     │    │     Qdrant      │────│   Embeddings    │
│  Observability  │    │  Vector Store   │    │   Generation    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Quick Start

### 1. Setup

```bash
# Clone and navigate to project
cd ai-agent-project

# Run setup script
python scripts/setup.py
```

This will:
- Create `.env` file from template
- Install Python dependencies
- Start Docker services (Qdrant, n8n, Langfuse)
- Create necessary directories

### 2. Configuration

Update `.env` file with your API keys:

```env
# Required for AI chat
OPENAI_API_KEY=your_openai_api_key_here

# MinIO (local S3) - preconfigured, no changes needed
AWS_ACCESS_KEY_ID=minioadmin
AWS_SECRET_ACCESS_KEY=minioadmin123
S3_BUCKET_NAME=documents
S3_ENDPOINT_URL=http://localhost:9000

# Optional: For AWS S3 instead of MinIO
# AWS_ACCESS_KEY_ID=your_aws_access_key_here
# AWS_SECRET_ACCESS_KEY=your_aws_secret_key_here
# S3_ENDPOINT_URL=

# Optional: For observability (leave empty to disable)
LANGFUSE_PUBLIC_KEY=
LANGFUSE_SECRET_KEY=
```

### 3. Add Documents

**Option A: Local Upload**
- Place PDF/JSON files in the `documents/` folder
- Use Streamlit interface to process them

**Option B: MinIO/S3 Sync**
```bash
# For MinIO (default setup)
python scripts/sync_s3.py

# Or use MinIO web console at http://localhost:9001
```

### 4. Start Chat Interface

```bash
streamlit run streamlit_app.py
```

Access the chat interface at: http://localhost:8501

## Usage

### Document Management

1. **Upload Documents**: Use the Streamlit sidebar to upload PDF/JSON files
2. **Process Documents**: Click "Process Documents" to extract text and generate embeddings
3. **S3 Sync**: Configure S3 credentials and use the sync script for automated updates

### Chat Interface

- Ask questions about your documents in natural language
- The system will retrieve relevant document chunks and provide contextualized answers
- Conversation history is maintained within each session

### Monitoring

- **MinIO Console**: http://localhost:9001 - S3-compatible storage (minioadmin/minioadmin123)
- **Qdrant Dashboard**: http://localhost:6333/dashboard - Vector database management
- **n8n Workflows**: http://localhost:5678 - Automation workflows (admin/admin123)
- **Langfuse**: http://localhost:3000 - LLM observability (optional)

## Technical Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Chat Interface** | Streamlit | User-friendly web interface |
| **Document Processing** | PyPDF2, JSON | Text extraction from documents |
| **Vector Database** | Qdrant | Semantic search and retrieval |
| **Embeddings** | OpenAI/SentenceTransformers | Text vectorization |
| **LLM** | OpenAI GPT-3.5-turbo | Response generation |
| **Observability** | Langfuse | LLM monitoring and tracing |
| **Workflow Automation** | n8n | Document processing pipelines |
| **Storage** | MinIO/AWS S3 | Document source storage |

## Project Structure

```
ai-agent-project/
├── src/
│   ├── core/           # Configuration and settings
│   ├── ingestion/      # Document processing pipeline
│   ├── retrieval/      # Vector search and retrieval
│   ├── chat/           # RAG chatbot implementation
│   └── utils/          # S3 sync and utilities
├── scripts/            # Setup and maintenance scripts
├── documents/          # Local document storage
├── data/              # Docker volume data
├── tests/             # Test files
├── docker-compose.yml # Service orchestration
├── streamlit_app.py   # Main chat interface
└── requirements.txt   # Python dependencies
```

## Development

### Running Tests

```bash
python -m pytest tests/
```

### Adding New Document Types

1. Extend `DocumentProcessor` in `src/ingestion/document_processor.py`
2. Add new processing method following existing patterns
3. Update file type detection in `process_directory`

### Customizing Chat Behavior

Modify the prompt template in `src/chat/chatbot.py` to adjust:
- Response tone and style
- Context formatting
- Conversation handling

## Configuration Options

| Setting | Default | Description |
|---------|---------|-------------|
| `CHUNK_SIZE` | 1000 | Document chunk size for embeddings |
| `CHUNK_OVERLAP` | 200 | Overlap between chunks |
| `LLM_PROVIDER` | openai | LLM provider (openai/ollama) |
| `EMBEDDING_MODEL` | text-embedding-ada-002 | Embedding model |
| `QDRANT_HOST` | localhost | Qdrant server host |
| `QDRANT_PORT` | 6333 | Qdrant server port |

## Troubleshooting

### Common Issues

**1. Qdrant Connection Error**
```bash
# Check if Qdrant is running
docker ps | grep qdrant
# Restart if needed
docker-compose restart qdrant
```

**2. OpenAI API Errors**
- Verify API key in `.env` file
- Check API quota and billing

**3. Document Processing Fails**
- Ensure documents are valid PDF/JSON files
- Check file permissions in documents folder

**4. S3 Sync Issues**
- Verify AWS credentials and permissions
- Check S3 bucket name and region

### Docker Services

```bash
# View service logs
docker-compose logs [service_name]

# Restart services
docker-compose restart

# Reset everything
docker-compose down -v
docker-compose up -d
```

## Performance Optimization

- **Batch Processing**: Process multiple documents simultaneously
- **Embedding Caching**: Reuse embeddings for unchanged documents
- **Query Optimization**: Adjust search parameters for relevance vs speed
- **Memory Management**: Monitor vector database size and optimize chunk sizes

## Security Considerations

- Store API keys securely in `.env` file
- Use IAM roles for S3 access in production
- Enable authentication for n8n and Langfuse in production
- Validate uploaded documents for malicious content

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

## License

This project is licensed under the MIT License.