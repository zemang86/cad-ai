"""FastAPI web API and UI for AutoCAD Batch Commander."""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field

from autocad_batch_commander import __version__
from autocad_batch_commander.knowledge.loader import query_knowledge_base
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
    return {"status": "ok", "version": __version__}


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


# ── Web UI ───────────────────────────────────────────────────────


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})
