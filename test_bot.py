import requests

def chat(message, phone="+923001234567"):
    response = requests.post(
        "http://localhost:8000/webhook",
        data={
            "From": f"whatsapp:{phone}",
            "Body": message,
            "NumMedia": "0"
        }
    )
    # Extract just the message text from TwiML response
    # Response looks like: <Response><Message>text here</Message></Response>
    import re
    match = re.search(r"<Message>(.*?)</Message>", response.text, re.DOTALL)
    reply = match.group(1) if match else response.text
    print(f"👤 You:   {message}")
    print(f"🔥 Ember: {reply}")
    print("-" * 40)

# Test full conversation
chat("Hi!")
chat("Are you open today?")
chat("Do you have vegan options?")
chat("Tell me about the ribeye steak")
chat("I want to order 2 Crispy Tofu Bites for delivery")
chat("My address is 10 Main St New York")