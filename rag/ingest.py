import hashlib
import json
import os
from pathlib import Path

from langchain_community.document_loaders import (
    Docx2txtLoader,
    PyPDFLoader,
    TextLoader,
)
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_ollama import OllamaEmbeddings

EMBEDDING_MODEL = 'hf.co/CompendiumLabs/bge-base-en-v1.5-gguf'
CHROMA_DB_PATH = "../chroma_db"

# NEW: tracks which files have been ingested (filename -> content hash +
# chunk count) so re-running ingest() never duplicates work or data.
MANIFEST_PATH = os.path.join(CHROMA_DB_PATH, "manifest.json")

# NEW: per the cahier des charges (section 1.3 / 2.1), the system must
# accept PDF, DOCX, and TXT — the old version only globbed "*.pdf".
SUPPORTED_LOADERS = {
    ".pdf": PyPDFLoader,
    ".docx": Docx2txtLoader,
    ".txt": lambda path: TextLoader(path, autodetect_encoding=True),
}


def _get_vectorstore() -> Chroma:
    """Open (or create) the persisted Chroma store for read/write."""
    return Chroma(
        persist_directory=CHROMA_DB_PATH,
        embedding_function=OllamaEmbeddings(model=EMBEDDING_MODEL),
    )


def _load_manifest() -> dict:
    if not os.path.exists(MANIFEST_PATH):
        return {}
    with open(MANIFEST_PATH, "r") as f:
        return json.load(f)


def _save_manifest(manifest: dict) -> None:
    os.makedirs(CHROMA_DB_PATH, exist_ok=True)
    with open(MANIFEST_PATH, "w") as f:
        json.dump(manifest, f, indent=2)


def _file_hash(file_path: str) -> str:
    """SHA-256 of the file's bytes, used to detect changed content."""
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        for block in iter(lambda: f.read(8192), b""):
            h.update(block)
    return h.hexdigest()


def _load_document(file_path: str):
    ext = Path(file_path).suffix.lower()
    loader_factory = SUPPORTED_LOADERS.get(ext)
    if loader_factory is None:
        raise ValueError(
            f"Unsupported file type '{ext}' for '{file_path}'. "
            f"Supported types: {', '.join(SUPPORTED_LOADERS)}"
        )
    loader = loader_factory(file_path)
    return loader.load()


def ingest_file(file_path: str, force: bool = False) -> dict:
    """
    Ingest a single PDF/DOCX/TXT file into the vector store.

    - Skips the file if its content hash matches what's already in the
      manifest (i.e. it was already ingested and hasn't changed).
    - If the file *has* changed since last time, its old chunks are
      deleted first so re-ingesting never leaves duplicates behind.
    - Every chunk gets metadata["source"] = filename, which is what
      list_documents()/delete_document() and the /query citations key
      off of.
    """
    filename = os.path.basename(file_path)
    file_hash = _file_hash(file_path)

    manifest = _load_manifest()
    previous = manifest.get(filename)

    if previous and previous["hash"] == file_hash and not force:
        print(f"Skipping '{filename}' — already ingested and unchanged")
        return {"filename": filename, "status": "skipped", "chunks": previous["chunks"]}

    docs = _load_document(file_path)
    for doc in docs:
        doc.metadata["source"] = filename

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    splits = text_splitter.split_documents(docs)

    vectorstore = _get_vectorstore()

    if previous:
        # Same filename ingested before with different content -> clear
        # its old chunks before adding the new ones.
        vectorstore.delete(where={"source": filename})

    vectorstore.add_documents(splits)

    manifest[filename] = {"hash": file_hash, "chunks": len(splits)}
    _save_manifest(manifest)

    print(f"Ingested '{filename}': {len(splits)} chunk(s)")
    return {"filename": filename, "status": "ingested", "chunks": len(splits)}


def ingest(folder_path: str = "data") -> list:
    """
    Ingest every supported file (PDF, DOCX, TXT) found directly inside
    folder_path. Already-ingested, unchanged files are skipped.
    """
    if not os.path.isdir(folder_path):
        raise FileNotFoundError(f"Folder not found: '{folder_path}'")

    files = [
        os.path.join(folder_path, f)
        for f in sorted(os.listdir(folder_path))
        if Path(f).suffix.lower() in SUPPORTED_LOADERS
    ]

    if not files:
        raise FileNotFoundError(
            f"No supported files (PDF, DOCX, TXT) found in '{folder_path}'."
        )

    results = [ingest_file(f) for f in files]

    ingested = sum(1 for r in results if r["status"] == "ingested")
    skipped = sum(1 for r in results if r["status"] == "skipped")
    print(f"Done: {ingested} ingested, {skipped} skipped (unchanged)")

    return results


def list_documents() -> list:
    """Filenames currently in the index, with their chunk counts."""
    manifest = _load_manifest()
    return [
        {"filename": name, "chunks": info["chunks"]}
        for name, info in sorted(manifest.items())
    ]


def delete_document(filename: str) -> dict:
    """Remove all chunks belonging to `filename` from the vector store."""
    manifest = _load_manifest()
    if filename not in manifest:
        raise FileNotFoundError(f"'{filename}' was not found in the index.")

    vectorstore = _get_vectorstore()
    vectorstore.delete(where={"source": filename})

    del manifest[filename]
    _save_manifest(manifest)

    print(f"Deleted '{filename}' from the index")
    return {"filename": filename, "status": "deleted"}


if __name__ == "__main__":
    ingest("../data")
