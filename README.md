<<<<<<< HEAD
# 🔥 Spice & Ember WhatsApp RAG Chatbot

A production-ready WhatsApp chatbot powered by Retrieval-Augmented Generation (RAG) that answers questions about restaurant menu, pricing, dietary information, and handles orders/bookings.

## 🎯 Features

- **RAG Pipeline**: Uses ChromaDB vector store + Google Gemini 2.5 Flash for intelligent responses
- **Multi-format Data**: Processes PDF menus and Excel spreadsheets
- **Conversation Memory**: Maintains context across multi-turn conversations
- **WhatsApp Integration**: Real-time messaging via Twilio API
- **Smart Retrieval**: Hybrid search with query expansion for better accuracy
- **Production Ready**: Deployed on Render.com with proper error handling
=======
# 🔥 Spice & Ember — RAG-Powered WhatsApp Chatbot

> A production-grade AI chatbot for a restaurant, built with Retrieval-Augmented Generation (RAG).
> Answers customer questions about the menu, hours, dietary needs, and takes orders — all on WhatsApp.

---

## 📸 Demo

| Customer Query | Bot Response |
|---|---|
| "Do you have vegan options?" | Lists all vegan items with prices |
| "Tell me about the ribeye steak" | Chef's notes + price + calories |
| "Are you open today?" | Checks today's day → returns correct hours |
| "I want to order 2 Crispy Tofu Bites" | Starts order flow, asks delivery or dine-in |

---
>>>>>>> 8ddd03b912c09c9e76794550857d4824eafd05ae

## 🏗️ Architecture

```
<<<<<<< HEAD
User WhatsApp Message
        ↓
Twilio API (receives message)
        ↓
FastAPI Webhook (06_whatsapp_bot.py)
        ↓
RAG Chain (rag_chain.py)
        ├─→ Retriever (retriever.py) → ChromaDB
        └─→ Google Gemini 2.5 Flash
        ↓
Response sent back via Twilio
        ↓
User receives reply on WhatsApp
```

## 🛠️ Tech Stack

- **Backend**: Python, FastAPI, Uvicorn
- **LLM**: Google Gemini 2.5 Flash
- **RAG Framework**: LangChain
- **Vector Database**: ChromaDB
- **Embeddings**: Google Generative AI Embeddings
- **Messaging**: Twilio WhatsApp API
- **Deployment**: Render.com
- **Data Processing**: PDFPlumber, Pandas, BeautifulSoup

## 📁 Project Structure

```
RAG Claude/
├── 06_whatsapp_bot.py      # FastAPI webhook server
├── rag_chain.py             # RAG pipeline + conversation manager
├── retriever.py             # Smart retrieval with query expansion
├── embedder.py              # Vector embedding logic
├── chunker.py               # Document chunking strategies
├── loaders.py               # PDF/Excel/HTML data loaders
├── chroma_db/               # Vector database storage
├── requirements.txt         # Python dependencies
├── Procfile                 # Deployment configuration
└── .env                     # Environment variables (not in repo)
```

## 🚀 Deployment

See [DEPLOYMENT_STEPS.md](DEPLOYMENT_STEPS.md) for detailed instructions.

**Quick summary:**
1. Push code to GitHub
2. Deploy to Render.com (free tier)
3. Set environment variables
4. Configure Twilio webhook
5. Test on WhatsApp!

## 🧪 Testing

Try these messages:
- `Hello` - Get welcome message
- `What's on the menu?` - See menu items
- `Do you have vegan options?` - Dietary queries
- `What's the price of Mango Sorbet?` - Pricing info
- `I want to order 2 Crispy Tofu Bites` - Place order
- `reset` - Clear conversation history

## 🔑 Environment Variables

Required in `.env` file:
```
GOOGLE_API_KEY=your_google_api_key
TWILIO_ACCOUNT_SID=your_twilio_sid
TWILIO_AUTH_TOKEN=your_twilio_token
TWILIO_WHATSAPP_NUMBER=whatsapp:+1234567890
```

