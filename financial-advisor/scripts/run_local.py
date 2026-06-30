"""
Local end-to-end test, no Docker/Redis/Postgres required (Celery runs
in eager mode, SQLite for storage).

Usage:
    PYTHONPATH=. CELERY_TASK_ALWAYS_EAGER=true python scripts/run_local.py
"""
from __future__ import annotations

import json

from tasks.celery_app import run_advisory_task

PROFILE_1 = {
    "income": 80000, "rent": 25000, "food": 8000, "subscriptions": 2000,
    "transport": 5000, "insurance": 3000, "investments": 10000,
    "savings_goal": 500000,
}

PROFILE_2 = {
    "income": 82000, "rent": 26000, "food": 8500, "subscriptions": 2200,
    "transport": 5200, "insurance": 3100, "investments": 9500,
    "savings_goal": 480000,
}


def main():
    print("=== Session 1 (no prior memory) ===")
    r1 = run_advisory_task.apply(args=[PROFILE_1, "demo_user"])
    print(json.dumps(r1.result, indent=2))

    print("\n=== Session 2 (should retrieve session 1 from RAG memory) ===")
    r2 = run_advisory_task.apply(args=[PROFILE_2, "demo_user"])
    print(json.dumps(r2.result, indent=2))


if __name__ == "__main__":
    main()
