"""
Obligation Impact Analysis - LangGraph Agent
Workflow: Parse → Decompose → Cross-Reference → Score → Report
"""

import json
from typing import TypedDict
from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, SystemMessage

from core.llm import get_openai_primary
from core.prompts import get_prompt
from core.domains import get_domain


class ImpactState(TypedDict):
    regulation_text: str
    regulation_source: str
    atomic_obligations: list[dict]
    cross_references: list[dict]
    impact_scores: list[dict]
    report: dict
    current_step: str


def decompose_obligations(state: ImpactState) -> ImpactState:
    """Decompose complex regulation into atomic, testable obligations."""
    llm = get_openai_primary()

    prompt = f"""Decompose this regulation into atomic compliance obligations.
Each obligation should be independently testable and assignable.

SOURCE: {state['regulation_source']}
TEXT:
{state['regulation_text']}

Return a JSON array:
[
    {{
        "ob_id": "unique short ID",
        "parent_section": "section reference from the regulation",
        "obligation": "Clear statement of what must be done",
        "obligated_entity": "Who must comply",
        "condition": "Under what conditions this applies",
        "deadline": "When compliance is required",
        "measurement_criteria": "How compliance is verified",
        "category": "operational|reporting|financial|technical|governance"
    }}
]"""

    response = llm.invoke([
        SystemMessage(content=get_prompt("obligation_impact")),
        HumanMessage(content=prompt)
    ])

    try:
        content = response.content
        obligations = json.loads(content[content.find("["):content.rfind("]") + 1])
    except (json.JSONDecodeError, ValueError):
        obligations = [{"ob_id": "PARSE-ERR", "obligation": "Failed to parse", "category": "unknown"}]

    return {**state, "atomic_obligations": obligations, "current_step": "cross_ref"}


def cross_reference(state: ImpactState) -> ImpactState:
    """Check for conflicts/overlaps with existing PG&E obligations."""
    llm = get_openai_primary()

    domain = get_domain()
    register = "\n".join(f"- {o}" for o in domain["existing_obligations"])

    prompt = f"""Analyze these new obligations for potential conflicts or overlaps with the
regulatory requirements already binding on {domain['company']}.

EXISTING OBLIGATION REGISTER:
{register}

NEW OBLIGATIONS:
{json.dumps(state['atomic_obligations'], indent=2)}

For each new obligation, identify:
[
    {{
        "ob_id": "matching new obligation ID",
        "conflicts_with": ["list of existing requirements that conflict"],
        "overlaps_with": ["list of existing requirements that overlap"],
        "conflict_description": "nature of conflict if any",
        "resolution_approach": "how to resolve conflicts",
        "synergies": "any existing programs that support compliance"
    }}
]"""

    response = llm.invoke([
        SystemMessage(content=get_prompt("obligation_impact")),
        HumanMessage(content=prompt)
    ])

    try:
        content = response.content
        refs = json.loads(content[content.find("["):content.rfind("]") + 1])
    except (json.JSONDecodeError, ValueError):
        refs = []

    return {**state, "cross_references": refs, "current_step": "score"}


def score_impacts(state: ImpactState) -> ImpactState:
    """Score each obligation on cost, effort, risk, and timeline dimensions."""
    llm = get_openai_primary()  # GPT-4o for cost-effective scoring

    domain = get_domain()

    prompt = f"""Score the impact of each obligation on {domain['company']}'s operations.
Consider its financial position, workforce, and regulatory history.

ENTERPRISE CONTEXT — {domain['company_full']}:
{domain['enterprise_profile']}

OBLIGATIONS:
{json.dumps(state['atomic_obligations'], indent=2)}

CROSS-REFERENCES:
{json.dumps(state['cross_references'], indent=2)}

Score each obligation:
[
    {{
        "ob_id": "matching ID",
        "cost_impact": {{
            "score": 1-10,
            "estimated_range_low": dollar amount,
            "estimated_range_high": dollar amount,
            "cost_type": "capex|opex|both",
            "rationale": "brief explanation"
        }},
        "operational_impact": {{
            "score": 1-10,
            "affected_processes": ["list"],
            "workforce_impact": "description",
            "rationale": "brief explanation"
        }},
        "timeline_risk": {{
            "score": 1-10,
            "feasibility": "achievable|challenging|at_risk|unlikely",
            "critical_path_items": ["list"],
            "rationale": "brief explanation"
        }},
        "penalty_risk": {{
            "score": 1-10,
            "max_penalty": dollar amount,
            "enforcement_likelihood": "low|medium|high",
            "rationale": "brief explanation"
        }},
        "overall_priority": "critical|high|medium|low",
        "recommended_approach": "brief strategy"
    }}
]"""

    response = llm.invoke([
        SystemMessage(content=get_prompt("obligation_impact")),
        HumanMessage(content=prompt)
    ])

    try:
        content = response.content
        scores = json.loads(content[content.find("["):content.rfind("]") + 1])
    except (json.JSONDecodeError, ValueError):
        scores = []

    return {**state, "impact_scores": scores, "current_step": "report"}


def generate_impact_report(state: ImpactState) -> ImpactState:
    """Generate executive impact report."""
    llm = get_openai_primary()

    prompt = f"""Generate an executive impact assessment report for PG&E leadership.

REGULATION: {state['regulation_source']}

OBLIGATIONS: {json.dumps(state['atomic_obligations'], indent=2)}

IMPACT SCORES: {json.dumps(state['impact_scores'], indent=2)}

CROSS-REFERENCES: {json.dumps(state['cross_references'], indent=2)}

Produce a JSON report:
{{
    "executive_summary": "3-4 sentence overview for C-suite",
    "total_obligations": number,
    "critical_obligations": number,
    "estimated_total_cost_low": dollar amount,
    "estimated_total_cost_high": dollar amount,
    "earliest_deadline": "date",
    "key_risks": ["top 3-5 risks"],
    "recommended_actions": [
        {{
            "action": "what to do",
            "owner": "department",
            "priority": "immediate|short_term|medium_term",
            "deadline": "date"
        }}
    ],
    "board_attention_items": ["items requiring board/executive attention"],
    "regulatory_strategy": "recommended approach for engaging with regulator"
}}"""

    response = llm.invoke([
        SystemMessage(content=get_prompt("obligation_impact")),
        HumanMessage(content=prompt)
    ])

    try:
        content = response.content
        report = json.loads(content[content.find("{"):content.rfind("}") + 1])
    except (json.JSONDecodeError, ValueError):
        report = {"executive_summary": response.content[:500], "error": "Failed to parse structured report"}

    return {**state, "report": report, "current_step": "complete"}


def build_impact_graph() -> StateGraph:
    """Build the obligation impact analysis graph."""
    workflow = StateGraph(ImpactState)

    workflow.add_node("decompose", decompose_obligations)
    workflow.add_node("cross_ref", cross_reference)
    workflow.add_node("score", score_impacts)
    workflow.add_node("report", generate_impact_report)

    workflow.set_entry_point("decompose")
    workflow.add_edge("decompose", "cross_ref")
    workflow.add_edge("cross_ref", "score")
    workflow.add_edge("score", "report")
    workflow.add_edge("report", END)

    return workflow.compile()


def run_obligation_impact(regulation_text: str, regulation_source: str = "Unknown") -> dict:
    """Run full obligation impact analysis."""
    graph = build_impact_graph()

    initial_state: ImpactState = {
        "regulation_text": regulation_text,
        "regulation_source": regulation_source,
        "atomic_obligations": [],
        "cross_references": [],
        "impact_scores": [],
        "report": {},
        "current_step": "decompose",
    }

    return graph.invoke(initial_state)