## 📊 RAG Pipeline Details

### 1. Data Loading
- PDF menus → Text extraction with PDFPlumber
- Excel spreadsheets → Pandas DataFrame processing
- Structured chunking with metadata preservation

### 2. Embedding & Storage
- Google Generative AI Embeddings (768 dimensions)
- ChromaDB for vector storage
- Metadata filtering for precise retrieval

### 3. Smart Retrieval
- Query expansion for better recall
- Hybrid search (semantic + keyword)
- Top-k retrieval with relevance scoring

### 4. Response Generation
- Context-aware prompting
- Conversation history (last 6 turns)
- Hallucination prevention (only answer from context)

## 🎓 What I Learned

- Building production RAG systems with LangChain
- Vector database optimization with ChromaDB
- FastAPI webhook integration with Twilio
- Conversation state management
- Deploying Python apps to cloud platforms
- Handling real-time messaging at scale

## 📝 License

MIT

## 👤 Author

[Your Name]
- GitHub: [@yourusername](https://github.com/yourusername)
- LinkedIn: [Your LinkedIn](https://linkedin.com/in/yourprofile)

---

**Note**: This is a portfolio project demonstrating RAG implementation. For production use, consider:
- Redis for session persistence
- Proper database for order/booking storage
- Rate limiting and authentication
- Monitoring and logging infrastructure
=======
┌─────────────────────────────────────────────────────────────┐
│                     INDEXING PIPELINE                       │
│                      (runs once)                            │
│                                                             │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐             │
│  │   PDF    │    │  Excel   │    │          │             │
│  │ 5 pages  │───▶│ 3 sheets │───▶│ 01       │             │
│  │ 6 formats│    │          │    │ loaders  │             │
│  └──────────┘    └──────────┘    └────┬─────┘             │
│                                       │ 76 documents       │
│                                  ┌────▼─────┐             │
│                                  │ 02       │             │
│                                  │ chunker  │             │
│                                  └────┬─────┘             │
│                                       │ 74 chunks          │
│                                  ┌────▼─────┐             │
│                                  │ 03       │             │
│                                  │ embedder │             │
│                                  │ (Gemini) │             │
│                                  └────┬─────┘             │
│                                       │ vectors            │
│                                  ┌────▼─────┐             │
│                                  │ ChromaDB │             │
│                                  │ (local)  │             │
│                                  └──────────┘             │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                      QUERY PIPELINE                         │
│                  (runs every message)                       │
│                                                             │
│  WhatsApp                                                   │
│     │                                                       │
│     ▼                                                       │
│  Twilio ──── POST ────▶ ngrok ────▶ FastAPI /webhook       │
│                                          │                  │
│                                     ┌────▼─────┐           │
│                                     │ 04       │           │
│                                     │retriever │           │
│                                     │          │           │
│                                     │ 1. detect│           │
│                                     │   intent │           │
│                                     │ 2. filter│           │
│                                     │   chunks │           │
│                                     │ 3. embed │           │
│                                     │   query  │           │
│                                     │ 4. search│           │
│                                     │  vectors │           │
│                                     └────┬─────┘           │
│                                          │ top 4 chunks     │
│                                     ┌────▼─────┐           │
│                                     │ 05       │           │
│                                     │ rag chain│           │
│                                     │          │           │
│                                     │ context  │           │
│                                     │ +        │           │
│                                     │ history  │           │
│                                     │ +        │           │
│                                     │ question │           │
│                                     └────┬─────┘           │
│                                          │                  │
│                                     ┌────▼─────┐           │
│                                     │  Gemini  │           │
│                                     │   LLM    │           │
│                                     └────┬─────┘           │
│                                          │ answer           │
│                                          ▼                  │
│                                       Twilio                │
│                                          │                  │
│                                          ▼                  │
│                                       WhatsApp              │
└─────────────────────────────────────────────────────────────┘
```

---

## 🛠️ Tech Stack

| Layer | Technology | Why |
|---|---|---|
| Language | Python 3.10 | Industry standard for AI |
| LLM | Gemini 2.5 Flash | Free tier, fast, high quality |
| Embeddings | Gemini Embedding 001 | Free, 768 dimensions |
| Vector DB | ChromaDB | Local, no setup, persistent |
| PDF Parsing | pdfplumber | Detects tables + text |
| Excel Parsing | openpyxl | Reads sheets and cell values |
| API Server | FastAPI + Uvicorn | Fast, async, production-ready |
| WhatsApp | Twilio Sandbox | Easy webhook integration |
| Tunneling | ngrok | Exposes localhost to Twilio |

---

## 📂 Project Structure

```
spice-ember-bot/
│
├── data/
│   ├── spice_and_ember_data.pdf      # Restaurant knowledge base (5 pages, 6 formats)
│   └── spice_and_ember_menu.xlsx     # Menu, nutrition, hours (3 sheets)
│
├── 01_loaders.py       # Extracts text from PDF + Excel into documents
├── 02_chunker.py       # Splits documents into right-sized chunks
├── 03_embedder.py      # Embeds chunks with Gemini → stores in ChromaDB
├── 04_retriever.py     # Semantic search with intent detection + metadata filtering
├── 05_rag_chain.py     # Full RAG loop: retrieve → augment → generate
├── 06_whatsapp_bot.py  # FastAPI webhook that connects everything to WhatsApp
│
├── chroma_db/          # Auto-generated vector store (after running embedder)
├── test_local.py       # Test the bot locally without WhatsApp
├── requirements.txt
├── .env.example
└── README.md
```

---

## 🧠 What Makes This RAG Pipeline Smart

### 1. Multi-Format Data Extraction
The knowledge base is a single PDF with 6 different data formats inside it:

```
Page 1  →  plain text paragraphs    (About section)
Page 1  →  key-value table          (Contact & ops)
Page 2  →  structured table         (Opening hours)
Page 3  →  multi-column table       (Full menu)
Page 3  →  Q&A pairs                (FAQ section)
Page 4  →  unstructured text        (Chef's notes)
Page 5  →  inline structured text   (Nutrition data)
```

Each format is parsed differently — tables become natural language sentences, Q&A pairs stay as question+answer units, plain text is sentence-split.

### 2. Intent-Based Retrieval
Before searching, the bot detects what the user is asking about:

```python
"do you have vegan options?"  →  intent: dietary   →  filter: menu_items only
"are you open Saturday?"      →  intent: hours     →  filter: hours docs only
"i want to book a table"      →  intent: booking   →  filter: faq + restaurant_info
"tell me about the ribeye"    →  intent: menu_item →  filter: menu_items only
```

This means the bot never searches nutrition data when answering hours questions — retrieval is fast and precise.

### 3. Metadata Filtering
Every document has rich metadata attached:

```python
{
    "doc_type": "menu_item",
    "category": "main",
    "is_vegan": "Yes",
    "price": 9.99,
    "spice_level": "mild"
}
```

ChromaDB uses these as pre-filters before vector search, dramatically improving accuracy.

### 4. Conversation Memory
Each WhatsApp number gets its own conversation history stored in memory. The last 6 turns are injected into every prompt, so the bot remembers context:

```
User:  "I want the tofu bites"
Bot:   "Great! Delivery or dine-in?"
User:  "Delivery"           ← bot knows this refers to the tofu bites order
Bot:   "What's your address?"
```

---

## ⚙️ Setup & Installation

### 1. Clone the repo
```bash
git clone https://github.com/yourusername/spice-ember-bot.git
cd spice-ember-bot
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Set up environment variables
```bash
cp .env.example .env
```

Fill in your `.env`:
```
GOOGLE_API_KEY=your_gemini_api_key
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=xxxxxxxxxxxxxxxx
TWILIO_WHATSAPP_NUMBER=whatsapp:+14155238886
```

Get your free Gemini API key at: `aistudio.google.com`

### 4. Build the knowledge base (run once)
```bash
python 01_loaders.py    # verify data extraction
python 03_embedder.py   # embed + store in ChromaDB
```

### 5. Test locally (no WhatsApp needed)
```bash
# Terminal 1
python 06_whatsapp_bot.py

# Terminal 2
python test_local.py
```

### 6. Connect to WhatsApp
```bash
# Terminal 1 — expose local server
ngrok http 8000

# Terminal 2 — run the bot
python 06_whatsapp_bot.py
```

Set webhook URL in Twilio Console:
```
https://your-ngrok-url.ngrok-free.app/webhook
```

---

## 🧪 Sample Local Test Output

```
👤 You:   Hi!
🔥 Ember: Hey there! 👋 I'm Ember, your assistant for Spice & Ember restaurant. 
          How can I help you today? 🔥
----------------------------------------
👤 You:   Do you have any vegan options?
🔥 Ember: Yes, we do! 🌱 Our vegan options include:
          • Crispy Tofu Bites — $9.99
          • Mango Sorbet — $6.49
          • Fresh Lemonade — $4.49
          Would you like to order any of these?
----------------------------------------
👤 You:   What are the calories in the Dragon Noodles?
🔥 Ember: The Spicy Dragon Noodles have 590 calories per serving. 🍜
          They also have 22g protein, 78g carbs, and 18g fat.
          Note: they are VERY spicy! 🌶️
----------------------------------------
👤 You:   Are you open today?
🔥 Ember: Today is Monday so unfortunately we are closed. 😔
          We reopen Tuesday from 12:00 PM. See you then! 🔥
----------------------------------------
👤 You:   I want to order 2 Crispy Tofu Bites
🔥 Ember: Great choice! 🤩 Would you like that for delivery or dine-in?
```

---

## 📊 Knowledge Base Stats

```
Source files:      2 (1 PDF + 1 Excel)
Total documents:   76
After chunking:    74 chunks
Avg chunk size:    45 tokens
Embedding model:   gemini-embedding-001 (768 dimensions)
Vector store:      ChromaDB (local, persistent)
```

---

## 🔄 Data Formats Handled

| Format | Source | Documents | Chunking Strategy |
|---|---|---|---|
| Plain text | PDF Page 1, 4 | 8 | Sentence split |
| Key-value table | PDF Page 1, 2 | 2 | Passthrough |
| Structured table | PDF Page 2, 3 | 21 | Passthrough (1 row = 1 doc) |
| Q&A pairs | PDF Page 3 | 6 | Passthrough |
| Inline structured | PDF Page 5 | 1 | Passthrough |
| Excel rows | Excel 3 sheets | 33 | Passthrough |

---

## 🚀 Production Deployment

To move from sandbox to production:

1. **WhatsApp Business API** — apply at business.whatsapp.com (free up to 1000 conversations/month via Meta)
2. **Deploy to Railway** — push to GitHub, connect Railway, set env vars, done
3. **Persistent sessions** — replace in-memory `ChatSession` dict with Redis
4. **Order storage** — save confirmed orders to Supabase or Google Sheets
5. **Monitoring** — add logging to track which questions the bot can't answer

---

## 👨‍💻 Author

Built as a portfolio project demonstrating production RAG pipeline development.

**Skills demonstrated:**
- RAG pipeline architecture
- Multi-format document processing
- Vector database integration
- LLM prompt engineering
- WhatsApp chatbot development
- FastAPI webhook development
- Error handling and rate limit management

---

## 📄 License

MIT — free to use, modify, and distribute.
>>>>>>> 8ddd03b912c09c9e76794550857d4824eafd05ae
