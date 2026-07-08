from langchain_community.document_loaders import DirectoryLoader, PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_ollama import OllamaEmbeddings

def ingest(file_name:str):
    loader = DirectoryLoader('data',glob="*.pdf",loader_cls=PyPDFLoader)
    docs=loader.load()
    print(len(docs))
    print(docs[0].metadata)
    print(docs[0].page_content[:300])
    text_splitter=RecursiveCharacterTextSplitter(chunk_size=1000,chunk_overlap=100)
    splits = text_splitter.split_documents(docs)
    vectordb=Chroma.from_documents(documents=splits,embedding=OllamaEmbeddings(model='hf.co/CompendiumLabs/bge-base-en-v1.5-gguf'),  persist_directory="./chroma_db")
    vectordb.persist()
