import os
from ingest import ingest
from multi_query import retrieve
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
import ollama

LANGUAGE_MODEL = 'hf.co/bartowski/Llama-3.2-1B-Instruct-GGUF'
CHROMA_DB_PATH = "./chroma_db"


def format_docs(docs):
    """Format retrieved documents into context string"""
    return "\n\n".join(doc.page_content for doc in docs)


def rag_pipeline(query, ingest_first=False, top_k=5):
    """
    Complete RAG pipeline:
    1. Ingest PDFs (optional)
    2. Retrieve relevant documents using multi-query
    3. Generate answer using LLM

    Args:
        query: The user's question
        ingest_first: Whether to ingest documents before retrieval
        top_k: Number of documents to retrieve per query (passed to multi_query)
    """

    # Step 1: Ingest documents if requested
    if ingest_first:
        print("Ingesting documents...")
        ingest("data")
        print("Documents ingested successfully!\n")

    # Step 2: Retrieve documents using multi-query
    print(f"Retrieving relevant documents for: '{query}'\n")

    # Check if vector database exists before retrieving
    if not os.path.exists(CHROMA_DB_PATH):
        raise FileNotFoundError(
            f"Vector database not found at {CHROMA_DB_PATH}. "
            "Please run with ingest_first=True or ingest documents first."
        )

    # Call retrieve with top_k parameter
    docs = retrieve(query, top_k=top_k)
    print(f"Retrieved {len(docs)} unique documents\n")

    # Step 3: Format context
    context = format_docs(docs)

    # Step 4: Generate answer using LLM
    prompt_template = """You are a helpful AI assistant. Use the following context to answer the user's question.
If the context does not contain enough information to answer the question, say "I don't have enough information to answer this question."

Context:
{context}

Question: {question}

Answer:"""

    prompt = ChatPromptTemplate.from_template(prompt_template)
    llm = ChatOllama(model=LANGUAGE_MODEL)

    rag_chain = (
            {"context": lambda x: context, "question": RunnablePassthrough()}
            | prompt
            | llm
            | StrOutputParser()
    )

    print("Generating answer...\n")
    answer = rag_chain.invoke(query)

    return answer


def rag_pipeline_with_streaming(query, ingest_first=False, top_k=5):
    """
    Alternative RAG pipeline with streaming output for better UX.
    """

    # Step 1: Ingest documents if requested
    if ingest_first:
        print("Ingesting documents...")
        ingest("data")
        print("Documents ingested successfully!\n")

    # Step 2: Retrieve documents using multi-query
    print(f"Retrieving relevant documents for: '{query}'\n")

    if not os.path.exists(CHROMA_DB_PATH):
        raise FileNotFoundError(
            f"Vector database not found at {CHROMA_DB_PATH}. "
            "Please run with ingest_first=True or ingest documents first."
        )

    docs = retrieve(query, top_k=top_k)
    print(f"Retrieved {len(docs)} unique documents\n")

    # Step 3: Format context
    context = format_docs(docs)

    # Step 4: Generate answer with streaming
    prompt_template = """You are a helpful AI assistant. Use the following context to answer the user's question.
If the context does not contain enough information to answer the question, say "I don't have enough information to answer this question."

Context:
{context}

Question: {question}

Answer:"""

    prompt = prompt_template.format(context=context, question=query)

    print("Generating answer...\n")

    # Stream the response
    stream = ollama.chat(
        model=LANGUAGE_MODEL,
        messages=[{'role': 'user', 'content': prompt}],
        stream=True
    )

    full_response = ""
    for response in stream:
        chunk = response['message']['content']
        print(chunk, end='', flush=True)
        full_response += chunk

    print("\n")
    return full_response


def main():
    """Main application entry point"""
    print("=" * 60)
    print("RAG (Retrieval-Augmented Generation) Application")
    print("=" * 60)

    # Check if vector database exists
    if not os.path.exists(CHROMA_DB_PATH):
        print("\nVector database not found. Ingesting documents first...")
        ingest_first = True
    else:
        print("\nVector database found. Starting RAG pipeline...\n")
        ingest_first = False

    # Main loop for asking questions
    while True:
        query = input("\nAsk a question (or 'quit' to exit): ").strip()

        if query.lower() in ['quit', 'exit', 'q']:
            print("Goodbye!")
            break

        if not query:
            print("Please enter a valid question.\n")
            continue

        try:
            # Option 1: Use the streaming version for better UX
            answer = rag_pipeline_with_streaming(query, ingest_first=ingest_first)

            # Option 2: Use the non-streaming version (commented out)
            # answer = rag_pipeline(query, ingest_first=ingest_first)
            # print("\n" + "=" * 60)
            # print(f"Answer:\n{answer}")
            # print("=" * 60 + "\n")

            ingest_first = False

        except FileNotFoundError as e:
            print(f"\nError: {e}")
            print("Please run with ingest_first=True or place documents in the 'data' directory.\n")
            ingest_first = True

        except Exception as e:
            print(f"\nError: {e}")
            print("Please make sure Ollama is running and the documents are ingested.\n")


if __name__ == "__main__":
    main()