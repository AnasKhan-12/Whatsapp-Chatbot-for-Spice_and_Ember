"""
02_chunker.py — Step 2: Smart Chunking

WHAT THIS FILE TEACHES YOU:
- Why chunking strategy is the #1 factor in RAG quality
- Different chunking strategies for different data types
- What chunk_size and chunk_overlap mean
- How to use tiktoken to count TOKENS (not characters)

THE GOLDEN RULE OF CHUNKING:
  Chunks should be semantically complete — a chunk should answer ONE question.
  Too small = loses context. Too large = retrieves irrelevant noise.

CHUNK SIZE GUIDE (in tokens):
  - Menu items / FAQ answers:   100–200 tokens  (very focused)
  - Chef notes / paragraphs:    200–350 tokens  (needs context)
  - Table rows:                  50–150 tokens  (already compact)
  - HTML sections:              200–400 tokens  (page-level content)
"""

import tiktoken
from dataclasses import dataclass

encoder = tiktoken.get_encoding("cl100k_base")

def count_tokens(text: str) -> int:
    return len(encoder.encode(text))


# ── CHUNK DATACLASS ───────────────────────────────────────────────────────────
@dataclass
class Chunk:
    text: str
    metadata: dict
    token_count: int


# ── STRATEGY 1: NO CHUNKING (for already-small documents) ─────────────────────
# JSON menu items and CSV rows are already small and self-contained.
# Splitting them further would DESTROY their meaning.

def chunk_passthrough(doc: dict) -> list[Chunk]:
    """
    Use the document as-is. No splitting.
    Best for: JSON menu items, CSV rows, short FAQ answers.
    """
    text = doc["page_content"]
    tokens = count_tokens(text)

    # Safety: if somehow a passthrough doc is too big, warn us
    if tokens > 500:
        print(f"⚠️  Warning: passthrough doc has {tokens} tokens — consider splitting")

    return [Chunk(
        text=text,
        metadata={**doc["metadata"], "chunk_index": 0, "chunk_strategy": "passthrough"},
        token_count=tokens
    )]


# ── STRATEGY 2: RECURSIVE CHARACTER SPLITTING ─────────────────────────────────
# The most common strategy. Split by paragraphs → sentences → words.
# Uses OVERLAP so context isn't lost at chunk boundaries.

def chunk_recursive(doc: dict, chunk_size: int = 300, overlap: int = 50) -> list[Chunk]:
    """
    Split text recursively. Try splitting by paragraph first,
    then sentence, then word — stopping when chunks are small enough.

    chunk_size: max tokens per chunk
    overlap: how many tokens to repeat between adjacent chunks
             (prevents losing context at the boundary)

    Best for: Chef notes, plain text paragraphs, HTML sections.

    OVERLAP EXPLAINED:
    Without overlap:  [chunk1: "The steak is dry aged..."] [chunk2: "served with mashed..."]
    With overlap:     [chunk1: "The steak is dry aged..."] [chunk2: "dry aged. served with mashed..."]
    The second version means a query about "dry aged steak sides" will hit chunk2 too.
    """
    text = doc["page_content"]
    separators = ["\n\n", "\n", ". ", " "]
    chunks = []

    def split(text: str, sep_idx: int = 0) -> list[str]:
        """Recursively split until all pieces fit in chunk_size tokens."""
        if count_tokens(text) <= chunk_size:
            return [text]

        if sep_idx >= len(separators):
            # Hard split by token count (last resort)
            words = text.split()
            result, current = [], []
            for word in words:
                current.append(word)
                if count_tokens(" ".join(current)) > chunk_size:
                    result.append(" ".join(current[:-1]))
                    current = current[-overlap:] + [word]
            if current:
                result.append(" ".join(current))
            return result

        sep = separators[sep_idx]
        parts = text.split(sep)
        result, current_chunk = [], ""

        for part in parts:
            candidate = current_chunk + sep + part if current_chunk else part
            if count_tokens(candidate) <= chunk_size:
                current_chunk = candidate
            else:
                if current_chunk:
                    # Recursively try to split current_chunk further
                    sub_chunks = split(current_chunk, sep_idx + 1)
                    result.extend(sub_chunks)
                    # Add overlap from end of last sub_chunk
                    overlap_text = sub_chunks[-1][-overlap*4:] if sub_chunks else ""
                    current_chunk = overlap_text + sep + part if overlap_text else part
                else:
                    current_chunk = part

        if current_chunk:
            result.extend(split(current_chunk, sep_idx + 1))

        return [c for c in result if c.strip()]

    raw_chunks = split(text)

    for i, chunk_text in enumerate(raw_chunks):
        if not chunk_text.strip():
            continue
        chunks.append(Chunk(
            text=chunk_text.strip(),
            metadata={
                **doc["metadata"],
                "chunk_index": i,
                "chunk_total": len(raw_chunks),
                "chunk_strategy": "recursive",
                "chunk_size_target": chunk_size,
                "overlap": overlap
            },
            token_count=count_tokens(chunk_text)
        ))

    return chunks


