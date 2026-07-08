from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.load import dumps, loads

from langchain_ollama import ChatOllama, OllamaEmbeddings
from langchain_community.vectorstores import Chroma


def get_unique_union(documents):
    """
    Remove duplicate documents while preserving the Document objects.
    """
    flattened_docs = [
        dumps(doc)
        for sublist in documents
        for doc in sublist
    ]

    unique_docs = list(set(flattened_docs))

    return [loads(doc) for doc in unique_docs]


def retrieve(query,top_k=5):
    # Prompt for generating multiple search queries
    template = """
You are an AI language model assistant.

Your task is to generate five different versions of the given user question
to retrieve relevant documents from a vector database.

Provide ONLY the questions, each on a new line.

Original question:
{question}
"""

    prompt = ChatPromptTemplate.from_template(template)

    # Local LLM
    llm = ChatOllama(
        model="hf.co/bartowski/Llama-3.2-1B-Instruct-GGUF"      # Change to your Ollama chat model
    )

    # Generate alternative queries
    generate_queries = (
        prompt
        | llm
        | StrOutputParser()
        | (lambda x: x.split("\n"))
    )

    queries = generate_queries.invoke({"question": query})

    print("Generated Queries:")
    for q in queries:
        print("-", q)

    # Load the existing Chroma database
    embeddings = OllamaEmbeddings(
        model='hf.co/CompendiumLabs/bge-base-en-v1.5-gguf'
        # or model="nomic-embed-text"
    )

    vectorstore = Chroma(
        persist_directory="./chroma_db",
        embedding_function=embeddings
    )

    retriever = vectorstore.as_retriever(
        search_kwargs={"k": top_k}
    )

    # Retrieve documents for every generated query
    all_docs = []

    for q in queries:
        docs = retriever.invoke(q)
        all_docs.append(docs)

    # Remove duplicates
    unique_docs = get_unique_union(all_docs)

    return unique_docs



