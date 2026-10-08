# RAG (Retrieval Augmented Generation) - Arrow Flow Diagrams

## What is RAG?
RAG = Retrieve relevant documents --> Feed them as context to an LLM --> Generate an accurate answer.
Instead of relying only on the LLM's training data, you fetch your own documents first.

## Text RAG Flow (Arrow Diagram)
```
USER QUESTION
     |
     v
[EMBEDDING MODEL]  (e.g., OpenAI text-embedding-3-small, sentence-transformers)
     |  converts question into a vector (list of floats)
     v
[VECTOR DATABASE SEARCH]  (e.g., Pinecone, Weaviate, ChromaDB, pgvector)
     |  finds top-K most similar document chunks
     v
[RETRIEVED CHUNKS]  (e.g., 5 relevant paragraphs)
     |
     v
[PROMPT ASSEMBLY]  system prompt + retrieved chunks + user question
     |
     v
[LLM]  (e.g., GPT-4, Claude, Gemini)
     |  reads the context and generates an answer
     v
[ANSWER TO USER]
```

## Image RAG Flow (Arrow Diagram)
```
USER UPLOADS IMAGE + ASKS QUESTION
     |
     v
[VISION ENCODER]  (e.g., CLIP ViT, BLIP-2, GPT-4V)
     |  converts image into embeddings or descriptions
     v
[IMAGE VECTOR SEARCH]  (search similar images in vector DB)
     |  also search related text documents
     v
[RETRIEVED CONTEXT]  (image descriptions + relevant text chunks)
     |
     v
[MULTIMODAL LLM]  (e.g., GPT-4V, Gemini Pro Vision, LLaVA)
     |  processes both image and text context
     v
[ANSWER TO USER]
```

## Hybrid RAG Flow (Text + Image together)
```
USER QUERY (can be text, image, or both)
     |
     +------------------+------------------+
     |                                     |
     v                                     v
[TEXT EMBEDDER]                    [IMAGE ENCODER]
     |                                     |
     v                                     v
[TEXT VECTOR SEARCH]               [IMAGE VECTOR SEARCH]
     |                                     |
     +------------------+------------------+
                        |
                        v
              [RERANKER]  (cross-encoder re-scores results)
                        |
                        v
              [CONTEXT ASSEMBLY]  top chunks from both
                        |
                        v
              [MULTIMODAL LLM]
                        |
                        v
              [FINAL ANSWER]
```

## Full RAG Pipeline (Ingestion + Query)

### INGESTION (Offline, done once)
```
DOCUMENTS (PDF, TXT, HTML, etc.)
     |
     v
[DOCUMENT LOADER]  (langchain, llama-index, custom)
     |
     v
[TEXT SPLITTER]  (chunk_size=500, chunk_overlap=50)
     |  splits into manageable chunks
     v
[EMBEDDING MODEL]  (converts each chunk to vector)
     |
     v
[VECTOR DATABASE]  (stores vectors + metadata)
```

### QUERY (Online, per user question)
```
USER QUESTION
     |
     v
[EMBEDDING MODEL]  (same model used in ingestion)
     |
     v
[VECTOR SEARCH]  (cosine similarity, top-K=5)
     |
     v
[OPTIONAL: RERANK]  (cross-encoder improves precision)
     |
     v
[PROMPT TEMPLATE]
  "Given the following context, answer the question.
   Context: {retrieved_chunks}
   Question: {user_question}"
     |
     v
[LLM GENERATION]
     |
     v
[ANSWER + SOURCES]
```

## Vector DB Comparison
```
ChromaDB    --> Local, easy, good for prototyping
pgvector    --> PostgreSQL extension, good if already using PG
Pinecone    --> Managed cloud, scales automatically
Weaviate    --> Open source, GraphQL API
Qdrant      --> Rust-based, fast, good filtering
Milvus      --> Enterprise scale, GPU acceleration
```

## Key Concepts
```
CHUNK     = A piece of a document (paragraph, section)
EMBEDDING = Vector representation of text/image (e.g., 1536 floats)
SIMILARITY = Cosine distance between vectors (0=identical, 1=unrelated)
TOP-K     = Number of chunks to retrieve (usually 3-10)
RERANKING = Second pass to improve result quality
HALLUCINATION = When LLM makes up facts --> RAG reduces this by giving real context
```

## Python Code Example (Text RAG)
```python
import chromadb
from sentence_transformers import SentenceTransformer

# 1. Setup
client = chromadb.Client()
collection = client.create_collection("docs")
model = SentenceTransformer("all-MiniLM-L6-v2")

# 2. Ingest documents
documents = ["Python is a language...", "FastAPI is a framework...", "Docker containers..."]
embeddings = model.encode(documents).tolist()
collection.add(documents=documents, embeddings=embeddings, ids=["1", "2", "3"])

# 3. Query
question = "What is FastAPI?"
question_embedding = model.encode(question).tolist()
results = collection.query(query_embeddings=[question_embedding], n_results=3)

# 4. Build prompt for LLM
context = "\n".join(results["documents"][0])
prompt = f"Context: {context}\n\nQuestion: {question}\nAnswer:"

# 5. Send to LLM (OpenAI, Gemini, etc.)
# response = openai.chat.completions.create(model="gpt-4", messages=[{"role": "user", "content": prompt}])
```
