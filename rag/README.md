# RAG (Retrieval-Augmented Generation) Application

A Python-based Retrieval-Augmented Generation system that ingests PDF documents, retrieves relevant information using multi-query strategies, and generates accurate answers using Ollama's large language models.

## Features

- 📄 **PDF Ingestion** - Automatically loads and processes PDF documents from the `data/` directory
- 🔍 **Multi-Query Retrieval** - Generates multiple query variations to retrieve more relevant documents
- 🤖 **LLM Integration** - Uses Ollama with Llama 3.2 for generating contextual answers
- 💾 **Vector Database** - Stores embeddings in ChromaDB for efficient retrieval
- 🔄 **Interactive Q&A** - Ask questions and get RAG-powered answers in real-time

## Prerequisites

- Python 3.8+
- [Ollama](https://ollama.ai) installed and running
- PDF documents in the `data/` directory

## Installation

1. **Clone the repository** (if needed):
```bash
git clone <your-repo-url>
cd RAG_project
```

2. **Install dependencies**:
```bash
pip install -r requirements.txt
```

3. **Setup Ollama**:
   - Download and install Ollama from [ollama.ai](https://ollama.ai)
   - Start the Ollama service:
   ```bash
   ollama serve
   ```
   - Pull required models (in another terminal):
   ```bash
   ollama pull llama3
   ollama pull nomic-embed-text
   ```

4. **Add your PDF documents**:
   - Create a `data/` directory if it doesn't exist:
   ```bash
   mkdir data
   ```
   - Place your PDF files in the `data/` directory

## Usage

### Run the application:
```bash
python app.py
```

### Example workflow:

```
==============================================================
RAG (Retrieval-Augmented Generation) Application
==============================================================

Vector database not found. Ingesting documents first...
Ingesting documents...
Documents ingested successfully!

Ask a question (or 'quit' to exit): What is machine learning?
Retrieving relevant documents for: 'What is machine learning?'

Generated Queries:
- What is machine learning?
- Define machine learning
- Explain machine learning concepts
- ...

Retrieved 5 unique documents

Generating answer...

==============================================================
Answer:
Machine learning is a subset of artificial intelligence that enables 
systems to learn and improve from experience without being explicitly programmed...
==============================================================
```

## Project Structure

```
RAG_project/
├── app.py                 # Main application - interactive RAG pipeline
├── ingest.py             # PDF ingestion and vector DB creation
├── multi_query.py        # Multi-query retrieval strategy
├── generation.py         # Answer generation (legacy)
├── requirements.txt      # Python dependencies
├── README.md            # This file
├── data/                 # Place your PDF files here
└── chroma_db/            # Vector database (auto-created)
```

## Component Details

### `ingest.py`
- Loads PDFs from the `data/` directory
- Splits documents into chunks (1000 tokens, 100 overlap)
- Creates embeddings using BGE model
- Stores vectors in ChromaDB

### `multi_query.py`
- Generates 5 alternative query versions using Llama 3
- Retrieves documents for each query variant
- Removes duplicate documents
- Returns unique, relevant documents

### `app.py`
- Main entry point
- Orchestrates the RAG pipeline
- Handles user interactions
- Manages document ingestion on first run

## Models Used

- **Language Model**: `hf.co/bartowski/Llama-3.2-1B-Instruct-GGUF`
- **Embedding Model**: `hf.co/CompendiumLabs/bge-base-en-v1.5-gguf`
- **Query Generation**: `llama3`

## Configuration

Edit these variables in the respective files to customize:

- `CHROMA_DB_PATH` - Vector database location (default: `./chroma_db`)
- `chunk_size` - Document chunk size in tokens (default: 1000)
- `chunk_overlap` - Overlap between chunks (default: 100)
- `k` - Number of documents to retrieve (default: 5)

## Troubleshooting

### "Ollama connection refused"
- Make sure Ollama is running: `ollama serve`
- Check if Ollama is accessible at `http://localhost:11434`

### "No documents retrieved"
- Ensure PDF files are in the `data/` directory
- Run with `ingest_first=True` to reingest documents
- Check PDF quality and format

### Out of memory errors
- Reduce `chunk_size` in `ingest.py`
- Use a smaller language model
- Process fewer documents

## Future Enhancements

- [ ] Support for more document formats (DOCX, TXT, etc.)
- [ ] Caching for faster queries
- [ ] Multi-language support
- [ ] Conversation history tracking
- [ ] Citation and source tracking

## License

MIT
