"""
FinancialAnalysisAgent: computes deterministic financial metrics from
a monthly budget profile. No LLM call here -- this is the kind of
arithmetic that should be exact, not generated.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict


@dataclass
class BudgetProfile:
    income: float
    rent: float
    food: float
    subscriptions: float
    transport: float
    insurance: float
    investments: float
    savings_goal: float


@dataclass
class FinancialAnalysis:
    total_expenses: float
    monthly_savings: float
    savings_rate_pct: float
    months_to_goal: float | None
    expense_breakdown_pct: dict


class FinancialAnalysisAgent:
    def analyze(self, profile: BudgetProfile) -> FinancialAnalysis:
        expense_fields = ["rent", "food", "subscriptions", "transport",
                           "insurance", "investments"]
        total_expenses = sum(getattr(profile, f) for f in expense_fields)
        monthly_savings = profile.income - total_expenses
        savings_rate_pct = (
            round(100 * monthly_savings / profile.income, 2)
            if profile.income > 0 else 0.0
        )

        months_to_goal = None
        if monthly_savings > 0 and profile.savings_goal > 0:
            months_to_goal = round(profile.savings_goal / monthly_savings, 1)

        breakdown = {
            f: round(100 * getattr(profile, f) / profile.income, 2)
            if profile.income > 0 else 0.0
            for f in expense_fields
        }

        return FinancialAnalysis(
            total_expenses=round(total_expenses, 2),
            monthly_savings=round(monthly_savings, 2),
            savings_rate_pct=savings_rate_pct,
            months_to_goal=months_to_goal,
            expense_breakdown_pct=breakdown,
        )
