import os
import re
import time
import traceback
from typing import List, Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "groq").lower()
GROQ_MODEL = os.getenv("CHATBOT_MODEL", "llama-3.1-8b-instant")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

try:
    from groq import Groq
except ImportError:
    Groq = None

SYSTEM_PROMPT = """You are ShopBot, the customer support assistant for ShopSphere.

RETURN POLICY: 30 days from delivery, original condition. Non-returnable: underwear, personalized, final-sale, perishable, gift cards. Return shipping FREE for defective/wrong items; buyer pays otherwise.

REFUND POLICY: Processed within 7 business days of receiving item. Issued to original payment method. Digital goods non-refundable once downloaded.

SHIPPING: Standard 5-7 days (free over $50, else $4.99). Express 2-3 days ($9.99). Overnight next day if before 12pm ET ($24.99). International 10-14 days.

ACCOUNT: Reset password at shopsphere.com/account/reset. Delete account: email privacy@shopsphere.com.

PAYMENT: Visa, Mastercard, Amex, Discover, PayPal, Apple Pay, Google Pay, Gift Cards. No crypto.

PRODUCTS: SP-EARBUDS-01 $79 | SP-HOODIE-CL $49 | SP-MUG-CER $14 | SP-LAMP-LED $39

Be concise (under 120 words). Quote exact figures. Unknown SKUs: say you don't have info."""


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


@app.post("/chat")
def chat(req: ChatRequest):
    try:
        if not GROQ_API_KEY or Groq is None:
            return {"reply": f"[mock] You asked: {req.message}. ShopSphere offers 30-day returns and free shipping over $50.", "model": "mock", "mode": "mock"}

        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        for m in req.history or []:
            messages.append({"role": m.role, "content": m.content})
        messages.append({"role": "user", "content": req.message})

        client = Groq(api_key=GROQ_API_KEY, timeout=8.0)
        completion = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=messages,
            temperature=0.3,
            max_tokens=300,
        )
        return {
            "reply": completion.choices[0].message.content,
            "model": GROQ_MODEL,
            "mode": "live",
        }
    except Exception as e:
        return {
            "reply": f"[error] {type(e).__name__}: {str(e)[:200]}",
            "model": "error",
            "mode": "error",
        }