# ── STRATEGY 3: SENTENCE WINDOW CHUNKING ──────────────────────────────────────
# Advanced technique used in production RAG.
# Store SMALL chunks for precise retrieval, but return LARGER context to the LLM.
# This solves: "retrieved chunk is too short → LLM lacks context to answer well"

def chunk_sentence_window(doc: dict, window_size: int = 3) -> list[Chunk]:
    """
    Split into individual sentences, but store a 'window' of surrounding
    sentences as context in the metadata.

    At query time:
    1. Embed and search the individual sentence (small = precise match)
    2. Return the window (large = enough context for LLM to answer)

    Best for: FAQ answers, chef notes — where one sentence is the answer
              but the LLM needs surrounding context to explain it properly.

    window_size: number of sentences before AND after to include as context
    """
    import re
    text = doc["page_content"]

    # Split into sentences (handles . ! ? followed by space/newline)
    sentences = re.split(r'(?<=[.!?])\s+', text)
    sentences = [s.strip() for s in sentences if len(s.strip()) > 20]

    chunks = []
    for i, sentence in enumerate(sentences):
        # Build context window
        start = max(0, i - window_size)
        end = min(len(sentences), i + window_size + 1)
        window_text = " ".join(sentences[start:end])

        chunks.append(Chunk(
            text=sentence,         # ← this gets EMBEDDED (small, precise)
            metadata={
                **doc["metadata"],
                "chunk_index": i,
                "chunk_total": len(sentences),
                "chunk_strategy": "sentence_window",
                "window_text": window_text,  # ← this gets sent to LLM (larger context)
                "window_size": window_size
            },
            token_count=count_tokens(sentence)
        ))

    return chunks


# ── ROUTING FUNCTION ───────────────────────────────────────────────────────────
# This is the KEY function. Different formats → different strategies.
# This is exactly what you'd see in a real Upwork RAG project.

# def chunk_document(doc: dict) -> list[Chunk]:
#     """
#     Route each document to the right chunking strategy based on its format/type.

#     ROUTING LOGIC:
#     - JSON menu items → passthrough (already 1 item = 1 concept)
#     - CSV rows        → passthrough (already 1 row = 1 item's nutrition)
#     - FAQ markdown    → recursive, small chunks (Q&A pairs are compact)
#     - Chef notes      → sentence_window (dense info, needs context)
#     - HTML sections   → recursive, medium chunks (page-level content)
#     - PDF text        → recursive, large chunks (mixed content)
#     - PDF tables      → passthrough (table rows are already structured)
#     """
def chunk_document(doc: dict) -> list[Chunk]:
    fmt = doc["metadata"].get("format", "")
    doc_type = doc["metadata"].get("doc_type", "")

    # Already small & self-contained → no splitting needed
    if fmt in ["table_row", "excel_row", "key_value_table", 
               "qa_pair", "inline_structured"]:
        return chunk_passthrough(doc)

    # About section paragraphs are already one paragraph each
    # splitting them breaks sentences — just pass through
    if fmt == "plain_text":
        return chunk_passthrough(doc)

    # Chef notes are dense → sentence window gives context
    if doc_type == "chef_note":
        return chunk_sentence_window(doc, window_size=2)

    # HTML sections → recursive medium size
    if fmt == "html_parsed":
        return chunk_recursive(doc, chunk_size=300, overlap=50)

    # PDF text fallback
    if fmt == "text":
        return chunk_recursive(doc, chunk_size=350, overlap=60)

    return chunk_recursive(doc, chunk_size=300, overlap=50)


# ── MASTER CHUNKER ─────────────────────────────────────────────────────────────
def chunk_all_documents(documents: list[dict]) -> list[Chunk]:
    """
    Chunk every document using the right strategy.
    Returns a flat list of all chunks ready for embedding.
    """
    all_chunks = []
    strategy_counts = {}

    for doc in documents:
        chunks = chunk_document(doc)
        all_chunks.extend(chunks)

        # Track how many chunks came from each strategy
        for chunk in chunks:
            strat = chunk.metadata.get("chunk_strategy", "unknown")
            strategy_counts[strat] = strategy_counts.get(strat, 0) + 1

    print(f"\n✅ Chunking complete: {len(all_chunks)} total chunks")
    print("   Strategy breakdown:")
    for strat, count in sorted(strategy_counts.items()):
        print(f"     {strat}: {count} chunks")

    # Token distribution stats
    token_counts = [c.token_count for c in all_chunks]
    print(f"   Token stats: min={min(token_counts)}, "
          f"max={max(token_counts)}, "
          f"avg={sum(token_counts)//len(token_counts)}")

    return all_chunks


# ── RUN ───────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    from loaders import load_all_documents

    docs = load_all_documents(
    pdf_path="./spice_and_ember_data.pdf",
    excel_path="./spice_and_ember_menu.xlsx"
)
    chunks = chunk_all_documents(docs)

    print("\n── Sample Chunks ──")
    for chunk in chunks[:3]:
        print(f"\n[{chunk.metadata['chunk_strategy']}] ({chunk.token_count} tokens)")
        print(chunk.text[:200])
        print("Metadata keys:", list(chunk.metadata.keys()))
