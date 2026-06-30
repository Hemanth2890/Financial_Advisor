"""
FastAPI service for the agentic financial advisory platform.

Endpoints:
  POST /advise          kicks off an async Celery task running the full
                         LangGraph pipeline (categorize -> analyze ->
                         retrieve_memory -> recommend), returns task_id
  GET  /advise/status/{task_id}   Celery task state
  GET  /advise/result/{task_id}   full pipeline output once complete
  GET  /history/{user_id}         past sessions for a user
  GET  /health
"""
from __future__ import annotations

from celery.result import AsyncResult
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from db.models import init_db, SessionLocal, AdvisorySession
from tasks.celery_app import celery_app, run_advisory_task

app = FastAPI(
    title="Agentic Financial Advisory API",
    description="LangGraph-orchestrated multi-agent financial advisory "
                 "platform with FastAPI, Celery/Redis async execution, "
                 "and pgvector-based RAG memory retrieval.",
    version="1.0.0",
)


@app.on_event("startup")
def on_startup():
    init_db()


class BudgetRequest(BaseModel):
    user_id: str = "anonymous"
    income: float
    rent: float
    food: float
    subscriptions: float
    transport: float
    insurance: float
    investments: float
    savings_goal: float


@app.post("/advise")
def advise(req: BudgetRequest):
    profile = req.dict(exclude={"user_id"})
    async_result = run_advisory_task.delay(profile, req.user_id)
    return {"task_id": async_result.id, "status": "submitted"}


@app.get("/advise/status/{task_id}")
def advise_status(task_id: str):
    result = AsyncResult(task_id, app=celery_app)
    return {"task_id": task_id, "state": result.state}


@app.get("/advise/result/{task_id}")
def advise_result(task_id: str):
    result = AsyncResult(task_id, app=celery_app)
    if result.state != "SUCCESS":
        return {"task_id": task_id, "state": result.state}
    return result.result


@app.get("/history/{user_id}")
def history(user_id: str):
    db = SessionLocal()
    try:
        sessions = (
            db.query(AdvisorySession)
            .filter(AdvisorySession.user_id == user_id)
            .order_by(AdvisorySession.created_at.desc())
            .all()
        )
        return [
            {"session_id": s.id, "task_id": s.task_id, "status": s.status,
             "savings_rate_pct": (s.analysis or {}).get("savings_rate_pct"),
             "created_at": s.created_at.isoformat() if s.created_at else None}
            for s in sessions
        ]
    finally:
        db.close()


@app.get("/health")
def health():
    return {"status": "ok"}
