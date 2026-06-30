"""
LangGraph orchestration for the financial advisory pipeline.

Graph flow:
  categorize -> analyze -> retrieve_memory -> recommend -> store_memory

Each node is one agent's responsibility; state is threaded through as a
typed dict, same pattern as the AutoML pipeline in this portfolio.
"""
from __future__ import annotations

from dataclasses import asdict
from typing import Any, TypedDict

from langgraph.graph import StateGraph, END

from agents.analysis_agent import FinancialAnalysisAgent, BudgetProfile
from agents.categorization_agent import TransactionCategorizationAgent
from agents.recommendation_agent import SavingsRecommendationAgent
from rag.memory import embed_text, summarize_profile, retrieve_similar_sessions


class AdvisoryState(TypedDict, total=False):
    profile: dict
    analysis: dict
    categorization: dict
    similar_sessions: list[dict]
    retrieval_latency_ms: float
    recommendation: dict
    user_id: str


def node_analyze(state: AdvisoryState) -> AdvisoryState:
    profile = BudgetProfile(**state["profile"])
    analysis = FinancialAnalysisAgent().analyze(profile)
    return {**state, "analysis": asdict(analysis)}


def node_categorize(state: AdvisoryState) -> AdvisoryState:
    result = TransactionCategorizationAgent().categorize(
        state["analysis"]["expense_breakdown_pct"]
    )
    flags = [asdict(f) for f in result.flags]
    categorization = {
        "essential_total_pct": result.essential_total_pct,
        "discretionary_total_pct": result.discretionary_total_pct,
        "savings_total_pct": result.savings_total_pct,
        "flags": flags,
    }
    return {**state, "categorization": categorization}


def node_retrieve_memory(state: AdvisoryState) -> AdvisoryState:
    summary = summarize_profile(state["profile"], state["analysis"])
    result = retrieve_similar_sessions(summary, user_id=state.get("user_id"))
    return {**state, "similar_sessions": result["matches"],
            "retrieval_latency_ms": result["retrieval_latency_ms"]}


def node_recommend(state: AdvisoryState) -> AdvisoryState:
    rec = SavingsRecommendationAgent().recommend(
        state["profile"], state["analysis"], state["categorization"],
        state["similar_sessions"],
    )
    return {**state, "recommendation": rec}


def build_graph():
    graph = StateGraph(AdvisoryState)
    graph.add_node("analyze", node_analyze)
    graph.add_node("categorize", node_categorize)
    graph.add_node("retrieve_memory", node_retrieve_memory)
    graph.add_node("recommend", node_recommend)

    graph.set_entry_point("analyze")
    graph.add_edge("analyze", "categorize")
    graph.add_edge("categorize", "retrieve_memory")
    graph.add_edge("retrieve_memory", "recommend")
    graph.add_edge("recommend", END)

    return graph.compile()


def run_advisory_pipeline(profile: dict, user_id: str = "anonymous") -> dict:
    app = build_graph()
    final_state = app.invoke({"profile": profile, "user_id": user_id})
    return {
        "analysis": final_state["analysis"],
        "categorization": final_state["categorization"],
        "similar_sessions": final_state["similar_sessions"],
        "retrieval_latency_ms": final_state["retrieval_latency_ms"],
        "recommendation": final_state["recommendation"]["recommendation"],
        "recommendation_method": final_state["recommendation"].get("method", "llm"),
    }
