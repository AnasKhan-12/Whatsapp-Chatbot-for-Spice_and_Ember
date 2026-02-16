"""
startup.py — runs once when Render starts the server
Builds ChromaDB from scratch if it doesn't exist yet
"""
import os
import sys

CHROMA_DIR = "/data/chroma_db" if os.path.exists("/data") else "./chroma_db"
print("🚀 Starting up...")
# Check if ChromaDB already exists
if not os.path.exists("./chroma_db") or len(os.listdir("./chroma_db")) == 0:
    print("📦 ChromaDB not found — building from scratch...")
    
    # Import and run the pipeline
    from loaders import load_all_documents
    from chunker import chunk_all_documents
    from embedder import embed_and_store
    
    docs   = load_all_documents(
        pdf_path="./spice_and_ember_data.pdf",
        excel_path="./spice_and_ember_menu.xlsx"
    )
    chunks = chunk_all_documents(docs)
    embed_and_store(chunks, persist_dir=CHROMA_DIR)
    
    print("✅ ChromaDB built successfully!")
else:
    print("⚡ ChromaDB already exists — skipping rebuild")

print("✅ Startup complete — launching bot...")