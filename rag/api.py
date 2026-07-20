import os
import shutil
from typing import Dict, List

from fastapi import FastAPI, File, HTTPException, UploadFile
from pydantic import BaseModel

from app import RAGService
from ingest import delete_document, ingest, ingest_file, list_documents

app = FastAPI()

# Instantiate once at startup rather than per-request (loading the LLM /
# embeddings client on every call would be slow).
rag_service = RAGService()

DATA_DIR = "../data"


class QueryRequest(BaseModel):
    question: str
    top_k: int = 5


class QueryResponse(BaseModel):
    answer: str
    sources: List[Dict]


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/query", response_model=QueryResponse)
def query(request: QueryRequest):
    try:
        result = rag_service.answer(request.question, top_k=request.top_k)
        sources = [
            {"source": doc.metadata.get("source"), "page": doc.metadata.get("page")}
            for doc in result["documents"]
        ]
        return QueryResponse(answer=result["answer"], sources=sources)
    except FileNotFoundError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/ingest")
def ingest_endpoint():
    """Bulk ingest every supported file in the data/ folder."""
    try:
        results = ingest(DATA_DIR)
        return {"status": "ok", "results": results}
    except FileNotFoundError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/documents")
def get_documents():
    """List every document currently indexed, with its chunk count."""
    return {"documents": list_documents()}


@app.post("/documents")
async def upload_document(file: UploadFile = File(...)):
    """
    Upload a single PDF/DOCX/TXT file and ingest it immediately.
    Re-uploading a file with unchanged content is a no-op (skipped);
    re-uploading a file whose content changed replaces its old chunks.
    """
    try:
        os.makedirs(DATA_DIR, exist_ok=True)
        dest_path = os.path.join(DATA_DIR, file.filename)

        with open(dest_path, "wb") as out_file:
            shutil.copyfileobj(file.file, out_file)

        return ingest_file(dest_path)
    except ValueError as e:
        # Unsupported file extension
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/documents/{filename}")
def remove_document(filename: str):
    """Delete a document and its chunks from the index."""
    try:
        return delete_document(filename)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
