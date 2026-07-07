from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import Chroma
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import OllamaEmbeddings ,Ollamallm
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
import ollama

 text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000,chunk_overlap=100)
 splits=text_splitter.split_documents(text)
 vectorstore=Chroma.from_texts(stext=splits,embedding=OllamaEmbeddings(model='hf.co/CompendiumLabs/bge-base-en-v1.5-gguf'))
 retriever=vectorstore.as_retriever(search_kwargs={'k':5})
template = """Answer the question based only on the following context:
{context}
Qestion:{ChatPromptTemplate.from_template(template)}
"""
prompt=ChatPromptTemplate.from_template(template)
llm=OllamaLLM(model='hf.co/bartowski/Llama-3.2-1B-Instruct-GGUF')

def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)  # what attribute holds the text of a Document?

rag_chain = (
    {"context": retriever | format_docs,"question": RunnablePassthrough()}
    | prompt | llm  | strOutputParser()
)

rag_chain.invoke("How tall is Mount Everest?")
