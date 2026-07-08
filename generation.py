from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_ollama import OllamaEmbeddings, ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_core.documents import Document
import json
import os
import ollama
EMBEDDING_MODEL = 'hf.co/CompendiumLabs/bge-base-en-v1.5-gguf'
LANGUAGE_MODEL = 'hf.co/bartowski/Llama-3.2-1B-Instruct-GGUF'
CHROMA_DB_PATH = "./chroma_db"
def answer_question(pdf_path, query):
    """Complete RAG pipeline"""
    # Setup vectorstore
    vectorstore = setup_vectorstore(pdf_path)

    # Retrieve with multi-query
    docs = retrieve_with_multi_query(query, vectorstore)

    # Build context
    context = "\n\n".join([doc.page_content for doc in docs])

    # Generate answer
    prompt = f"""You are a helpful chatbot. Use the following context to answer the user's question.
    If the context does not contain the answer, say "I don't know".

    Context:
    {context}

    Question: {query}

    Answer:"""

    stream = ollama.chat(
        model=LANGUAGE_MODEL,
        messages=[{'role': 'user', 'content': prompt}],
        stream=True
    )

    print("\nAnswer:")
    for response in stream:
        print(response['message']['content'], end='', flush=True)
    print()


# Usage
if __name__ == "__main__":
    pdf_path = "your_document.pdf"
    query = input("Ask a question: ")
    answer_question(pdf_path, query)