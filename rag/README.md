# 📚 RAG (Retrieval-Augmented Generation) Application

A Python-based Retrieval-Augmented Generation system that ingests PDF documents, retrieves relevant information using multi-query strategies, and generates accurate answers using Ollama's large language models.

## ✨ Features

- 📄 **PDF Ingestion** - Automatically loads and processes PDF documents from the `data/` directory
- 🔍 **Multi-Query Retrieval** - Generates multiple query variations to improve document relevance
- 🤖 **LLM Integration** - Uses Ollama with Llama 3.2 for generating contextual answers
- 💾 **Vector Database** - Stores embeddings in ChromaDB for efficient, scalable retrieval
- 🔄 **Interactive Q&A** - Ask questions and get RAG-powered answers in real-time

## 📋 Prerequisites

- **Python 3.8+**
- **[Ollama](https://ollama.ai)** installed and running with required models
- **Disk space** for ChromaDB vector storage and models (~2-5GB depending on documents)

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Setup Ollama
```bash
# Install Ollama from https://ollama.ai, then:
ollama serve  # Start in one terminal

# In another terminal, pull required models:
ollama pull llama3
ollama pull hf.co/bartowski/Llama-3.2-1B-Instruct-GGUF
```

### 3. Add PDF Documents
```bash
mkdir -p ../data
# Copy your PDF files to the data/ directory
```

### 4. Run the Application
```bash
python app.py
```

## 💻 Usage

### Interactive Mode
```bash
python app.py
```

Then simply ask questions at the prompt:
```
Ask a question (or 'quit' to exit): What is machine learning?
```

### Example Output

```
==============================================================
RAG (Retrieval-Augmented Generation) Application
==============================================================

Vector database initialized. Ready to answer questions!

Ask a question (or 'quit' to exit): What is machine learning?

Retrieving relevant documents...
Retrieved 5 documents

Generating answer...

==============================================================
Answer:
Machine learning is a subset of artificial intelligence that 
enables systems to learn and improve from experience without 
being explicitly programmed. It works by identifying patterns 
in data and using those patterns to make predictions or 
decisions on new data...
==============================================================
```

### Programmatic Usage

```python
from app import RAGService

# Initialize the RAG service
rag = RAGService()

# Ask a question
response = rag.answer(query="What is machine learning?", top_k=5)
print(response)
```

## 📁 Project Structure

```
RAG_project/
├── rag/
│   ├── app.py                 # Main application & RAGService class
│   ├── ingest.py             # PDF ingestion and vector DB creation
│   ├── multi_query.py        # Multi-query retrieval strategy
│   ├── generation.py         # Answer generation utilities
│   └── README.md             # This file
├── data/                      # Place your PDF files here
├── chroma_db/                 # Vector database (auto-created)
├── requirements.txt           # Python dependencies
└── .gitignore
```

## 🔧 Component Details

### `app.py`
- **RAGService class** - Main orchestrator for the RAG pipeline
- Initializes LLM and prompt templates
- Handles document retrieval and answer generation
- Provides both CLI and programmatic interfaces

### `ingest.py`
- Loads PDF files from the `data/` directory
- Splits documents into manageable chunks (1000 tokens, 100 overlap)
- Creates embeddings and stores in ChromaDB
- Handles document persistence for reuse

### `multi_query.py`
- Generates 5 alternative query variations using LLM
- Retrieves relevant documents for each query variant
- Removes duplicate results across queries
- Returns top-k unique, most-relevant documents

## 🤖 Models Used

- **Language Model**: `hf.co/bartowski/Llama-3.2-1B-Instruct-GGUF` (1B parameters, optimized for speed)
- **Query Generation**: `llama3` (for multi-query alternatives)

## ⚙️ Configuration

Key configuration variables can be customized in their respective files:

| Variable | File | Default | Purpose |
|----------|------|---------|---------|
| `CHROMA_DB_PATH` | `app.py` | `../chroma_db` | Vector database location |
| `chunk_size` | `ingest.py` | `1000` | Document chunk size (tokens) |
| `chunk_overlap` | `ingest.py` | `100` | Overlap between chunks |
| `top_k` | `multi_query.py` | `5` | Number of documents to retrieve |
| `language_model` | `app.py` | Llama-3.2-1B | LLM model name/path |

## 🐛 Troubleshooting

### "Ollama connection refused"
```bash
# Make sure Ollama is running:
ollama serve

# Verify Ollama is accessible:
curl http://localhost:11434
```

### "Vector database not found"
- Ensure PDF files exist in `data/`
- The database is auto-created on first run
- Check file permissions and disk space

### "No documents retrieved"
- Verify PDFs are properly formatted and readable
- Check PDF quality (OCR-scanned PDFs work best)
- Ensure documents are in the `data/` directory
- Try with `top_k=10` for more results

### "Out of memory errors"
- Reduce `chunk_size` in `ingest.py` (try 500)
- Use a smaller language model
- Process fewer PDF files at once
- Increase available system RAM/swap

### Model Download Issues
```bash
# If a model fails to download automatically:
ollama pull llama3
ollama pull hf.co/bartowski/Llama-3.2-1B-Instruct-GGUF

# Verify installed models:
ollama list
```

## 📊 Performance Tips

- **Faster queries**: Use smaller chunk sizes and fewer retrieval documents
- **Better answers**: Use larger chunk overlap (50-200) for more context
- **Reduced memory**: Batch process large PDF directories
- **Improved relevance**: Use domain-specific PDFs rather than general content

## 🚀 Future Enhancements

- [ ] Support for more document formats (DOCX, TXT, etc.)
- [ ] Query result caching for repeated questions
- [ ] Multi-language support
- [ ] Conversation history tracking
- [ ] Source/citation tracking in generated answers
- [ ] Web UI interface
- [ ] REST API endpoints

## 📝 License

MIT
