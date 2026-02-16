# 🔥 Spice & Ember WhatsApp RAG Chatbot

A production-ready WhatsApp chatbot powered by Retrieval-Augmented Generation (RAG) that answers questions about restaurant menu, pricing, dietary information, and handles orders/bookings.

## 🎯 Features

- **RAG Pipeline**: Uses ChromaDB vector store + Google Gemini 2.5 Flash for intelligent responses
- **Multi-format Data**: Processes PDF menus and Excel spreadsheets
- **Conversation Memory**: Maintains context across multi-turn conversations
- **WhatsApp Integration**: Real-time messaging via Twilio API
- **Smart Retrieval**: Hybrid search with query expansion for better accuracy
- **Production Ready**: Deployed on Render.com with proper error handling

## 🏗️ Architecture

```
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
