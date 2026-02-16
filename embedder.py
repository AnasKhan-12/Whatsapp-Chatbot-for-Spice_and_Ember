"""
03_embedder.py — Step 3: Embed Chunks & Store in ChromaDB

WHAT THIS FILE TEACHES YOU:
- What embeddings ARE (numbers that represent meaning)
- How OpenAI's text-embedding-3-small works
- How to store embeddings in ChromaDB (local vector database)
- What metadata filtering is and why it's powerful
- How to avoid re-embedding (cost savings with persistence)

WHAT IS AN EMBEDDING?
  "I want vegan food"  →  [0.23, -0.41, 0.87, ...]  (1536 numbers)
  "Plant-based options" → [0.25, -0.39, 0.84, ...]  (similar numbers!)
  "Ribeye steak"        → [-0.71, 0.22, -0.33, ...] (very different numbers)

  ChromaDB stores these number arrays. When you search,
  it finds chunks whose numbers are CLOSEST to your query's numbers.
  That's semantic search — finding meaning, not just keywords.

COST TIP:
  text-embedding-3-small = $0.02 per 1M tokens
  For our ~100 chunks × ~200 tokens = ~20,000 tokens = $0.0004 total
  Basically free. But always persist so you don't re-embed!
"""

import os
import json
import chromadb
from chromadb.utils import embedding_functions
# CORRECT
import google.generativeai as genai
from dotenv import load_dotenv
CHROMA_DIR = "/data/chroma_db" if os.path.exists("/data") else "./chroma_db"
load_dotenv()  # loads OPENAI_API_KEY from .env file

genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# ── SETUP CHROMADB ─────────────────────────────────────────────────────────────
# ChromaDB can run:
#   - In-memory (lost on restart)  → for testing
#   - Persistent (saved to disk)   → for production ✅

def get_vector_store(persist_dir: str = CHROMA_DIR):
    # No embedding function passed here at all
    # We will embed manually and pass raw vectors ourselves
    client = chromadb.PersistentClient(path=persist_dir)
    collection = client.get_or_create_collection(
        name="spice_and_ember",
        metadata={"hnsw:space": "cosine"}
    )
    return collection
def embed_text(text: str) -> list[float]:
    # This calls Gemini directly and returns the raw vector
    result = genai.embed_content(
        model="models/gemini-embedding-001",
        content=text,
        task_type="retrieval_document"
    )
    return result["embedding"]

# ── EMBED AND STORE ────────────────────────────────────────────────────────────

def embed_and_store(chunks: list, persist_dir: str = "./chroma_db"):
    collection = get_vector_store(persist_dir)

    # Skip if already populated
    if collection.count() > 0:
        print(f"⚡ Already has {collection.count()} chunks. Delete ./chroma_db to re-embed.")
        return collection

    print(f"🔄 Embedding {len(chunks)} chunks with Gemini...")

    # ChromaDB accepts batches — we batch by 100 for efficiency
    batch_size = 100
    total_batches = (len(chunks) + batch_size - 1) // batch_size
    ids        = []
    documents  = []
    metadatas  = []
    embeddings = []   # ← we now build this manually

    for i, chunk in enumerate(chunks):
        chunk_id = f"chunk_{i:04d}"

        # Embed the text by calling Gemini ourselves
        vector = embed_text(chunk.text)

        # Clean metadata — ChromaDB only accepts str, int, float, bool
        clean_meta = {}
        for k, v in chunk.metadata.items():
            if isinstance(v, (str, int, float, bool)):
                clean_meta[k] = v
            elif isinstance(v, list):
                clean_meta[k] = ", ".join(str(x) for x in v)
            else:
                clean_meta[k] = str(v)

        ids.append(chunk_id)
        documents.append(chunk.text)
        metadatas.append(clean_meta)
        embeddings.append(vector)

        # Log progress every 10 chunks
        if (i + 1) % 10 == 0:
            print(f"   Embedded {i+1}/{len(chunks)} chunks...")

    # Pass the pre-computed vectors directly — no embedding function needed
    collection.add(
        ids=ids,
        documents=documents,
        metadatas=metadatas,
        embeddings=embeddings   # ← raw vectors go here
    )

    print(f"\n✅ Done! {collection.count()} chunks stored in ChromaDB")
    return collection


# ── INSPECT THE STORE ──────────────────────────────────────────────────────────
def inspect_collection(persist_dir: str = "./chroma_db"):
    """
    Print stats about what's in your vector store.
    Run this after embedding to verify everything looks right.
    """
    collection = get_vector_store(persist_dir)
    total = collection.count()
    print(f"\n📊 Vector Store Stats:")
    print(f"   Total chunks: {total}")

    if total == 0:
        print("   (empty — run embed_and_store first)")
        return

    # Sample 5 random chunks
    sample = collection.get(limit=5, include=["documents", "metadatas"])
    print(f"\n── 5 Sample Chunks ──")
    for i in range(len(sample["ids"])):
        print(f"\n[{sample['ids'][i]}]")
        print(f"  Format:   {sample['metadatas'][i].get('format', 'N/A')}")
        print(f"  Doc type: {sample['metadatas'][i].get('doc_type', 'N/A')}")
        print(f"  Tokens:   {sample['metadatas'][i].get('token_count', 'N/A')}")
        print(f"  Text:     {sample['documents'][i][:120]}...")

    # Count by format
    all_meta = collection.get(include=["metadatas"])["metadatas"]
    format_counts = {}
    for m in all_meta:
        fmt = m.get("format", "unknown")
        format_counts[fmt] = format_counts.get(fmt, 0) + 1

    print(f"\n── Chunks by Format ──")
    for fmt, count in sorted(format_counts.items(), key=lambda x: -x[1]):
        print(f"   {fmt}: {count}")


# ── RUN ───────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    from loaders import load_all_documents
    from chunker import chunk_all_documents

    # Load → Chunk → Embed
    docs = load_all_documents(
    pdf_path="./spice_and_ember_data.pdf",
    excel_path="./spice_and_ember_menu.xlsx"
)
    chunks = chunk_all_documents(docs)
    collection = embed_and_store(chunks)

    # Verify
    inspect_collection()
