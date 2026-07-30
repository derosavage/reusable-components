from collections import deque
from typing import Dict, List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from shared.config import settings
from .strategies import LLMOrchestrator

app = FastAPI(title="LLM Service", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=settings.CORS_ORIGINS, allow_credentials=True, allow_methods=["*"], allow_headers=["*"])


class ChatRequest(BaseModel):
    messages: List[Dict[str, str]]
    model: Optional[str] = None
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None


class EnsembleRequest(BaseModel):
    messages: List[Dict[str, str]]
    models: List[str]


_conversations: Dict[str, deque] = {}


@app.post("/chat")
async def chat(req: ChatRequest):
    try:
        strategy = LLMOrchestrator.get(req.model)
        kwargs = {}
        if req.max_tokens is not None:
            kwargs["max_tokens"] = req.max_tokens
        if req.temperature is not None:
            kwargs["temperature"] = req.temperature
        return await strategy.generate(req.messages, **kwargs)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"LLM request failed: {str(e)}")


@app.post("/ensemble")
async def ensemble(req: EnsembleRequest):
    try:
        return {"results": await LLMOrchestrator.ensemble_generate(req.messages, req.models)}
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Ensemble failed: {str(e)}")


@app.post("/conversation")
async def conversation(req: ChatRequest):
    session_id = f"conv_{hash(str(req.messages))}"
    if session_id not in _conversations:
        _conversations[session_id] = deque(maxlen=100)
    history = list(_conversations[session_id])
    strategy = LLMOrchestrator.get(req.model)
    result = await strategy.generate(history + req.messages)
    for msg in req.messages:
        _conversations[session_id].append(msg)
    choices = result.get("choices", [])
    if choices:
        _conversations[session_id].append({"role": "assistant", "content": choices[0]["message"]["content"]})
    return {"session_id": session_id, "result": result}


@app.get("/models")
def list_models():
    return {"models": list(LLMOrchestrator._models.keys())}


@app.get("/health")
def health():
    return {"status": "ok", "service": "llm"}
