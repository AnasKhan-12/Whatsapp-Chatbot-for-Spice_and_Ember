"""
startup.py — runs once when Render starts the server
Builds ChromaDB from scratch if it doesn't exist yet
"""
import sys

import os
from loaders import load_all_documents
from chunker import chunk_all_documents
from embedder import embed_and_store

CHROMA_DIR = "./chroma_db"

print("📦 Building ChromaDB...")
docs   = load_all_documents(
    pdf_path="./spice_and_ember_data.pdf",
    excel_path="./spice_and_ember_menu.xlsx"
)
chunks = chunk_all_documents(docs)
embed_and_store(chunks, persist_dir=CHROMA_DIR)
print("✅ ChromaDB ready!")