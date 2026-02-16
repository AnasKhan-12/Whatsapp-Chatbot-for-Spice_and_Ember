"""
06_whatsapp_bot.py — Step 6: WhatsApp Integration via Twilio

WHAT THIS FILE TEACHES YOU:
- How to set up a FastAPI webhook for Twilio WhatsApp
- How Twilio sends messages to your server
- How to reply back through Twilio's API
- How to deploy this (ngrok for local testing → Railway for production)

HOW TWILIO WHATSAPP WORKS:
  User sends WhatsApp message
        ↓
  Twilio receives it
        ↓
  Twilio sends HTTP POST to YOUR webhook URL
        ↓
  Your FastAPI server processes it with RAG
        ↓
  Your server replies to Twilio API
        ↓
  Twilio sends reply back to user on WhatsApp

SETUP STEPS:
  1. Create Twilio account → get free sandbox number
  2. Install ngrok → run: ngrok http 8000
  3. Set webhook URL in Twilio: https://your-ngrok-url.ngrok.io/webhook
  4. Run: python 06_whatsapp_bot.py
  5. Send "join <sandbox-word>" to Twilio's sandbox number on WhatsApp

DEPLOY TO PRODUCTION:
  1. Push code to GitHub
  2. Deploy to Railway (railway.app) — free tier works
  3. Set environment variables (OPENAI_API_KEY, TWILIO_*)
  4. Update Twilio webhook URL to your Railway URL
"""
import startup
import os
from fastapi import FastAPI, Form, Response
from twilio.rest import Client
from twilio.twiml.messaging_response import MessagingResponse
from dotenv import load_dotenv

from rag_chain import ChatSession

load_dotenv()

# ── TWILIO CONFIG ──────────────────────────────────────────────────────────────
# Add these to your .env file:
# TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxx
# TWILIO_AUTH_TOKEN=your_auth_token
# TWILIO_WHATSAPP_NUMBER=whatsapp:+14155238886  ← Twilio sandbox number

TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_WHATSAPP_NUMBER = os.getenv("TWILIO_WHATSAPP_NUMBER")

twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

# ── FASTAPI APP ────────────────────────────────────────────────────────────────
app = FastAPI(title="Spice & Ember WhatsApp Bot")

# One session manager for all users (in memory)
# In production: use Redis so sessions survive server restarts
session_manager = ChatSession()


# ── WEBHOOK ENDPOINT ───────────────────────────────────────────────────────────
# @app.post("/webhook")
# async def whatsapp_webhook(
#     From: str = Form(...),       # Sender's WhatsApp number e.g. "whatsapp:+1234567890"
#     Body: str = Form(...),       # Message text
#     NumMedia: int = Form(0),     # Number of media attachments (images, docs)
# ):
#     """
#     Twilio calls this endpoint every time a user sends a WhatsApp message.

#     Form fields sent by Twilio:
#     - From:       sender's number ("whatsapp:+1234567890")
#     - To:         your Twilio number
#     - Body:       message text
#     - NumMedia:   how many attachments
#     - MediaUrl0:  URL of first attachment (if any)
#     """
#     user_id = From  # use phone number as session key
#     message = Body.strip()

#     print(f"\n📱 Message from {user_id}: {message}")

#     # ── Handle special commands ──
#     if message.lower() in ["reset", "start over", "restart", "hi", "hello", "start"]:
#         if message.lower() in ["reset", "start over", "restart"]:
#             response_text = session_manager.reset(user_id)
#         else:
#             response_text = (
#                 "Welcome to Spice & Ember! 🔥\n\n"
#                 "I'm Ember, your personal assistant. I can help you with:\n"
#                 "🍽 Our menu & prices\n"
#                 "🥗 Dietary & allergy info\n"
#                 "🛵 Placing a delivery order\n"
#                 "📅 Booking a table\n"
#                 "🕐 Opening hours\n\n"
#                 "What can I help you with today?"
#             )
#     else:
#         # Run the full RAG pipeline
#         response_text = session_manager.chat(user_id, message)

#     print(f"🤖 Response: {response_text[:100]}...")

#     # ── Build TwiML response ──
#     # TwiML = Twilio Markup Language — XML format Twilio uses for responses
#     twiml = MessagingResponse()
#     twiml.message(response_text)

#     return Response(content=str(twiml), media_type="application/xml")

@app.post("/webhook")
async def whatsapp_webhook(
    From: str = Form(...),
    Body: str = Form(...),
    NumMedia: int = Form(0),
):
    user_id = From
    message = Body.strip()

    print(f"📱 Message from {user_id}: {message}")

    response_text = session_manager.chat(user_id, message)

    print(f"🔥 Ember: {response_text}")

    twiml = MessagingResponse()
    twiml.message(response_text)

    return Response(content=str(twiml), media_type="application/xml")


# ── HEALTH CHECK ───────────────────────────────────────────────────────────────
# @app.get("/")
# async def health_check():
#     return {
#         "status": "running",
#         "bot": "Spice & Ember WhatsApp Bot",
#         "active_sessions": len(session_manager.sessions)
#     }

@app.get("/webhook")
async def webhook_verify():
    return Response(content="OK", status_code=200)


# ── ALTERNATIVE: SEND PROACTIVE MESSAGES ──────────────────────────────────────
def send_whatsapp_message(to_number: str, message: str):
    """
    Send a proactive message (not a reply).
    Use case: order confirmation, booking reminder, delivery update.

    to_number format: "+1234567890" (without "whatsapp:" prefix)
    """
    twilio_client.messages.create(
        from_=TWILIO_WHATSAPP_NUMBER,
        to=f"whatsapp:{to_number}",
        body=message
    )
    print(f"✅ Message sent to {to_number}")


# ── RUN ───────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting Spice & Ember WhatsApp Bot...")
    print("   Webhook URL: http://localhost:8000/webhook")
    print("   For local testing: ngrok http 8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)
