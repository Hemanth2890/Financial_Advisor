"""
RAG-based memory retrieval for the financial advisor.

Each advisory session's profile + analysis is summarized into a short
text description and embedded with fastembed (BAAI/bge-small-en-v1.5,
ONNX runtime, no GPU). When a new session comes in, the system embeds
its own summary and retrieves the most similar past sessions via
pgvector (or numpy cosine similarity on SQLite), giving the
recommendation agent real prior context -- e.g. "a similar profile was
advised X before" -- rather than treating every request as stateless.
"""
from __future__ import annotations

import time

import numpy as np
from fastembed import TextEmbedding

from db.models import SessionLocal, AdvisorySession, USE_PGVECTOR, deserialize_embedding

_model = None


def _get_model() -> TextEmbedding:
    global _model
    if _model is None:
        _model = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")
    return _model


def embed_text(text: str) -> np.ndarray:
    model = _get_model()
    embedding = next(model.embed([text]))
    return np.asarray(embedding, dtype=np.float32)


def summarize_profile(profile: dict, analysis: dict) -> str:
    return (
        f"Monthly income {profile['income']}, total expenses "
        f"{analysis['total_expenses']}, savings rate "
        f"{analysis['savings_rate_pct']} percent, savings goal "
        f"{profile['savings_goal']}, months to goal "
        f"{analysis.get('months_to_goal')}."
    )


def retrieve_similar_sessions(summary_text: str, user_id: str | None = None,
                               top_k: int = 3) -> dict:
    """Embed the current session summary and retrieve the most similar
    past sessions (optionally scoped to a user). Returns retrieved
    summaries plus measured retrieval latency."""
    query_embedding = embed_text(summary_text)

    db = SessionLocal()
    try:
        start = time.perf_counter()

        if USE_PGVECTOR:
            q = db.query(AdvisorySession).filter(
                AdvisorySession.summary_embedding.isnot(None)
            )
            if user_id:
                q = q.filter(AdvisorySession.user_id == user_id)
            results = (
                q.order_by(AdvisorySession.summary_embedding.cosine_distance(query_embedding))
                .limit(top_k)
                .all()
            )
            matches = [
                {"session_id": r.id, "summary": summarize_profile(r.profile, r.analysis),
                 "recommendation": r.recommendation,
                 "similarity": _cosine_sim(query_embedding,
                                            np.asarray(r.summary_embedding, dtype=np.float32))}
                for r in results
            ]
        else:
            q = db.query(AdvisorySession).filter(
                AdvisorySession.summary_embedding.isnot(None)
            )
            if user_id:
                q = q.filter(AdvisorySession.user_id == user_id)
            all_sessions = q.all()
            scored = []
            for s in all_sessions:
                vec = np.asarray(deserialize_embedding(s.summary_embedding), dtype=np.float32)
                sim = _cosine_sim(query_embedding, vec)
                scored.append((sim, s))
            scored.sort(key=lambda t: t[0], reverse=True)
            matches = [
                {"session_id": s.id, "summary": summarize_profile(s.profile, s.analysis),
                 "recommendation": s.recommendation, "similarity": round(float(sim), 4)}
                for sim, s in scored[:top_k]
            ]

        elapsed_ms = (time.perf_counter() - start) * 1000
        return {"matches": matches, "retrieval_latency_ms": round(elapsed_ms, 3),
                "backend": "pgvector" if USE_PGVECTOR else "numpy_fallback"}
    finally:
        db.close()


def _cosine_sim(a: np.ndarray, b: np.ndarray) -> float:
    denom = np.linalg.norm(a) * np.linalg.norm(b)
    if denom == 0:
        return 0.0
    return round(float(np.dot(a, b) / denom), 4)
