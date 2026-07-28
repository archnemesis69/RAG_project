from langchain_community.document_loaders import PyPDFLoader
# FIX: module is singular `langchain.text_splitter`, not
# `langchain.text_splitters` (plural). The plural form doesn't exist in
# this package and raised ModuleNotFoundError on import. Matches the
# import already used correctly in ingest.py.
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import OllamaEmbeddings
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.load import dumps, loads
import ollama  # FIX: was used below but never imported -> NameError

EMBEDDING_MODEL = 'hf.co/CompendiumLabs/bge-base-en-v1.5-gguf'
LANGUAGE_MODEL = 'hf.co/bartowski/Llama-3.2-1B-Instruct-GGUF'


def setup_vectorstore(pdf_path: str):

    loader = PyPDFLoader(pdf_path)
    docs = loader.load()

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    splits = text_splitter.split_documents(docs)

    vectorstore = Chroma.from_documents(
        documents=splits,
        embedding=OllamaEmbeddings(model=EMBEDDING_MODEL),
    )
    return vectorstore


def _get_unique_union(documents):
    flattened_docs = [dumps(doc) for sublist in documents for doc in sublist]
    unique_docs = list(set(flattened_docs))
    return [loads(doc) for doc in unique_docs]


def retrieve_with_multi_query(query: str, vectorstore, top_k: int = 5):
    """
    FIX: this function was called but never defined. Generates 5
    rephrasings of the query and retrieves+dedupes across all of them,
    same pattern as multi_query.py.
    """
    from langchain_community.chat_models import ChatOllama

    template = """You are an AI language model assistant.
Your task is to generate five different versions of the given user question
to retrieve relevant documents from a vector database.
Provide ONLY the questions, each on a new line.

Original question:
{question}
"""
    prompt = ChatPromptTemplate.from_template(template)
    llm = ChatOllama(model=LANGUAGE_MODEL)

    generate_queries = (
            prompt
            | llm
            | StrOutputParser()
            | (lambda x: [q.strip() for q in x.split("\n") if q.strip()])
    )
    queries = generate_queries.invoke({"question": query})

    retriever = vectorstore.as_retriever(search_kwargs={"k": top_k})
    all_docs = [retriever.invoke(q) for q in queries]

    return _get_unique_union(all_docs)


def answer_question(pdf_path, query):
    """Complete RAG pipeline for a single PDF file"""
    vectorstore = setup_vectorstore(pdf_path)
    docs = retrieve_with_multi_query(query, vectorstore)

    context = "\n\n".join([doc.page_content for doc in docs])

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


if __name__ == "__main__":
    pdf_path = "your_document.pdf"
    query = input("Ask a question: ")
    answer_question(pdf_path, query)
