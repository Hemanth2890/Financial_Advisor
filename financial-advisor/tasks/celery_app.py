"""
Celery task wrapping the full LangGraph advisory pipeline, so the
FastAPI endpoint returns immediately with a task_id rather than
blocking on the LLM call and embedding generation.
"""
from __future__ import annotations

import os
import datetime as dt

from celery import Celery

from db.models import SessionLocal, AdvisorySession, init_db, serialize_embedding
from agents.graph import run_advisory_pipeline
from rag.memory import embed_text, summarize_profile

REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
ALWAYS_EAGER = os.environ.get("CELERY_TASK_ALWAYS_EAGER", "false").lower() == "true"

celery_app = Celery("financial_advisor_tasks", broker=REDIS_URL, backend=REDIS_URL)
celery_app.conf.task_always_eager = ALWAYS_EAGER
celery_app.conf.task_serializer = "json"
celery_app.conf.result_serializer = "json"
celery_app.conf.accept_content = ["json"]


@celery_app.task(bind=True, name="tasks.run_advisory")
def run_advisory_task(self, profile: dict, user_id: str = "anonymous"):
    init_db()
    db = SessionLocal()
    task_id = self.request.id or "eager-run"

    session = AdvisorySession(task_id=task_id, user_id=user_id, profile=profile,
                               status="running")
    db.add(session)
    db.commit()

    try:
        result = run_advisory_pipeline(profile, user_id=user_id)

        summary = summarize_profile(profile, result["analysis"])
        embedding = embed_text(summary)

        session.analysis = result["analysis"]
        session.categorization = result["categorization"]
        session.recommendation = result["recommendation"]
        session.summary_embedding = serialize_embedding(embedding)
        session.status = "completed"
        db.commit()

        return result
    except Exception:
        session.status = "failed"
        db.commit()
        raise
    finally:
        db.close()
