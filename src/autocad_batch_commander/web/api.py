"""FastAPI web API and UI for AutoCAD Batch Commander."""

from __future__ import annotations

import json
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from autocad_batch_commander import __version__
from autocad_batch_commander.config import settings
from autocad_batch_commander.knowledge.loader import load_ubbl_content, query_knowledge_base
from autocad_batch_commander.operations.compliance_ops import (
    check_compliance,
    list_rule_sets,
    load_rule_set,
)
from autocad_batch_commander.models import ComplianceCheckRequest

# ── App setup ────────────────────────────────────────────────────

app = FastAPI(
    title="AutoCAD Batch Commander API",
    description="Malaysian building regulation knowledge base and compliance checking",
    version=__version__,
)

_template_dir = Path(__file__).parent / "templates"
templates = Jinja2Templates(directory=str(_template_dir))


# ── Request / response models ───────────────────────────────────


class QueryRequest(BaseModel):
    question: str


class QueryResponse(BaseModel):
    query: str
    files_loaded: int
    results: dict[str, str]


# ── Endpoints ────────────────────────────────────────────────────


@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "version": __version__,
        "chat_enabled": settings.chat_enabled,
    }


@app.post("/api/query", response_model=QueryResponse)
def query(request: QueryRequest):
    results = query_knowledge_base(request.question)
    return QueryResponse(
        query=request.question,
        files_loaded=len(results),
        results=results,
    )


@app.get("/api/rules")
def rules():
    return {"rule_sets": list_rule_sets()}


@app.get("/api/rules/{rule_set}")
def rule_set_detail(rule_set: str):
    rs = load_rule_set(rule_set)
    return rs.model_dump()


@app.post("/api/compliance/check")
def compliance_check(request: ComplianceCheckRequest):
    result = check_compliance(request)
    return result.model_dump()


@app.get("/api/ubbl")
def get_ubbl_content():
    return load_ubbl_content()


# ── Chat endpoints ──────────────────────────────────────────────


def _require_chat():
    """Guard: raise 503 if chat is not enabled."""
    if not settings.chat_enabled:
        raise HTTPException(status_code=503, detail="Chat feature is not enabled")


@app.post("/api/chat/session")
def create_session(body: dict):
    """Create or register a chat session with consent."""
    from autocad_batch_commander.chat.models import SessionConsentRequest
    from autocad_batch_commander.chat.client import get_supabase

    _require_chat()
    req = SessionConsentRequest(**body)

    supabase = get_supabase()
    supabase.table("chat_sessions").upsert(
        {
            "id": req.session_id,
            "consent_given": req.consent_given,
            "user_agent": req.user_agent,
        }
    ).execute()

    return {"session_id": req.session_id, "status": "ok"}


@app.post("/api/chat")
async def chat(body: dict):
    """Send a chat message and receive a streamed SSE response."""
    from autocad_batch_commander.chat.models import ChatRequest
    from autocad_batch_commander.chat.rag import generate_chat_response

    _require_chat()
    req = ChatRequest(**body)

    async def event_stream():
        async for event in generate_chat_response(
            session_id=req.session_id,
            message=req.message,
            history=req.conversation_history,
        ):
            yield f"data: {json.dumps(event)}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@app.post("/api/feedback")
def submit_feedback(body: dict):
    """Submit thumbs up/down feedback on an assistant message."""
    from autocad_batch_commander.chat.models import FeedbackRequest
    from autocad_batch_commander.chat.client import get_supabase

    _require_chat()
    req = FeedbackRequest(**body)

    supabase = get_supabase()
    supabase.table("feedback").upsert(
        {
            "message_id": req.message_id,
            "session_id": req.session_id,
            "rating": req.rating,
            "comment": req.comment,
        },
        on_conflict="message_id",
    ).execute()

    return {"status": "ok"}


# ── Web UI ───────────────────────────────────────────────────────


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})
