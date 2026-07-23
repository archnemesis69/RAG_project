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
from langchain_community.embeddings import OllamaEmbeddings

EMBEDDING_MODEL = 'hf.co/CompendiumLabs/bge-base-en-v1.5-gguf'
CHROMA_DB_PATH = "../chroma_db"

# manifest.json is now a nested dict: { owner_id: { filename: {hash, chunks} } }
# instead of a flat { filename: {...} }. A flat manifest meant two
# different users uploading a file with the same name collided in the
# same slot -> whichever uploaded second would either get skipped as
# "unchanged" (if hashes happened to match) or silently delete/replace
# the other user's chunks. Nesting by owner_id makes filenames unique
# only *within* a user's own documents, which is what "ses documents"
# (section 2.1) actually implies.
MANIFEST_PATH = os.path.join(CHROMA_DB_PATH, "manifest.json")

SUPPORTED_LOADERS = {
    ".pdf": PyPDFLoader,
    ".docx": Docx2txtLoader,
    ".txt": lambda path: TextLoader(path, autodetect_encoding=True),
}


def _get_vectorstore() -> Chroma:
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
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        for block in iter(lambda: f.read(8192), b""):
            h.update(block)
    return h.hexdigest()


def _owner_filter(filename: str, owner_id: str) -> dict:
    """
    Chroma 'where' filter scoping a query/delete to one owner's copy of
    one filename. Using $and explicitly rather than a flat two-key dict,
    since some Chroma versions require it for multi-condition filters.
    """
    return {"$and": [{"source": filename}, {"owner_id": owner_id}]}


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


def ingest_file(file_path: str, owner_id: str = "default", force: bool = False) -> dict:
    """
    Ingest a single PDF/DOCX/TXT file into the vector store, scoped to
    owner_id. Every chunk gets metadata:
      - source: the filename (used for citations and per-owner delete)
      - owner_id: whose document this is (used to filter retrieval)

    Skips re-ingesting if this owner already ingested this exact
    filename with unchanged content. If the content changed, the
    owner's old chunks for that filename are deleted first.
    """
    filename = os.path.basename(file_path)
    file_hash = _file_hash(file_path)

    manifest = _load_manifest()
    owner_entries = manifest.get(owner_id, {})
    previous = owner_entries.get(filename)

    if previous and previous["hash"] == file_hash and not force:
        print(f"Skipping '{filename}' for owner '{owner_id}' — already ingested and unchanged")
        return {"filename": filename, "status": "skipped", "chunks": previous["chunks"]}

    docs = _load_document(file_path)
    for doc in docs:
        doc.metadata["source"] = filename
        doc.metadata["owner_id"] = owner_id

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    splits = text_splitter.split_documents(docs)

    vectorstore = _get_vectorstore()

    if previous:
        vectorstore.delete(where=_owner_filter(filename, owner_id))

    vectorstore.add_documents(splits)

    owner_entries[filename] = {"hash": file_hash, "chunks": len(splits)}
    manifest[owner_id] = owner_entries
    _save_manifest(manifest)

    print(f"Ingested '{filename}' for owner '{owner_id}': {len(splits)} chunk(s)")
    return {"filename": filename, "status": "ingested", "chunks": len(splits)}


def ingest(folder_path: str = "data", owner_id: str = "default") -> list:
    """Ingest every supported file directly inside folder_path, scoped to owner_id."""
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

    results = [ingest_file(f, owner_id=owner_id) for f in files]

    ingested = sum(1 for r in results if r["status"] == "ingested")
    skipped = sum(1 for r in results if r["status"] == "skipped")
    print(f"Done: {ingested} ingested, {skipped} skipped (unchanged)")

    return results


def list_documents(owner_id: str = "default") -> list:
    """Filenames this owner has indexed, with chunk counts."""
    manifest = _load_manifest()
    owner_entries = manifest.get(owner_id, {})
    return [
        {"filename": name, "chunks": info["chunks"]}
        for name, info in sorted(owner_entries.items())
    ]


def delete_document(filename: str, owner_id: str = "default") -> dict:
    """Remove one owner's chunks for `filename`. Never touches another owner's copy."""
    manifest = _load_manifest()
    owner_entries = manifest.get(owner_id, {})

    if filename not in owner_entries:
        raise FileNotFoundError(f"'{filename}' was not found in the index for this owner.")

    vectorstore = _get_vectorstore()
    vectorstore.delete(where=_owner_filter(filename, owner_id))

    del owner_entries[filename]
    manifest[owner_id] = owner_entries
    _save_manifest(manifest)

    print(f"Deleted '{filename}' for owner '{owner_id}'")
    return {"filename": filename, "status": "deleted"}


if __name__ == "__main__":
    ingest("../data")
