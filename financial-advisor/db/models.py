"""
Database layer for advisory session history and RAG memory. Uses
Postgres with pgvector in production, SQLite locally with a numpy
cosine-similarity fallback for retrieval, same pattern as the other
projects in this portfolio.
"""
from __future__ import annotations

import os
import json
import datetime as dt

from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, JSON
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./financial_advisor.db")
USE_PGVECTOR = DATABASE_URL.startswith("postgresql")

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {},
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()

if USE_PGVECTOR:
    from pgvector.sqlalchemy import Vector
    EMBEDDING_COLUMN_TYPE = Vector(384)
else:
    EMBEDDING_COLUMN_TYPE = JSON


class AdvisorySession(Base):
    __tablename__ = "advisory_sessions"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(String, unique=True, index=True)
    user_id = Column(String, index=True, default="anonymous")
    profile = Column(JSON)            # raw budget profile input
    analysis = Column(JSON)           # FinancialAnalysisAgent output
    categorization = Column(JSON)     # TransactionCategorizationAgent output
    recommendation = Column(String)   # final LLM-generated advice
    summary_embedding = Column(EMBEDDING_COLUMN_TYPE, nullable=True)
    status = Column(String, default="pending")
    created_at = Column(DateTime, default=dt.datetime.utcnow)


def init_db():
    if USE_PGVECTOR:
        with engine.connect() as conn:
            conn.exec_driver_sql("CREATE EXTENSION IF NOT EXISTS vector;")
            conn.commit()
    Base.metadata.create_all(bind=engine)


def get_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def serialize_embedding(vec):
    if USE_PGVECTOR:
        return vec
    return json.dumps(list(map(float, vec)))


def deserialize_embedding(value):
    if USE_PGVECTOR:
        return value
    return json.loads(value) if isinstance(value, str) else value
