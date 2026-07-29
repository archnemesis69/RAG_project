import os
import ollama

from ingest import ingest
from multi_query import retrieve

from langchain_community.chat_models import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough


class RAGService:
    def __init__(self):
        self.chroma_db_path = os.environ.get("CHROMA_DB_PATH", "/app/chroma_db")
        self.data_dir = os.environ.get("DATA_DIR", "/app/data")
        self.ollama_host = os.environ.get("OLLAMA_HOST", "http://localhost:11434")

        self.language_model = "hf.co/bartowski/Llama-3.2-1B-Instruct-GGUF"

        self.llm = ChatOllama(model=self.language_model, base_url=self.ollama_host)

        self.prompt = ChatPromptTemplate.from_template("""
You are a helpful AI assistant.

Use ONLY the following context to answer the user's question.

If the context does not contain enough information, say:
"I don't have enough information to answer this question."

Context:
{context}

Question:
{question}

Answer:
""")

    def format_docs(self, docs):
        return "\n\n".join(doc.page_content for doc in docs)

    def retrieve_context(self, query, top_k=5, owner_id="default"):

        if not os.path.exists(self.chroma_db_path):
            raise FileNotFoundError(
                f"Vector database not found at {self.chroma_db_path}. "
                "Please ingest documents first."
            )

        # FIX: owner_id now passed through so retrieval only ever
        # searches this owner's own documents.
        docs = retrieve(query, top_k=top_k, owner_id=owner_id)

        context = self.format_docs(docs)

        return docs, context

    def generate_answer(self, query, context):

        rag_chain = (
            {
                "context": lambda _: context,
                "question": RunnablePassthrough(),
            }
            | self.prompt
            | self.llm
            | StrOutputParser()
        )

        return rag_chain.invoke(query)

    def stream_answer(self, query, context):

        prompt = self.prompt.format(
            context=context,
            question=query,
        )

        stream = ollama.chat(
            model=self.language_model,
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            stream=True,
        )

        full_response = ""

        for response in stream:
            chunk = response["message"]["content"]
            print(chunk, end="", flush=True)
            full_response += chunk

        print()

        return full_response

    def answer(
        self,
        query,
        top_k=5,
        stream=False,
        ingest_first=False,
        owner_id="default",
    ):

        if ingest_first:
            print("Ingesting documents...")
            ingest(self.data_dir, owner_id=owner_id)
            print("Documents ingested.\n")

        docs, context = self.retrieve_context(
            query=query,
            top_k=top_k,
            owner_id=owner_id,
        )

        if stream:
            answer = self.stream_answer(query, context)
        else:
            answer = self.generate_answer(query, context)

        return {
            "answer": answer,
            "documents": docs,
        }
