"""
Regulatory Change Monitor - LangGraph Agent
Multi-step agentic workflow: Fetch → Classify → Extract → Compare → Map → Notify
"""

import json
import uuid
from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, SystemMessage

from core.llm import get_claude_sonnet
from core.prompts import REGULATORY_MONITOR_PROMPT
from agents.regulatory_monitor.tools import (
    SAMPLE_REGULATORY_UPDATES,
)


# --- State Schema ---
class MonitorState(TypedDict):
    source_filter: str
    raw_updates: list[dict]
    classified_updates: list[dict]
    extracted_obligations: list[dict]
    impact_mappings: list[dict]
    alerts: list[dict]
    current_step: str
    error: str | None


# --- Graph Nodes ---

def fetch_updates(state: MonitorState) -> MonitorState:
    """Node 1: Fetch regulatory updates from sources."""
    source = state.get("source_filter", "all")
    updates = SAMPLE_REGULATORY_UPDATES
    if source != "all":
        updates = [u for u in updates if u["source"].upper() == source.upper()]
    return {
        **state,
        "raw_updates": updates,
        "current_step": "classify",
    }


def classify_changes(state: MonitorState) -> MonitorState:
    """Node 2: Classify each update by type and severity using Claude."""
    llm = get_claude_sonnet()
    classified = []

    for update in state["raw_updates"]:
        prompt = f"""Analyze this regulatory update and classify it.

SOURCE: {update['source']}
TITLE: {update['title']}
DATE: {update['published_date']}

FULL TEXT:
{update['text']}

Respond in JSON format:
{{
    "change_type": "rule_change|guidance|notice|enforcement|proposed_rule",
    "severity": "critical|high|medium|low",
    "summary": "2-3 sentence summary of the material change",
    "key_deadlines": ["list of deadline strings"],
    "penalty_info": "penalty details if mentioned"
}}"""

        response = llm.invoke([
            SystemMessage(content=REGULATORY_MONITOR_PROMPT),
            HumanMessage(content=prompt)
        ])

        try:
            # Extract JSON from response
            content = response.content
            json_start = content.find("{")
            json_end = content.rfind("}") + 1
            classification = json.loads(content[json_start:json_end])
        except (json.JSONDecodeError, ValueError):
            classification = {
                "change_type": "unknown",
                "severity": "medium",
                "summary": content[:300],
                "key_deadlines": [],
                "penalty_info": "Unable to parse"
            }

        classified.append({
            **update,
            "classification": classification
        })

    return {
        **state,
        "classified_updates": classified,
        "current_step": "extract",
    }


def extract_obligations(state: MonitorState) -> MonitorState:
    """Node 3: Extract specific obligations from classified changes."""
    llm = get_claude_sonnet()
    all_obligations = []

    for update in state["classified_updates"]:
        prompt = f"""Extract all specific compliance obligations from this regulatory change.

SOURCE: {update['source']}
TITLE: {update['title']}
CLASSIFICATION: {json.dumps(update['classification'])}

FULL TEXT:
{update['text']}

For each obligation, provide JSON array:
[
    {{
        "obligation_id": "unique short ID like CPUC-WMP-001",
        "description": "What must be done",
        "responsible_entity": "Who must do it",
        "deadline": "When it must be done",
        "measurement": "How compliance is measured",
        "penalty": "Consequence of non-compliance",
        "category": "wildfire|grid_reliability|cybersecurity|environmental|reporting|safety|ai_governance|financial"
    }}
]"""

        response = llm.invoke([
            SystemMessage(content=REGULATORY_MONITOR_PROMPT),
            HumanMessage(content=prompt)
        ])

        try:
            content = response.content
            json_start = content.find("[")
            json_end = content.rfind("]") + 1
            obligations = json.loads(content[json_start:json_end])
        except (json.JSONDecodeError, ValueError):
            obligations = [{
                "obligation_id": f"{update['source']}-PARSE-ERR",
                "description": "Failed to parse obligations — manual review required",
                "responsible_entity": "PG&E",
                "deadline": "TBD",
                "measurement": "TBD",
                "penalty": "TBD",
                "category": "unknown"
            }]

        for ob in obligations:
            ob["source_regulation"] = update["title"]
            ob["source_body"] = update["source"]
            ob["severity"] = update["classification"]["severity"]

        all_obligations.extend(obligations)

    return {
        **state,
        "extracted_obligations": all_obligations,
        "current_step": "map",
    }


