import os
import re
import time
from typing import List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# ── LLM provider ─────────────────────────────────────────────────────────────
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "groq").lower()
GROQ_MODEL = os.getenv("CHATBOT_MODEL", "llama-3.1-8b-instant")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

try:
    from groq import Groq
except ImportError:
    Groq = None

SYSTEM_PROMPT = """You are ShopBot, the customer support assistant for ShopSphere — a mid-sized e-commerce store that sells electronics, apparel, and home goods.

You answer questions about orders, refunds, shipping, returns, accounts, and products using ONLY the policies and product info below. If a question is outside this scope, say so politely and suggest contacting human support at support@shopsphere.com.

== POLICIES ==

RETURN POLICY
- Customers have 30 days from the delivery date to return most items.
- Items must be in original condition with original packaging and proof of purchase.
- Non-returnable: underwear/intimate apparel, personalized products, final-sale items, perishable goods, gift cards.
- Return shipping is FREE for defective or wrong items; buyer pays for all other reasons.

REFUND POLICY
- Refunds processed within 7 business days of receiving the returned item.
- Refunds issued to original payment method; original shipping costs non-refundable unless our error.
- Digital goods are non-refundable once downloaded.

SHIPPING POLICY
- Standard: 5-7 business days inside the US (free on orders over $50, otherwise $4.99).
- Express: 2-3 business days ($9.99).
- Overnight: next business day if ordered before 12pm ET ($24.99).
- International: 10-14 business days; customs fees are buyer's responsibility.

ACCOUNT
- Reset password at shopsphere.com/account/reset.
- Order history under "My Orders" after sign-in.
- To delete your account, email privacy@shopsphere.com.

PAYMENT METHODS
- Accepted: Visa, Mastercard, Amex, Discover, PayPal, Apple Pay, Google Pay, ShopSphere Gift Cards.
- Cryptocurrency NOT accepted.

== PRODUCT CATALOG ==
- SKU SP-EARBUDS-01: Wireless Earbuds, $79, Bluetooth 5.3, 30hr battery, IPX4.
- SKU SP-HOODIE-CL: Classic Hoodie, $49, 80% cotton/20% polyester, sizes XS-XXL.
- SKU SP-MUG-CER: Ceramic Mug 12oz, $14, dishwasher-safe.
- SKU SP-LAMP-LED: LED Desk Lamp, $39, 3 brightness levels, USB-C.

== RULES ==
1. Be concise (under 120 words per reply).
2. Quote exact numbers and timeframes from policies — never invent figures.
3. If asked about a SKU not listed, say: "I don't have information on that product."
"""


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    message: str
    history: Optional[List[ChatMessage]] = None


class ChatResponse(BaseModel):
    reply: str
    model: str
    mode: str


app = FastAPI(title="ShopSphere Chatbot", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {"status": "ok", "service": "ShopSphere Chatbot API", "endpoints": ["/health", "/chat"]}


@app.get("/health")
def health():
    return {
        "status": "ok",
        "model": GROQ_MODEL,
        "provider": LLM_PROVIDER,
        "groq_configured": bool(GROQ_API_KEY),
    }


def _mock_reply(msg: str) -> str:
    return (
        "[mock mode — set GROQ_API_KEY] "
        f"You asked: '{msg}'. ShopSphere supports refunds within 30 days, "
        "free standard shipping over $50, and 24/7 email support."
    )


def _groq_retry_wait(exc: Exception) -> float:
    try:
        m = re.search(r"try again in ([\d.]+)s", str(exc))
        return float(m.group(1)) + 5 if m else 70.0
    except Exception:
        return 70.0


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    if not GROQ_API_KEY or Groq is None:
        return ChatResponse(reply=_mock_reply(req.message), model="mock", mode="mock")

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    for m in req.history or []:
        messages.append({"role": m.role, "content": m.content})
    messages.append({"role": "user", "content": req.message})

    client = Groq(api_key=GROQ_API_KEY)
    for attempt in range(3):
        try:
            completion = client.chat.completions.create(
                model=GROQ_MODEL,
                messages=messages,
                temperature=0.3,
                max_tokens=400,
            )
            return ChatResponse(
                reply=completion.choices[0].message.content,
                model=GROQ_MODEL,
                mode="live",
            )
        except Exception as e:
            is_rate_limit = "429" in str(e) or "rate_limit_exceeded" in str(e)
            if not is_rate_limit or attempt == 2:
                raise HTTPException(status_code=502, detail=f"Groq error: {e}") from e
            wait = _groq_retry_wait(e)
            time.sleep(wait)
