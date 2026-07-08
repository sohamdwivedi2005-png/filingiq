"""FastAPI app: POST /api/ask returns a cited, XBRL-verified answer; / serves UI."""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

from filingiq.llm.groq import MissingAPIKey
from filingiq.rag.answer import answer_question

WEB_DIR = Path(__file__).resolve().parents[3] / "web"

app = FastAPI(title="FilingIQ", description="Grounded, XBRL-verified Q&A over SEC filings")


class AskRequest(BaseModel):
    question: str
    ticker: str | None = None
    k: int = 6


class SourceOut(BaseModel):
    n: int
    ticker: str
    report_date: str
    item: str
    item_label: str
    chunk_index: int


class VerdictOut(BaseModel):
    raw: str
    status: str
    concept: str | None = None
    period_end: str | None = None


class AskResponse(BaseModel):
    question: str
    answer: str
    sources: list[SourceOut]
    verifications: list[VerdictOut]


@app.post("/api/ask", response_model=AskResponse)
def ask(req: AskRequest) -> AskResponse:
    if not req.question.strip():
        raise HTTPException(status_code=400, detail="question is required")
    try:
        res = answer_question(
            req.question, k=req.k, ticker=req.ticker, verify=bool(req.ticker)
        )
    except MissingAPIKey as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    return AskResponse(
        question=res.question,
        answer=res.answer,
        sources=[
            SourceOut(
                n=i,
                ticker=s["ticker"],
                report_date=s["report_date"],
                item=s["item"],
                item_label=s["item_label"],
                chunk_index=s["chunk_index"],
            )
            for i, s in enumerate(res.sources, 1)
        ],
        verifications=[
            VerdictOut(raw=v.raw, status=v.status, concept=v.concept, period_end=v.period_end)
            for v in res.verifications
        ],
    )


@app.get("/")
def index() -> FileResponse:
    return FileResponse(WEB_DIR / "index.html")
