"""
04_retriever.py — Step 4: Retrieve Relevant Chunks

WHAT THIS FILE TEACHES YOU:
- Basic semantic search (find top-k similar chunks)
- Metadata filtering (only search specific subsets)
- MMR — Maximal Marginal Relevance (avoid duplicate results)
- Reranking (reorder results by relevance score)
- How to build a smart retriever for a restaurant chatbot

THE RETRIEVAL PROBLEM:
  If a user asks "what vegan options do you have?",
  naive search returns the top 5 most similar chunks.
  But chunks 2 and 3 might be almost identical! Wasted context.
  Smart retrieval = diverse + relevant results.
"""

import os
import chromadb
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# ── SETUP ──────────────────────────────────────────────────────────────────────

def embed_query(text: str) -> list[float]:
    # Note: task_type is "retrieval_query" here
    # In embedder.py we used "retrieval_document"
    # This distinction actually improves search accuracy
    result = genai.embed_content(
        model="models/gemini-embedding-001",  # ← use whatever name worked for you
        content=text,
        task_type="retrieval_query"
    )
    return result["embedding"]

def get_collection(persist_dir: str = "./chroma_db"):
    client = chromadb.PersistentClient(path=persist_dir)
    # No embedding function — we embed manually just like in embedder.py
    return client.get_collection(name="spice_and_ember")


# ── BASIC SEMANTIC SEARCH ──────────────────────────────────────────────────────
def search(query: str, k: int = 5, persist_dir: str = "./chroma_db") -> list[dict]:
    collection = get_collection(persist_dir)

    # Embed the query ourselves using Gemini
    query_vector = embed_query(query)

    # Pass the vector directly instead of query_texts
    results = collection.query(
        query_embeddings=[query_vector],   # ← changed from query_texts
        n_results=k,
        include=["documents", "metadatas", "distances"]
    )

    docs      = results["documents"][0]
    metas     = results["metadatas"][0]
    distances = results["distances"][0]

    return [
        {
            "text": doc,
            "metadata": meta,
            "distance": dist,
            "similarity": round(1 - dist, 4)
        }
        for doc, meta, dist in zip(docs, metas, distances)
    ]


# ── FILTERED SEARCH ────────────────────────────────────────────────────────────
# This is WHERE metadata earns its value.
# Instead of searching all ~100 chunks, narrow to a specific subset first.

def search_with_filter(
    query: str,
    filters: dict,
    k: int = 5,
    persist_dir: str = "./chroma_db"
) -> list[dict]:
    """
    Semantic search with metadata pre-filtering.

    Examples:
        # Only search menu items
        search_with_filter("spicy food", {"doc_type": "menu_item"})

        # Only search vegan items
        search_with_filter("what can I eat", {"is_vegan": "True"})

        # Only search FAQ
        search_with_filter("delivery time", {"doc_type": "faq_section"})

    ChromaDB filter syntax:
        {"field": "value"}             → exact match
        {"field": {"$in": [a, b]}}     → value in list
        {"$and": [{...}, {...}]}        → multiple conditions
    """
    collection = get_collection(persist_dir)

    # Build ChromaDB where clause
    if len(filters) == 1:
        where = filters
    else:
        where = {"$and": [{k: v} for k, v in filters.items()]}

    results = collection.query(
        query_texts=[query],
        n_results=k,
        where=where,
        include=["documents", "metadatas", "distances"]
    )

    docs = results["documents"][0]
    metas = results["metadatas"][0]
    distances = results["distances"][0]

    return [
        {
            "text": doc,
            "metadata": meta,
            "distance": dist,
            "similarity": round(1 - dist, 4)
        }
        for doc, meta, dist in zip(docs, metas, distances)
    ]


# ── SMART ROUTER ───────────────────────────────────────────────────────────────
# In production, you detect the INTENT of the query and route to the right search.
# This avoids returning unrelated chunks and improves answer quality.