def map_to_departments(state: MonitorState) -> MonitorState:
    """Node 4: Map obligations to PG&E departments and assess impact."""
    llm = get_claude_sonnet()

    obligations_text = json.dumps(state["extracted_obligations"], indent=2)

    prompt = f"""Given these extracted regulatory obligations for PG&E, map each to the
appropriate PG&E department(s) and assess operational impact.

PG&E DEPARTMENTS:
- Electric Operations (grid, transmission, distribution)
- Gas Operations (pipeline, distribution, storage)
- Wildfire Safety (vegetation mgmt, fire prevention, PSPS)
- IT/Cybersecurity (NERC CIP, data systems)
- Environmental & Sustainability (emissions, compliance)
- Regulatory Affairs (filings, rate cases)
- Legal & Compliance (enforcement, litigation)
- Customer Operations (billing, service, data privacy)
- Generation (power plants, procurement)
- Corporate (finance, governance, reporting)

OBLIGATIONS:
{obligations_text}

For each obligation, provide a JSON array:
[
    {{
        "obligation_id": "the original ID",
        "primary_department": "main responsible department",
        "supporting_departments": ["other involved departments"],
        "operational_impact": "brief description of what changes operationally",
        "estimated_effort": "low|medium|high|very_high",
        "requires_capex": true/false,
        "requires_new_systems": true/false,
        "timeline_risk": "on_track|tight|at_risk|critical"
    }}
]"""

    response = llm.invoke([
        SystemMessage(content=REGULATORY_MONITOR_PROMPT),
        HumanMessage(content=prompt)
    ])

    try:
        content = response.content
        json_start = content.find("[")
        json_end = content.rfind("]") + 1
        mappings = json.loads(content[json_start:json_end])
    except (json.JSONDecodeError, ValueError):
        mappings = []

    return {
        **state,
        "impact_mappings": mappings,
        "current_step": "notify",
    }


def generate_alerts(state: MonitorState) -> MonitorState:
    """Node 5: Generate alerts with priority for stakeholders."""
    alerts = []

    severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}

    for update in state["classified_updates"]:
        classification = update["classification"]
        severity = classification.get("severity", "medium")

        related_obligations = [
            o for o in state["extracted_obligations"]
            if o.get("source_regulation") == update["title"]
        ]
        related_mappings = [
            m for m in state["impact_mappings"]
            if m.get("obligation_id") in [o["obligation_id"] for o in related_obligations]
        ]

        affected_depts = set()
        for m in related_mappings:
            affected_depts.add(m.get("primary_department", "Unknown"))
            affected_depts.update(m.get("supporting_departments", []))

        alert = {
            "alert_id": str(uuid.uuid4())[:8],
            "source": update["source"],
            "title": update["title"],
            "severity": severity,
            "change_type": classification.get("change_type", "unknown"),
            "summary": classification.get("summary", ""),
            "key_deadlines": classification.get("key_deadlines", []),
            "penalty_info": classification.get("penalty_info", ""),
            "obligation_count": len(related_obligations),
            "obligations": related_obligations,
            "affected_departments": sorted(affected_depts),
            "impact_mappings": related_mappings,
            "sort_key": severity_order.get(severity, 2),
        }
        alerts.append(alert)

    # Sort by severity
    alerts.sort(key=lambda a: a["sort_key"])

    return {
        **state,
        "alerts": alerts,
        "current_step": "complete",
    }


# --- Build Graph ---

def build_monitor_graph() -> StateGraph:
    """Build the LangGraph state machine for regulatory monitoring."""
    workflow = StateGraph(MonitorState)

    workflow.add_node("fetch", fetch_updates)
    workflow.add_node("classify", classify_changes)
    workflow.add_node("extract", extract_obligations)
    workflow.add_node("map", map_to_departments)
    workflow.add_node("notify", generate_alerts)

    workflow.set_entry_point("fetch")
    workflow.add_edge("fetch", "classify")
    workflow.add_edge("classify", "extract")
    workflow.add_edge("extract", "map")
    workflow.add_edge("map", "notify")
    workflow.add_edge("notify", END)

    return workflow.compile()


def run_regulatory_monitor(source_filter: str = "all") -> dict:
    """Run the full regulatory monitoring pipeline."""
    graph = build_monitor_graph()

    initial_state: MonitorState = {
        "source_filter": source_filter,
        "raw_updates": [],
        "classified_updates": [],
        "extracted_obligations": [],
        "impact_mappings": [],
        "alerts": [],
        "current_step": "fetch",
        "error": None,
    }

    result = graph.invoke(initial_state)
    return result
