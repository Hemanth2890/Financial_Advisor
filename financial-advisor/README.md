# Agentic Financial Advisory Platform

A multi-agent financial advisory system that analyzes a monthly budget, classifies spending into essential and discretionary categories, retrieves context from similar past advisory sessions, and generates personalized savings recommendations. The pipeline is orchestrated with LangGraph and served through a FastAPI backend, with Celery and Redis handling asynchronous execution and PostgreSQL with pgvector providing RAG-based memory of prior sessions.

## Overview

Generic budgeting advice tends to ignore two things: how a person's specific spending compares to reasonable benchmarks for their income, and whether anything similar has come up before. This platform addresses both. A categorization agent flags spending categories that look high relative to income, an analysis agent computes exact savings metrics, and a recommendation agent uses Gemini 2.0 Flash to write advice that is grounded in both the current numbers and relevant prior sessions retrieved through vector search.

## Architecture

```
Client --> FastAPI /advise --> Celery task --> LangGraph pipeline
                                                    |
                  PostgreSQL (pgvector) <-- AdvisorySession
                                                    |
                                      analyze -> categorize -> retrieve_memory
                                                              -> recommend (Gemini)
```

### Agents

- `FinancialAnalysisAgent` - computes total expenses, monthly savings, savings rate, and months to reach the savings goal. Pure arithmetic, no LLM call, so the numbers are always exact.
- `TransactionCategorizationAgent` - classifies budget categories into essential and discretionary spending and flags any category that exceeds a standard income-based benchmark (e.g. rent above 35 percent of income). Operates on category-level budget inputs (rent, food, subscriptions, transport, insurance, investments); it does not ingest individual transaction line items, since the platform does not currently accept itemized transaction data.
- `SavingsRecommendationAgent` - generates the final advice with Gemini 2.0 Flash, conditioned on the analysis, the categorization flags, and similar past sessions retrieved via RAG. Falls back to a template-based recommendation if no API key is configured, clearly labeled in the response.

### Infrastructure

- `api/main.py` - FastAPI service: `POST /advise`, `GET /advise/status/{id}`, `GET /advise/result/{id}`, `GET /history/{user_id}`.
- `tasks/celery_app.py` - Celery task wrapping the full LangGraph pipeline and persisting the session and its embedding, run in a background worker so the API returns immediately.
- `rag/memory.py` - generates real semantic embeddings with `fastembed` (BAAI/bge-small-en-v1.5, ONNX runtime, no GPU required) for each session summary, and retrieves the most similar past sessions via pgvector cosine distance (or an in-process numpy fallback for local SQLite development).
- `db/models.py` - SQLAlchemy `AdvisorySession` table storing the budget profile, analysis, categorization, recommendation, and embedding for each session.

## Setup

### 1. Configure Gemini

```bash
export GEMINI_API_KEY="..."
```

Without this, recommendations fall back to a template built from the deterministic analysis and categorization flags rather than failing; the response is labeled accordingly.

### 2. Local run (no Docker, no Redis, no Postgres)

```bash
pip install -r requirements.txt
PYTHONPATH=. CELERY_TASK_ALWAYS_EAGER=true python scripts/run_local.py
```

This runs two sessions for the same user back to back; the second should retrieve the first from RAG memory. The first run downloads the embedding model from Hugging Face (a few hundred MB, one-time).

### 3. Full stack (API, Celery worker, Redis, Postgres with pgvector)

```bash
docker compose up --build
curl -X POST localhost:8002/advise -H "Content-Type: application/json" \
  -d '{"user_id": "demo", "income": 80000, "rent": 25000, "food": 8000, "subscriptions": 2000, "transport": 5000, "insurance": 3000, "investments": 10000, "savings_goal": 500000}'
curl localhost:8002/advise/status/<task_id>
curl localhost:8002/advise/result/<task_id>
```

## API Reference

| Endpoint | Method | Description |
|---|---|---|
| `/advise` | POST | Submit a budget profile, kicks off the async advisory pipeline |
| `/advise/status/{task_id}` | GET | Celery task state |
| `/advise/result/{task_id}` | GET | Full pipeline output: analysis, categorization, retrieved sessions, recommendation |
| `/history/{user_id}` | GET | Past sessions for a user |
| `/health` | GET | Health check |

## Project Structure

```
agents/
  analysis_agent.py        deterministic budget arithmetic
  categorization_agent.py  category-level essential/discretionary classification and benchmarking
  recommendation_agent.py  Gemini-based recommendation generation, with fallback
  graph.py                 LangGraph StateGraph orchestrating all three agents
api/
  main.py                  FastAPI service
tasks/
  celery_app.py            async pipeline execution and session persistence
rag/
  memory.py                session embedding and pgvector/numpy similarity retrieval
db/
  models.py                SQLAlchemy models
scripts/
  run_local.py             local end-to-end test runner
Dockerfile
docker-compose.yml
requirements.txt
```

## License

MIT