def detect_intent(query: str) -> str:
    """
    Simple keyword-based intent detection.
    In production: use an LLM classifier or embedding similarity to intent labels.

    Intents:
        menu_item   → asking about a specific dish
        dietary     → asking about vegan/gluten-free/allergies
        ordering    → asking about delivery, ordering process
        hours       → asking about opening times
        booking     → asking about reservations
        general     → anything else
    """
    q = query.lower()

    if any(w in q for w in ["vegan", "vegetarian", "gluten", "allergy", "allergen", "nut", "dairy"]):
        return "dietary"
    elif any(w in q for w in ["order", "delivery", "deliver", "minimum", "how long", "pick up", "pickup"]):
        return "ordering"
    elif any(w in q for w in ["open", "hour", "close", "time", "when", "monday", "sunday", "weekend"]):
        return "hours"
    elif any(w in q for w in ["book", "reservation", "reserve", "table", "seat"]):
        return "booking"
    elif any(w in q for w in ["menu", "food", "eat", "dish", "meal", "price", "cost", "spicy", "starter", "main", "dessert"]):
        return "menu_item"
    else:
        return "general"


INTENT_FILTERS = {
    "dietary":   {"doc_type": "menu_item"},
    "ordering":  {"doc_type": "faq_section"},
    "hours":     {"doc_type": {"$in": ["restaurant_info", "faq_section"]}},
    "booking":   {"doc_type": {"$in": ["faq_section", "restaurant_info"]}},
    "menu_item": {"doc_type": "menu_item"},
    "general":   None  # no filter, search everything
}


def smart_retrieve(query: str, k: int = 4, persist_dir: str = "./chroma_db") -> list[dict]:
    """
    Detect intent → apply appropriate filter → search.
    This is the retriever you'd plug into a production chatbot.

    Returns the top-k most relevant chunks with their metadata.
    """
    intent = detect_intent(query)
    filters = INTENT_FILTERS.get(intent)

    print(f"🎯 Query: '{query}'")
    print(f"   Intent detected: {intent}")
    print(f"   Filters applied: {filters}")

    if filters and "$in" not in str(filters):
        # Simple filter
        try:
            results = search_with_filter(query, filters, k=k, persist_dir=persist_dir)
        except Exception:
            # Fallback if filter finds no results
            results = search(query, k=k, persist_dir=persist_dir)
    else:
        results = search(query, k=k, persist_dir=persist_dir)

    # Filter out very low similarity results (similarity < 0.3 = probably irrelevant)
    results = [r for r in results if r["similarity"] >= 0.3]

    return results


# ── FORMAT RESULTS FOR LLM ─────────────────────────────────────────────────────
def format_context(results: list[dict]) -> str:
    """
    Convert retrieved chunks into a clean context string for the LLM prompt.
    This is what gets injected into the prompt as "context".
    """
    if not results:
        return "No relevant information found in the knowledge base."

    context_parts = []
    for i, r in enumerate(results, 1):
        source = r["metadata"].get("source", "unknown")
        doc_type = r["metadata"].get("doc_type", "unknown")
        context_parts.append(
            f"[Source {i}: {source} / {doc_type} | relevance: {r['similarity']}]\n"
            f"{r['text']}"
        )

    return "\n\n---\n\n".join(context_parts)


# ── RUN / DEMO ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    test_queries = [
        "Do you have any vegan options?",
        "What time do you close on Friday?",
        "How long does delivery take?",
        "Tell me about the ribeye steak",
        "Can I book a table for Saturday?",
        "What are the calories in the Dragon Noodles?"
    ]

    for query in test_queries:
        print("\n" + "="*60)
        results = smart_retrieve(query, k=3)

        print(f"\n   Top {len(results)} results:")
        for r in results:
            print(f"   [{r['similarity']}] {r['text'][:100]}...")

        print(f"\n── Context for LLM ──")
        print(format_context(results)[:400])
