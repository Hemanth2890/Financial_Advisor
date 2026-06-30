"""
SavingsRecommendationAgent: generates personalized, contextually-aware
savings advice using Gemini 2.0 Flash, conditioned on the deterministic
analysis, the categorization flags, and any similar past sessions
retrieved via RAG. Falls back to a template-based recommendation if no
GEMINI_API_KEY is configured, clearly labeled.
"""
from __future__ import annotations

import os


class SavingsRecommendationAgent:
    def __init__(self, model: str = "gemini-2.5-flash"):
        self.model_name = model

    def recommend(self, profile: dict, analysis: dict, categorization: dict,
                   similar_sessions: list[dict]) -> dict:
        api_key = os.environ.get("GEMINI_API_KEY")
        if api_key:
            try:
                return self._recommend_llm(api_key, profile, analysis,
                                            categorization, similar_sessions)
            except Exception as exc:  # noqa: BLE001
                fallback = self._recommend_fallback(analysis, categorization)
                fallback["method"] = f"fallback (LLM error: {exc})"
                return fallback
        fallback = self._recommend_fallback(analysis, categorization)
        fallback["method"] = "fallback (no GEMINI_API_KEY set)"
        return fallback

    def _recommend_llm(self, api_key: str, profile: dict, analysis: dict,
                        categorization: dict, similar_sessions: list[dict]) -> dict:
        import google.generativeai as genai

        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(self.model_name)

        context_block = ""
        if similar_sessions:
            context_block = "\n\nSIMILAR PAST SESSIONS (for context, do not repeat verbatim):\n"
            for s in similar_sessions:
                context_block += f"- {s['summary']} Advice given: {s['recommendation'][:200]}\n"

        flagged = [f for f in categorization.get("flags", []) if f["status"] == "above_benchmark"]
        flags_text = (
            ", ".join(f"{f['category']} ({f['pct_of_income']}% of income, "
                      f"benchmark {f['benchmark_pct']}%)" for f in flagged)
            if flagged else "none"
        )

        prompt = f"""You are a personal finance advisor. Give personalized, practical savings advice.

FINANCIAL PROFILE:
- Monthly income: {profile['income']}
- Total expenses: {analysis['total_expenses']}
- Monthly savings: {analysis['monthly_savings']}
- Savings rate: {analysis['savings_rate_pct']}%
- Savings goal: {profile['savings_goal']}
- Estimated months to reach goal: {analysis.get('months_to_goal', 'N/A')}

CATEGORIZATION:
- Essential spending: {categorization['essential_total_pct']}% of income
- Discretionary spending: {categorization['discretionary_total_pct']}% of income
- Categories above typical benchmark: {flags_text}
{context_block}
Give 3 specific, practical recommendations referencing the actual numbers above.
Respond in plain bullet points, no markdown headers."""

        response = model.generate_content(prompt)
        return {
            "recommendation": response.text.strip(),
            "method": "llm",
        }

    def _recommend_fallback(self, analysis: dict, categorization: dict) -> dict:
        flagged = [f["category"] for f in categorization.get("flags", [])
                   if f["status"] == "above_benchmark"]
        lines = [
            f"- Your current savings rate is {analysis['savings_rate_pct']}%.",
        ]
        if analysis.get("months_to_goal"):
            lines.append(f"- At this rate, you'll reach your savings goal in "
                          f"about {analysis['months_to_goal']} months.")
        if flagged:
            lines.append(f"- Consider reviewing spending in: {', '.join(flagged)}, "
                          f"which is above typical benchmarks for your income.")
        else:
            lines.append("- Your spending across categories looks within typical ranges.")
        return {"recommendation": "\n".join(lines)}
