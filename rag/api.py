import os
import shutil
from typing import Dict, List

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from pydantic import BaseModel

from app import RAGService
from ingest import delete_document, ingest, ingest_file, list_documents

app = FastAPI()

rag_service = RAGService()

DATA_DIR = "../data"


class QueryRequest(BaseModel):
    question: str
    top_k: int = 5
    # FIX: every endpoint now threads an owner_id through to the
    # ingestion/retrieval layer so one user's questions can only ever
    # surface their own documents. Defaults to "default" so this still
    # works standalone/in tests without a real caller; the Spring Boot
    # backend always sends the authenticated user's id.
    owner_id: str = "default"


class QueryResponse(BaseModel):
    answer: str
    sources: List[Dict]


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/query", response_model=QueryResponse)
def query(request: QueryRequest):
    try:
        result = rag_service.answer(
            request.question,
            top_k=request.top_k,
            owner_id=request.owner_id,
        )
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
def ingest_endpoint(owner_id: str = "default"):
    """Bulk ingest every supported file in this owner's data folder."""
    try:
        owner_dir = os.path.join(DATA_DIR, owner_id)
        results = ingest(owner_dir, owner_id=owner_id)
        return {"status": "ok", "results": results}
    except FileNotFoundError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/documents")
def get_documents(owner_id: str = "default"):
    """List documents indexed for this owner only."""
    return {"documents": list_documents(owner_id=owner_id)}


@app.post("/documents")
async def upload_document(file: UploadFile = File(...), owner_id: str = Form("default")):
    """
    Upload a single PDF/DOCX/TXT file and ingest it immediately, scoped
    to owner_id.

    FIX: files used to all land in one shared ../data/ folder keyed
    only by filename, so two different users uploading "report.pdf"
    would overwrite each other's file on disk. Storage is now
    namespaced per owner (../data/{owner_id}/...), matching the
    per-owner isolation already applied in ingest.py/multi_query.py.
    """
    try:
        owner_dir = os.path.join(DATA_DIR, owner_id)
        os.makedirs(owner_dir, exist_ok=True)
        dest_path = os.path.join(owner_dir, file.filename)

        with open(dest_path, "wb") as out_file:
            shutil.copyfileobj(file.file, out_file)

        return ingest_file(dest_path, owner_id=owner_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/documents/{filename}")
def remove_document(filename: str, owner_id: str = "default"):
    """Delete a document, scoped to owner_id - never deletes another owner's copy."""
    try:
        return delete_document(filename, owner_id=owner_id)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
