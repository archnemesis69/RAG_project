import ollama
import numpy as np
EMBEDDING_MODEL = 'hf.co/CompendiumLabs/bge-base-en-v1.5-gguf'
LANGUAGE_MODEL = 'hf.co/bartowski/Llama-3.2-1B-Instruct-GGUF'
def load_data(path):
    data=[]
    with open(path,'r') as f:
        chunks = [line.strip() for line in f if line.strip()]
        print(f'loaded{len(data)}lines')
    return data
def add_chunks_database(chunk,vector_db):
    response=ollama.embed(model=EMBEDDING_MODEL,input=chunk)
    embedding=response.embeddings[0]
    vector_db.append((chunk,embedding))
def add_data_to_database(dataset,vector_db):
    for i,chunk in enumerate(dataset):
        add_chunks_database(chunk,vector_db)
        print(f'Added chunk {i+1}/{len(dataset)} to the database')
def cosine_similarity(v1,v2):
    return np.dot(v1,v2)/(np.linalg.norm(v1)*np.linalg.norm(v2))
def retrieve(query,vector_db,top_k=5):
    response=ollama.embed(model=EMBEDDING_MODEL,input=query)
    query_embedding=response.embeddings[0]
    similarity=[]
    for i,chunk in enumerate(vector_db):
        similarity.append((chunk, cosine_similarity(query_embedding,chunk[1])))
    similarity.sort(key=lambda x:x[1],reverse=True)
    return similarity[:top_k]
vector_db = []
data = load_data('/home/azizk/PycharmProjects/MLlearn/PythonProject/catfacts/cat-facts.txt')
add_data_to_database(data, vector_db)

# --- Query ---
input_query = input("Ask me a question: ")
retrieved_knowledge = retrieve(input_query, vector_db, top_k=5)

print("\nRetrieved knowledge:")
# --- Build the prompt with context ---
context = "\n".join([chunk.strip() for chunk, _ in retrieved_knowledge])
instruction_prompt = f"""You are a helpful chatbot. Use the following context to answer the user's question.
If the context does not contain the answer, say "I don't know".

Context:
{context}
"""

# --- Generate answer with streaming ---
stream = ollama.chat(
    model=LANGUAGE_MODEL,
    messages=[
        {'role': 'system', 'content': instruction_prompt},
        {'role': 'user', 'content': input_query}
    ],
    stream=True
)

print("\nChatbot response:")
for response in stream:
    # Each chunk is a dict; extract the text
    print(response['message']['content'], end='', flush=True)
