from langchain_community.document_loaders import DirectoryLoader, PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_ollama import OllamaEmbeddings

EMBEDDING_MODEL = 'hf.co/CompendiumLabs/bge-base-en-v1.5-gguf'
CHROMA_DB_PATH = "./chroma_db"


def ingest(folder_path: str = "data"):

    loader = DirectoryLoader(folder_path, glob="*.pdf", loader_cls=PyPDFLoader)
    docs = loader.load()

    if not docs:
        raise FileNotFoundError(
            f"No PDFs found in '{folder_path}'. Add .pdf files there before ingesting."
        )

    print(f"Loaded {len(docs)} page(s) from '{folder_path}'")
    print("First doc metadata:", docs[0].metadata)
    print("First doc preview:", docs[0].page_content[:300])

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    splits = text_splitter.split_documents(docs)
    print(f"Split into {len(splits)} chunks")


    Chroma.from_documents(
        documents=splits,
        embedding=OllamaEmbeddings(model=EMBEDDING_MODEL),
        persist_directory=CHROMA_DB_PATH,
    )
    print(f"Vectorstore persisted to {CHROMA_DB_PATH}")


if __name__ == "__main__":
    ingest("data")
