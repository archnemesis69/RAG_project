from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.load import dumps, loads

from langchain_ollama import ChatOllama, OllamaEmbeddings
from langchain_community.vectorstores import Chroma

LANGUAGE_MODEL = 'hf.co/bartowski/Llama-3.2-1B-Instruct-GGUF'
EMBEDDING_MODEL = 'hf.co/CompendiumLabs/bge-base-en-v1.5-gguf'
CHROMA_DB_PATH = "../chroma_db"


def get_unique_union(documents):

    flattened_docs = [
        dumps(doc)
        for sublist in documents
        for doc in sublist
    ]
    unique_docs = list(set(flattened_docs))
    return [loads(doc) for doc in unique_docs]


def retrieve(query, top_k: int = 5):
    """
    Multi-query retrieval: generate 5 rephrasings of `query`, retrieve
    top_k docs for each, and return the deduplicated union.

    FIX: top_k parameter added — app.py already called retrieve(query,
    top_k=top_k), which crashed with TypeError since this function
    previously only accepted `query`.
    """
    template = """
You are an AI language model assistant.

Your task is to generate five different versions of the given user question
to retrieve relevant documents from a vector database.

Provide ONLY the questions, each on a new line.

Original question:
{question}
"""
    prompt = ChatPromptTemplate.from_template(template)

    # FIX: use the shared LANGUAGE_MODEL constant instead of a hardcoded,
    # possibly-not-installed "llama3" model.
    llm = ChatOllama(model=LANGUAGE_MODEL)

    generate_queries = (
            prompt
            | llm
            | StrOutputParser()
            | (lambda x: [q.strip() for q in x.split("\n") if q.strip()])
    )

    queries = generate_queries.invoke({"question": query})

    print("Generated Queries:")
    for q in queries:
        print("-", q)

    embeddings = OllamaEmbeddings(model=EMBEDDING_MODEL)

    vectorstore = Chroma(
        persist_directory=CHROMA_DB_PATH,
        embedding_function=embeddings,
    )

    retriever = vectorstore.as_retriever(search_kwargs={"k": top_k})

    all_docs = [retriever.invoke(q) for q in queries]

    return get_unique_union(all_docs)