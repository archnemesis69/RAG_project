# Marginal RAG Assistant

A 3-tier Retrieval-Augmented Generation (RAG) application that allows users to upload documents (PDF, DOCX, TXT) and seamlessly chat with them using local LLMs.

## 🌟 Features
- **Premium UI**: A highly responsive, modern dark-mode React interface with glassmorphism effects and smooth animations.
- **Secure & Multi-tenant**: Spring Boot backend handles JWT authentication, ensuring users can only access and query their own documents.
- **Local AI Engine**: FastAPI Python backend using LangChain, ChromaDB, and Ollama for completely private, local embeddings and inference.
- **Robust Error Handling**: Real-time upload status tracking and detailed error reporting.

## 🏗️ Architecture
- **Frontend**: React, Vite, TypeScript, Vanilla CSS
- **Backend (API Gateway)**: Java 21, Spring Boot, Spring Security, PostgreSQL
- **AI Service (Inference & Ingestion)**: Python 3.11, FastAPI, LangChain, ChromaDB
- **LLM Provider**: Ollama (must be installed on the host machine)

## 📋 Prerequisites
1. **Docker & Docker Compose**
2. **Ollama**: Must be running locally on your host machine.

> [!WARNING]
> **Linux Users**: Ollama binds to `127.0.0.1` by default, which Docker containers cannot reach. You **must** configure Ollama to listen on all interfaces so the FastAPI container can connect to it. Start Ollama with:
> `OLLAMA_HOST=0.0.0.0 ollama serve`

## 🚀 Quick Start

1. **Start Ollama** on your host machine (ensuring it's accessible to Docker):
   ```bash
   OLLAMA_HOST=0.0.0.0 ollama serve
   ```

2. **Pull the required models** (run this in a new terminal):
   ```bash
   ollama pull llama3
   ollama pull nomic-embed-text
   ```
   *(Note: Adjust the model names if you have configured different defaults in your `api.py`)*

3. **Start the application stack**:
   ```bash
   docker compose up -d --build
   ```

4. **Access the Application**:
   Open your browser and navigate to `http://localhost:5173` (or your configured frontend port). Create an account, upload a document, and start chatting!

## 🔧 Development

### Frontend
```bash
cd frontend
npm install
npm run dev
```

### Spring Boot Backend
```bash
cd backend
mvn clean package
java -jar target/ragassistant-0.0.1-SNAPSHOT.jar
```

### FastAPI Service
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn rag.api:app --reload
```
