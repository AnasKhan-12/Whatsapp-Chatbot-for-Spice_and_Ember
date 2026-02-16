"""
05_rag_chain.py — Step 5: Full RAG Chain

WHAT THIS FILE TEACHES YOU:
- How to combine retrieval + LLM into a complete RAG chain
- How to write a good system prompt for a restaurant chatbot
- How to maintain conversation history (multi-turn chat)
- How to handle "I don't know" gracefully (hallucination prevention)
- How this connects to WhatsApp (next step)

THE FULL RAG FLOW:
  User message
      ↓
  smart_retrieve(message)   → finds relevant chunks
      ↓
  build_prompt(message, chunks, history)  → creates the LLM prompt
      ↓
  call_llm(prompt)          → GPT-4o-mini generates answer
      ↓
  Response to user
"""

import os
import google.generativeai as genai
from dotenv import load_dotenv
from retriever import smart_retrieve, format_context
CHROMA_DIR = "/data/chroma_db" if os.path.exists("/data") else "./chroma_db"

load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))


# ── SYSTEM PROMPT ──────────────────────────────────────────────────────────────
# This is the MOST important prompt in your system.
# It defines the bot's personality, rules, and how to use context.
from datetime import datetime

def get_llm():
    # Called fresh each time so date is always current
    today = datetime.now().strftime("%A, %B %d %Y")  
    # gives "Monday, February 16 2026"
    
    return genai.GenerativeModel(
        model_name="gemini-2.5-flash",
        system_instruction=f"""
You are Ember 🔥, the friendly WhatsApp assistant for Spice & Ember restaurant in New York.

TODAY IS: {today}

RULES:
1. ONLY answer using the CONTEXT provided. Never make up prices, hours, or menu items.
2. If context doesn't contain the answer say:
   "I don't have that info right now! Call us at +1-555-432-1000 🍽"
3. Keep answers short and friendly — this is WhatsApp, not an essay.
4. Use max 2 emojis per message.
5. When someone asks "are you open today" or "open now" use TODAY's day name
   to find the correct hours from context.
6. When taking an order collect: items, quantity, delivery or dine-in, address if delivery.
7. When taking a booking collect: date, time, guests, name.
""".strip()
    )


# ── PROMPT BUILDER ─────────────────────────────────────────────────────────────
def build_prompt(user_message: str, context: str, conversation_history: list[dict]) -> list[dict]:
    messages = []

    # Add conversation history (last 6 turns)
    for turn in conversation_history[-6:]:
        messages.append(turn)

    # Final message with context injected
    current_message = f"""CONTEXT FROM KNOWLEDGE BASE:
{context}

---
CUSTOMER MESSAGE: {user_message}

Answer the customer using ONLY the context above."""

    messages.append({"role": "user", "content": current_message})
    return messages


# ── LLM CALL ───────────────────────────────────────────────────────────────────
# def call_llm(messages: list[dict], temperature: float = 0.4) -> str:
#     """
#     Call OpenAI GPT-4o-mini and get a response.

#     temperature:
#         0.0 = very deterministic (good for factual Q&A)
#         0.7 = more creative (good for conversational tone)
#         0.4 = balanced — our sweet spot for a chatbot

#     Why GPT-4o-mini?
#     - 8x cheaper than GPT-4o
#     - Fast (important for WhatsApp — users expect quick replies)
#     - More than good enough for menu Q&A and order taking
#     """
#     response = client_openai.chat.completions.create(
#         model="gpt-4o-mini",
#         messages=messages,
#         temperature=temperature,
#         max_tokens=300,   # WhatsApp messages should be short
#     )
#     return response.choices[0].message.content.strip()

def call_llm(messages: list[dict]) -> str:
    # Get fresh LLM instance with current date in system prompt
    current_llm = get_llm()
    
    history = []
    for msg in messages[:-1]:
        role = "model" if msg["role"] == "assistant" else "user"
        history.append({
            "role": role,
            "parts": [msg["content"]]
        })

    chat = current_llm.start_chat(history=history)
    response = chat.send_message(messages[-1]["content"])
    return response.text.strip()

# ── FULL RAG CHAIN ──────────────────────────────────────────────────────────────
def rag_chat(user_message, conversation_history, persist_dir=CHROMA_DIR):
    # Retrieval stays simple — just the user message
    results = smart_retrieve(user_message, k=4, persist_dir=persist_dir)
    context = format_context(results)
    
    # Date is already in system prompt — no need to inject here
    messages = build_prompt(user_message, context, conversation_history)
    response = call_llm(messages)
    
    updated_history = conversation_history + [
        {"role": "user", "content": user_message},
        {"role": "assistant", "content": response}
    ]
    
    return response, updated_history

# ── SESSION MANAGER ────────────────────────────────────────────────────────────
# In a real WhatsApp bot, each phone number = one session.
# We keep conversation history per phone number in memory (or Redis in production).

class ChatSession:
    """
    Manages per-user conversation state.
    In production: replace `sessions` dict with Redis for persistence.
    """

    def __init__(self):
        # Key = phone number (or user_id), Value = conversation history list
        self.sessions: dict[str, list[dict]] = {}

    def chat(self, user_id: str, message: str) -> str:
        """
        Process a message from a user, maintaining their conversation history.
        """
        history = self.sessions.get(user_id, [])
        response, updated_history = rag_chat(message, history)

        # Keep last 20 turns to avoid token overflow
        self.sessions[user_id] = updated_history[-20:]

        return response

    def reset(self, user_id: str):
        """Clear a user's conversation (e.g. when they send 'reset' or 'start over')"""
        self.sessions[user_id] = []
        return "Chat reset! Hi again, I'm Ember 🔥 How can I help you?"

    def get_history(self, user_id: str) -> list[dict]:
        return self.sessions.get(user_id, [])


# ── ORDER/BOOKING STATE MACHINE ────────────────────────────────────────────────
# For structured flows (ordering, booking), we track what we've collected.
# The LLM handles the conversation, we just extract and validate the data.

class OrderTracker:
    """
    Tracks order/booking state for a user.
    In a real system, save this to Supabase or Firebase.
    """

    def __init__(self):
        self.orders: dict[str, dict] = {}

    def start_order(self, user_id: str):
        self.orders[user_id] = {
            "items": [],
            "type": None,        # "delivery" or "dine_in"
            "address": None,
            "time": None,
            "status": "collecting"
        }

    def start_booking(self, user_id: str):
        self.orders[user_id] = {
            "type": "booking",
            "date": None,
            "time": None,
            "guests": None,
            "name": None,
            "status": "collecting"
        }

    def get_order(self, user_id: str) -> dict:
        return self.orders.get(user_id, {})

    def confirm_order(self, user_id: str):
        if user_id in self.orders:
            self.orders[user_id]["status"] = "confirmed"
            # In production: save to database here
            print(f"📦 Order confirmed for {user_id}: {self.orders[user_id]}")


# ── RUN / DEMO ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    session = ChatSession()
    user_id = "+1234567890"

    test_conversation = [
        "Hi!",
        "Do you have any vegan options?",
        "What's the price of the Mango Sorbet?",
        "Are you open on Saturday?",
        "I want to order 2 Crispy Tofu Bites please",
    ]

    print("🔥 Spice & Ember Chatbot — Live Test\n")
    print("=" * 50)

    for message in test_conversation:
        print(f"\n👤 Customer: {message}")
        response = session.chat(user_id, message)
        print(f"🔥 Ember:    {response}")
        print("-" * 40)
