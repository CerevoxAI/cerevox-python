# Vector Database Integration Guide

Cerevox is engineered specifically for vector databases and RAG applications with intelligent chunking and structure preservation.

## Table of Contents

- [Quick Start](#quick-start)
  - [Basic Text Chunks for Vector Databases](#basic-text-chunks-for-vector-databases)
  - [Markdown Chunks with Structure Preservation](#markdown-chunks-with-structure-preservation)
- [Smart Chunking Features](#smart-chunking-features)
  - [🎯 Structure-Aware Chunking](#-structure-aware-chunking)
  - [📏 Precision Control](#-precision-control)
- [Vector Database Examples](#vector-database-examples)
  - [Pinecone Integration](#pinecone-integration)
  - [ChromaDB Integration](#chromadb-integration)
  - [Weaviate Integration](#weaviate-integration)
  - [Qdrant Integration](#qdrant-integration)
- [Standalone Chunking Functions](#standalone-chunking-functions)
- [RAG Application Example](#rag-application-example)
- [Best Practices](#best-practices)
  - [Chunk Size Recommendations](#chunk-size-recommendations)
  - [Metadata Utilization](#metadata-utilization)
  - [Performance Optimization](#performance-optimization)

---

## Quick Start

### Basic Text Chunks for Vector Databases

```python
from cerevox import AsyncLexa

async with AsyncLexa(api_key="your-api-key") as client:
    documents = await client.parse(["document.pdf", "report.docx"])
    
    # Get optimized chunks for vector databases
    chunks = documents.get_all_text_chunks(
        target_size=500,  # Optimal for most embedding models
        tolerance=0.1,    # ±10% size flexibility
        include_metadata=True
    )
    
    print(f"Ready for embedding: {len(chunks)} chunks")
```

### Markdown Chunks with Structure Preservation

```python
# Get markdown chunks that preserve formatting and tables
markdown_chunks = documents.get_all_markdown_chunks(
    target_size=800,      # Larger chunks for formatted content
    tolerance=0.1,
    preserve_tables=True  # Keep table structures intact
)
```

## Smart Chunking Features

### 🎯 Structure-Aware Chunking
- **Headers & Sections**: Preserves document hierarchy and logical boundaries
- **Paragraphs**: Maintains complete thoughts and context
- **Code Blocks**: Keeps syntax highlighting and structure intact
- **Tables**: Preserves table relationships and formatting

### 📏 Precision Control
- **Target Size**: Configurable chunk sizes optimized for different embedding models
- **Size Tolerance**: Flexible sizing (±10% default) for better semantic boundaries
- **Metadata Rich**: Full document context for enhanced retrieval

## Vector Database Examples

### Pinecone Integration

```python
import pinecone
from cerevox import AsyncLexa

# Initialize Pinecone
pinecone.init(api_key="your-pinecone-key", environment="your-env")
index = pinecone.Index("your-index")

async with AsyncLexa() as client:
    documents = await client.parse(["document.pdf"])
    chunks = documents.get_all_text_chunks(target_size=512)  # Optimal for Pinecone
    
    # Prepare vectors for upsert
    vectors = []
    for i, chunk in enumerate(chunks):
        embedding = generate_embedding(chunk['content'])  # Your embedding function
        vectors.append({
            'id': f"{chunk['document_filename']}_{chunk['chunk_index']}",
            'values': embedding,
            'metadata': {
                'content': chunk['content'],
                'filename': chunk['document_filename'],
                'page': chunk.get('page_number'),
                'element_type': chunk.get('element_type')
            }
        })
    
    # Upload to Pinecone
    index.upsert(vectors)
```

### ChromaDB Integration

```python
import chromadb
from cerevox import AsyncLexa

# Initialize ChromaDB
client_chroma = chromadb.Client()
collection = client_chroma.create_collection("documents")

async with AsyncLexa() as client:
    documents = await client.parse(["document.pdf"])
    chunks = documents.get_all_text_chunks(target_size=500)
    
    # Add to ChromaDB
    collection.add(
        documents=[chunk['content'] for chunk in chunks],
        metadatas=[{
            'filename': chunk['document_filename'],
            'page': chunk.get('page_number', 0),
            'chunk_index': chunk['chunk_index']
        } for chunk in chunks],
        ids=[f"doc_{i}" for i in range(len(chunks))]
    )
```

### Weaviate Integration

```python
import weaviate
from cerevox import AsyncLexa

# Initialize Weaviate client
client_weaviate = weaviate.Client("http://localhost:8080")

async with AsyncLexa() as client:
    documents = await client.parse(["document.pdf"])
    chunks = documents.get_all_text_chunks(target_size=600)
    
    # Create objects for Weaviate
    for chunk in chunks:
        data_object = {
            "content": chunk['content'],
            "filename": chunk['document_filename'],
            "page": chunk.get('page_number'),
            "element_type": chunk.get('element_type', 'text')
        }
        
        client_weaviate.data_object.create(
            data_object=data_object,
            class_name="Document"
        )
```

### Qdrant Integration

```python
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from cerevox import AsyncLexa

# Initialize Qdrant
qdrant = QdrantClient("localhost", port=6333)

# Create collection
qdrant.create_collection(
    collection_name="documents",
    vectors_config=VectorParams(size=768, distance=Distance.COSINE)
)

async with AsyncLexa() as client:
    documents = await client.parse(["document.pdf"])
    chunks = documents.get_all_text_chunks(target_size=500)
    
    # Prepare points
    points = []
    for i, chunk in enumerate(chunks):
        embedding = generate_embedding(chunk['content'])  # Your embedding function
        
        points.append(PointStruct(
            id=i,
            vector=embedding,
            payload={
                "content": chunk['content'],
                "filename": chunk['document_filename'],
                "page": chunk.get('page_number'),
                "chunk_index": chunk['chunk_index']
            }
        ))
    
    # Upload points
    qdrant.upsert(collection_name="documents", points=points)
```

## Standalone Chunking Functions

For existing text content, use the standalone chunking functions:

```python
from cerevox import chunk_text, chunk_markdown

# Chunk plain text
text_chunks = chunk_text(
    text=plain_text_content,
    target_size=500,
    tolerance=0.1
)

# Chunk markdown with structure preservation
markdown_chunks = chunk_markdown(
    markdown=markdown_content,
    target_size=800,
    tolerance=0.1,
    preserve_tables=True
)
```

## RAG Application Example

Complete example of a RAG pipeline with Cerevox:

```python
import asyncio
from cerevox import AsyncLexa
from sentence_transformers import SentenceTransformer
import chromadb

async def build_rag_pipeline():
    # Initialize components
    model = SentenceTransformer('all-MiniLM-L6-v2')
    chroma_client = chromadb.Client()
    collection = chroma_client.create_collection("rag_docs")
    
    # Parse and chunk documents
    async with AsyncLexa() as client:
        documents = await client.parse([
            "policy_doc.pdf",
            "user_manual.docx",
            "faq.html"
        ])
        
        # Get optimized chunks
        chunks = documents.get_all_text_chunks(
            target_size=400,  # Good for sentence transformers
            include_metadata=True
        )
    
    # Generate embeddings and store
    contents = [chunk['content'] for chunk in chunks]
    embeddings = model.encode(contents)
    
    collection.add(
        documents=contents,
        embeddings=embeddings.tolist(),
        metadatas=chunks,
        ids=[f"chunk_{i}" for i in range(len(chunks))]
    )
    
    print(f"RAG pipeline ready with {len(chunks)} chunks")
    return collection

# Query the RAG system
def query_rag(collection, query_text, model, top_k=5):
    query_embedding = model.encode([query_text])
    
    results = collection.query(
        query_embeddings=query_embedding.tolist(),
        n_results=top_k
    )
    
    return results

# Run the pipeline
asyncio.run(build_rag_pipeline())
```

## Best Practices

### Chunk Size Recommendations

| Embedding Model | Recommended Size | Use Case |
|----------------|------------------|----------|
| OpenAI text-embedding-ada-002 | 500-800 chars | General purpose |
| Sentence Transformers | 300-500 chars | Fast retrieval |
| Cohere Embed | 400-600 chars | Multilingual |
| E5 models | 600-1000 chars | Long context |

### Metadata Utilization

Use the rich metadata for better retrieval:

```python
# Filter by document type
pdf_chunks = [c for c in chunks if c['document_filename'].endswith('.pdf')]

# Filter by page range
first_half = [c for c in chunks if c.get('page_number', 0) <= 10]

# Filter by content type
table_chunks = [c for c in chunks if c.get('element_type') == 'table']
```

### Performance Optimization

```python
# For high-volume processing
async with AsyncLexa(
    max_concurrent=20,  # Increase parallel processing
    timeout=120.0       # Extended timeout for large files
) as client:
    # Process in batches for memory efficiency
    batch_size = 50
    for i in range(0, len(file_list), batch_size):
        batch = file_list[i:i + batch_size]
        documents = await client.parse(batch)
        chunks = documents.get_all_text_chunks(target_size=500)
        # Process chunks immediately
        await store_in_vector_db(chunks)
``` 