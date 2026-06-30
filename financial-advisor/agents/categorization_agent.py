"""
TransactionCategorizationAgent: classifies budget categories as
essential vs. discretionary spending and flags categories that look
anomalous relative to common income-based budgeting benchmarks (e.g.
the 50/30/20 rule). Operates on the user's category-level budget
inputs (rent, food, subscriptions, etc.), not itemized line-item
transactions -- this project does not ingest a transaction-level
dataset, so "categorization" here means category-level classification
and benchmarking, not per-transaction merchant classification.
"""
from __future__ import annotations

from dataclasses import dataclass

ESSENTIAL_CATEGORIES = {"rent", "food", "insurance", "transport"}
DISCRETIONARY_CATEGORIES = {"subscriptions"}
SAVINGS_CATEGORIES = {"investments"}

# Rough benchmark ceilings as a percentage of income, used only to flag
# categories worth a closer look -- not hard financial rules.
BENCHMARK_CEILINGS_PCT = {
    "rent": 35.0,
    "food": 15.0,
    "subscriptions": 5.0,
    "transport": 15.0,
    "insurance": 10.0,
}


@dataclass
class CategoryFlag:
    category: str
    pct_of_income: float
    benchmark_pct: float
    status: str  # "within_range" | "above_benchmark"


@dataclass
class CategorizationResult:
    essential_total_pct: float
    discretionary_total_pct: float
    savings_total_pct: float
    flags: list[CategoryFlag]


class TransactionCategorizationAgent:
    def categorize(self, expense_breakdown_pct: dict) -> CategorizationResult:
        essential_total = sum(
            expense_breakdown_pct.get(c, 0.0) for c in ESSENTIAL_CATEGORIES
        )
        discretionary_total = sum(
            expense_breakdown_pct.get(c, 0.0) for c in DISCRETIONARY_CATEGORIES
        )
        savings_total = sum(
            expense_breakdown_pct.get(c, 0.0) for c in SAVINGS_CATEGORIES
        )

        flags = []
        for category, pct in expense_breakdown_pct.items():
            ceiling = BENCHMARK_CEILINGS_PCT.get(category)
            if ceiling is None:
                continue
            status = "above_benchmark" if pct > ceiling else "within_range"
            flags.append(CategoryFlag(
                category=category, pct_of_income=pct,
                benchmark_pct=ceiling, status=status,
            ))

        return CategorizationResult(
            essential_total_pct=round(essential_total, 2),
            discretionary_total_pct=round(discretionary_total, 2),
            savings_total_pct=round(savings_total, 2),
            flags=flags,
        )
