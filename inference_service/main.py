"""
Inference API — owned by M2 (LLM / Inference Engineer)

Contract (from team blueprint, Interface: M2 -> M1/M4):
    model_id + messages/images + config -> response + usage metadata

Wraps local Ollama server on http://localhost:11434.
Run:
    ..\venv\Scripts\python.exe -m uvicorn main:app --reload --port 8001
"""

import time
import base64
import re
from typing import List, Optional, Literal

import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

OLLAMA_BASE_URL = "http://localhost:11434"

app = FastAPI(title="Sovereign Workbench - Inference API", version="0.1.0")


# ---------- Contract schemas ----------

class Message(BaseModel):
    role: Literal["system", "user", "assistant"]
    content: str
    images: Optional[List[str]] = None  # Base64 encoded strings


class GenerateConfig(BaseModel):
    temperature: float = 0.2
    max_tokens: int = 1024
    top_p: float = 0.9


class GenerateRequest(BaseModel):
    model_config = {"protected_namespaces": ()}

    model_id: str  # e.g. "qwen3:4b-instruct-2507-q4_K_M", "qwen3:4b", "gemma3:4b"
    messages: List[Message]
    config: GenerateConfig = GenerateConfig()


class Usage(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    latency_ms: int


class GenerateResponse(BaseModel):
    model_config = {"protected_namespaces": ()}

    model_id: str
    response: str
    usage: Usage


# Registered available local models
REGISTERED_MODELS = {
    "qwen3:4b-instruct-2507-q4_K_M": {"role": "reasoning", "multimodal": False},
    "qwen3:4b": {"role": "reasoning", "multimodal": False},
    "qwen3-coder:7b": {"role": "coding", "multimodal": False},
    "gemma3:4b": {"role": "vision-language", "multimodal": True},
}


def strip_thinking(text: str) -> str:
    """Remove any <think>...</think> block from reasoning models."""
    return re.sub(r"<think>.*?</think>\s*", "", text, flags=re.DOTALL).strip()


@app.get("/models")
def list_models():
    """Router (M1) calls this to know available models."""
    return {"models": REGISTERED_MODELS}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/generate", response_model=GenerateResponse)
async def generate(req: GenerateRequest):
    if req.model_id not in REGISTERED_MODELS:
        raise HTTPException(
            status_code=400,
            detail=f"model_id '{req.model_id}' is not registered. Available: {list(REGISTERED_MODELS.keys())}"
        )

    ollama_messages = []
    for m in req.messages:
        entry = {"role": m.role, "content": m.content}
        if m.images:
            entry["images"] = m.images
        ollama_messages.append(entry)

    payload = {
        "model": req.model_id,
        "messages": ollama_messages,
        "stream": False,
        "think": False,  # Turn off reasoning pass for low latency on CPU
        "options": {
            "temperature": req.config.temperature,
            "num_predict": req.config.max_tokens,
            "top_p": req.config.top_p,
        },
    }

    start = time.time()
    async with httpx.AsyncClient(timeout=300) as client:
        try:
            r = await client.post(f"{OLLAMA_BASE_URL}/api/chat", json=payload)
            r.raise_for_status()
        except httpx.HTTPError as e:
            raise HTTPException(status_code=502, detail=f"Ollama call failed: {e}")

    data = r.json()
    latency_ms = int((time.time() - start) * 1000)

    raw_content = data.get("message", {}).get("content", "")
    clean_content = strip_thinking(raw_content)

    return GenerateResponse(
        model_id=req.model_id,
        response=clean_content,
        usage=Usage(
            prompt_tokens=data.get("prompt_eval_count", 0),
            completion_tokens=data.get("eval_count", 0),
            latency_ms=latency_ms,
        ),
    )


def encode_image_to_base64(path: str) -> str:
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")
