# Regulatory Compliance AI — Full Source Bundle

> Every file below. Paste-safe, human-readable. For the executable version that
> reconstitutes the project with checksums, use `regcompliance_bundle.py`.

**23 files · 302,251 bytes**

## Contents

- `agents/__init__.py` (44 bytes)
- `agents/regulatory_monitor/__init__.py` (68 bytes)
- `agents/regulatory_monitor/graph.py` (12,297 bytes)  ← **the provenance verifier — do not lose this**
- `agents/regulatory_monitor/tools.py` (21,427 bytes)
- `agents/obligation_impact/__init__.py` (66 bytes)
- `agents/obligation_impact/graph.py` (8,457 bytes)
- `agents/audit_prep/__init__.py` (59 bytes)
- `agents/audit_prep/graph.py` (29,055 bytes)
- `agents/case_analytics/__init__.py` (90 bytes)
- `agents/case_analytics/chain.py` (35,426 bytes)
- `core/__init__.py` (42 bytes)
- `core/prompts.py` (5,971 bytes)
- `core/domains.py` (82,287 bytes)
- `core/llm.py` (4,193 bytes)
- `core/vectorstore.py` (3,427 bytes)
- `core/db.py` (7,452 bytes)
- `core/embeddings.py` (1,381 bytes)
- `api.py` (18,274 bytes)
- `requirements.txt` (558 bytes)
- `.env.example` (679 bytes)
- `BLUEPRINT.md` (26,215 bytes)
- `TOPAZ_PORT.md` (8,125 bytes)
- `docs/openapi.json` (36,658 bytes)

---

## `agents/__init__.py`

```python
# Regulatory Compliance AI - Agents Module
```

## `agents/regulatory_monitor/__init__.py`

```python
from agents.regulatory_monitor.graph import run_regulatory_monitor
```

## `agents/regulatory_monitor/graph.py`

```python
"""
Regulatory Change Monitor - LangGraph Agent
Multi-step agentic workflow: Fetch → Classify → Extract → Compare → Map → Notify
"""

import json
import uuid
from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, SystemMessage

from core.llm import get_openai_primary
from core.prompts import get_prompt
from core.domains import get_domain
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

def _normalize(text: str) -> str:
    """Collapse whitespace so a quote can be matched against wrapped source text."""
    return " ".join(text.split()).lower()


def _quote_in_source(quote: str, source_text: str) -> bool:
    """True only if the model's quote actually appears in the source document.

    Regulatory obligations are only defensible if they trace to real text. A quote the
    model paraphrased or invented will not match, and the obligation is flagged rather
    than silently trusted. Matching is whitespace- and case-insensitive; a long quote is
    accepted if a substantial leading span matches, since models sometimes elide with '...'.
    """
    q, src = _normalize(quote), _normalize(source_text)
    if not q or len(q) < 12:
        return False
    if q in src:
        return True
    # Tolerate elision: require the first 60 chars of the quote to appear verbatim.
    head = q[:60]
    return len(head) >= 40 and head in src


def fetch_updates(state: MonitorState) -> MonitorState:
    """Node 1: Fetch regulatory updates from sources."""
    source = state.get("source_filter", "all")
    updates = get_domain()["regulations"]
    if source != "all":
        updates = [u for u in updates if u["source"].upper() == source.upper()]
    return {
        **state,
        "raw_updates": updates,
        "current_step": "classify",
    }


def classify_changes(state: MonitorState) -> MonitorState:
    """Node 2: Classify each update by type and severity using Claude."""
    llm = get_openai_primary()
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
            SystemMessage(content=get_prompt("regulatory_monitor")),
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
    llm = get_openai_primary()
    all_obligations = []

    for update in state["classified_updates"]:
        prompt = f"""Extract all specific compliance obligations from this regulatory change.

SOURCE: {update['source']}
TITLE: {update['title']}
CLASSIFICATION: {json.dumps(update['classification'])}

FULL TEXT:
{update['text']}

PROVENANCE IS MANDATORY. Every obligation must carry a verbatim quote from the source text above.
If a field is not stated in the source, write "not stated in source" — never estimate a value into it.
An obligation with no supporting quote must not be emitted.

For each obligation, provide JSON array:
[
    {{
        "obligation_id": "unique short ID like OEIS-WMP-001",
        "description": "What must be done",
        "responsible_entity": "Who must do it",
        "deadline": "When it must be done, or 'not stated in source'",
        "measurement": "How compliance is measured, or 'not stated in source'",
        "penalty": "Consequence of non-compliance, or 'not stated in source'",
        "category": "wildfire|grid_reliability|cybersecurity|environmental|reporting|safety|ai_governance|financial",
        "source_quote": "VERBATIM sentence(s) copied exactly from the FULL TEXT above that establish this obligation",
        "source_section": "the numbered section the quote came from, e.g. '1. ENHANCED VEGETATION MANAGEMENT'",
        "confidence": "high|medium|low — how unambiguously the source establishes this obligation",
        "inferred": false
    }}
]"""

        response = llm.invoke([
            SystemMessage(content=get_prompt("regulatory_monitor")),
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
                "deadline": "not stated in source",
                "measurement": "not stated in source",
                "penalty": "not stated in source",
                "category": "unknown",
                "source_quote": "",
                "source_section": "",
                "confidence": "low",
                "inferred": True,
            }]

        for ob in obligations:
            ob["source_regulation"] = update["title"]
            ob["source_body"] = update["source"]
            ob["source_url"] = update.get("url", "")
            ob["severity"] = update["classification"]["severity"]
            # Verify the model actually quoted the source rather than paraphrasing it.
            # An unverifiable quote is downgraded, never silently accepted.
            quote = (ob.get("source_quote") or "").strip()
            ob["citation_verified"] = bool(quote) and _quote_in_source(quote, update["text"])
            if not ob["citation_verified"]:
                ob["confidence"] = "low"

        all_obligations.extend(obligations)

    return {
        **state,
        "extracted_obligations": all_obligations,
        "current_step": "map",
    }


def map_to_departments(state: MonitorState) -> MonitorState:
    """Node 4: Map obligations to Company departments and assess impact."""
    llm = get_openai_primary()

    obligations_text = json.dumps(state["extracted_obligations"], indent=2)
    domain = get_domain()
    departments = "\n".join(f"- {d}" for d in domain["departments"])

    prompt = f"""Given these extracted regulatory obligations for {domain['company']}, map each to
the appropriate department(s) and assess operational impact.

DEPARTMENTS:
{departments}

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
        SystemMessage(content=get_prompt("regulatory_monitor")),
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
```

## `agents/regulatory_monitor/tools.py`

```python
"""
Regulatory Change Monitor - Agent Tools
Web scraping, document parsing, and RAG search tools.
"""

import json
from datetime import datetime
from langchain_core.tools import tool
from core.vectorstore import search_documents, add_documents, COLLECTION_REGULATIONS


# --- Simulated regulatory sources for prototype ---
# In production, these would scrape actual CPUC/FERC/NERC websites

SAMPLE_REGULATORY_UPDATES = [
    # ==================== OEIS (wildfire-safety regulator; WMPs are filed HERE, not with CPUC) ====
    {
        "source": "OEIS",
        "title": "2026-2028 Wildfire Mitigation Plan Guidelines: Updated Requirements",
        "url": "https://energysafety.ca.gov/what-we-do/electrical-infrastructure-safety/wildfire-mitigation-and-safety/wildfire-mitigation-plans/",
        "published_date": "2025-12-15",
        "text": """The Office of Energy Infrastructure Safety (OEIS) issues these Wildfire Mitigation Plan
        Guidelines directing PG&E and all large electrical corporations to submit updated Wildfire Mitigation
        Plans (WMPs) incorporating the following new requirements effective January 1, 2026. WMPs are submitted
        to and approved by OEIS, which also issues the annual Safety Certification; the CPUC ratifies OEIS's
        WMP approval. Failure to evidence compliance may affect the Safety Certification and the cost-recovery
        presumption available under AB 1054 (Pub. Util. Code § 451.1).

        1. ENHANCED VEGETATION MANAGEMENT: Utilities must increase vegetation inspection frequency
           from annual to semi-annual for all Tier 3 High Fire Threat Districts (HFTDs).
           Clearance requirements increased from 4 feet to 6 feet for all transmission lines above 65kV.

        2. GRID HARDENING TARGETS: Underground 300 additional circuit-miles in HFTDs by December 2027.
           All new distribution construction in Tier 2/3 HFTDs must use covered conductor.

        3. PUBLIC SAFETY POWER SHUTOFF (PSPS) REDUCTION: Reduce PSPS events by 50% compared to
           2024 baseline. Implement sectionalizing devices on all circuits serving critical facilities.

        4. REAL-TIME MONITORING: Deploy HD cameras and weather stations at 100% of transmission
           structures in Tier 3 HFTDs by June 2026. AI-powered fire detection required.

        5. REPORTING: Quarterly compliance reports due within 30 days of quarter end.
           Annual independent audit of WMP implementation required.

        Consequences of non-compliance: OEIS may find the WMP non-compliant, may decline to issue or may
        revoke the annual Safety Certification, and may refer the matter to the CPUC's Safety and Enforcement
        Division (SED). SED enforcement may impose penalties of up to $100,000 per violation per day under
        Pub. Util. Code § 2107. Loss of Safety Certification also affects the AB 1054 cost-recovery
        presumption and Wildfire Fund access."""
    },
    {
        "source": "CPUC",
        "title": "Rulemaking 25-01-012: AI and Advanced Analytics in Utility Operations",
        "url": "https://docs.cpuc.ca.gov/PublishedDocs/Published/G000/M535/K456/535456789.PDF",
        "published_date": "2026-01-15",
        "text": """The Commission opens this rulemaking to establish a framework for the responsible
        deployment of Artificial Intelligence (AI) and advanced analytics by California utilities.

        Proposed requirements:
        1. AI GOVERNANCE: Utilities deploying AI systems that affect service reliability, rates,
           or safety must establish an AI Governance Board with quarterly reporting to CPUC.

        2. ALGORITHMIC TRANSPARENCY: AI models used in rate-setting, demand forecasting, or
           outage prediction must be explainable. Black-box models prohibited for safety-critical
           applications without human-in-the-loop override.

        3. BIAS TESTING: AI systems affecting customer service, disconnection, or billing must
           undergo annual bias audits by independent third parties.

        4. DATA PRIVACY: Customer data used for AI training must be anonymized per CCPA+
           standards. Opt-out mechanism required for customers.

        5. CYBERSECURITY: AI systems connected to grid operations must meet NERC CIP standards.

        Comment deadline: March 15, 2026. Proposed decision expected Q3 2026."""
    },
    {
        "source": "CPUC",
        "title": "Decision 26-02-018: Customer Data Privacy and Third-Party Access Rules",
        "url": "https://docs.cpuc.ca.gov/PublishedDocs/Published/G000/M540/K789/540789012.PDF",
        "published_date": "2026-02-20",
        "text": """The CPUC adopts updated rules governing customer energy usage data privacy and
        third-party data access for all California investor-owned utilities, effective July 1, 2026.

        KEY REQUIREMENTS:
        1. DATA MINIMIZATION: Utilities shall collect only the minimum customer data necessary
           for service delivery. AMI (smart meter) data at sub-15-minute intervals requires
           explicit opt-in consent from the customer.

        2. THIRD-PARTY ACCESS: All third-party data sharing agreements must be filed with the
           CPUC. Customers must be notified within 5 business days of any data sharing.
           Green Button Connect My Data (CMD) API must be available for all residential accounts.

        3. BREACH NOTIFICATION: Utilities must notify affected customers within 72 hours of
           discovering a data breach affecting energy usage data, customer PII, or billing records.
           CPUC notification required within 24 hours.

        4. AI/ML TRAINING DATA: Customer data used for AI model training must be anonymized
           using k-anonymity (k>=5) or differential privacy techniques. Annual privacy impact
           assessments required for all AI systems using customer data.

        5. RETENTION LIMITS: Granular energy usage data (sub-hourly) shall be retained for
           no more than 3 years. Aggregated data may be retained for 7 years.

        Penalties: $2,500 per affected customer per violation under PU Code Section 2108.
        Annual third-party privacy audit required starting 2027."""
    },
    {
        "source": "CPUC",
        "title": "Resolution E-5289: Electric Vehicle Infrastructure and Rate Design",
        "url": "https://docs.cpuc.ca.gov/PublishedDocs/Published/G000/M542/K234/542234567.PDF",
        "published_date": "2026-03-01",
        "text": """The CPUC adopts Resolution E-5289 establishing new requirements for utility-owned
        EV charging infrastructure and time-of-use rate design for EV customers.

        REQUIREMENTS:
        1. INFRASTRUCTURE DEPLOYMENT: PG&E shall deploy 5,000 Level 2 and 500 DC Fast Charging
           stations in disadvantaged communities (DACs) by December 2028. At least 40% must be
           in multi-family housing locations.

        2. RATE DESIGN: New EV-specific time-of-use rate with super-off-peak period (midnight-6am)
           priced at no more than $0.10/kWh to incentivize managed charging. Dynamic pricing pilot
           with real-time grid carbon intensity signals required by 2027.

        3. GRID INTEGRATION: Vehicle-to-Grid (V2G) interconnection standards must be filed within
           120 days. Utilities must develop bidirectional charging tariffs by Q4 2026.

        4. REPORTING: Quarterly deployment progress reports; annual equity analysis of charging
           access in DACs vs non-DAC areas; grid impact studies for each service territory.

        Compliance deadlines: Rate design effective Q1 2027. Infrastructure 50% complete by 2027."""
    },
    # ==================== FERC ====================
    {
        "source": "FERC",
        "title": "Order No. 901: Transmission Planning for Extreme Weather Events",
        "url": "https://www.ferc.gov/media/order-no-901",
        "published_date": "2025-11-20",
        "text": """FERC Order No. 901 requires all transmission planning entities to incorporate
        extreme weather scenario analysis into their planning processes.

        Key requirements:
        1. Transmission planners must model at least 3 extreme weather scenarios (heat dome,
           atmospheric river, compound wildfire-heat events) in annual planning assessments.

        2. N-1-1 contingency analysis must include weather-correlated forced outage rates.

        3. All utilities with transmission assets must file updated planning criteria within
           180 days of the effective date of this order.

        4. Regional entities must coordinate extreme weather assumptions across seams.

        Compliance deadline: June 30, 2026. Penalties per 18 CFR 385.218."""
    },
    {
        "source": "FERC",
        "title": "Order No. 898: Cybersecurity Incentives for Grid-Enhancing Technologies",
        "url": "https://www.ferc.gov/media/order-no-898",
        "published_date": "2026-01-10",
        "text": """FERC Order No. 898 establishes cybersecurity incentive rate treatment for
        transmission owners deploying qualifying grid-enhancing technologies (GETs).

        KEY PROVISIONS:
        1. ELIGIBLE TECHNOLOGIES: Dynamic line rating (DLR), advanced power flow controllers,
           topology optimization software, and grid-forming inverters with embedded cybersecurity.

        2. INCENTIVE RATE: 50 basis point adder to ROE for qualifying cybersecurity investments
           in GETs that meet NIST Cybersecurity Framework 2.0 and NERC CIP standards.

        3. SUPPLY CHAIN SECURITY: All GET hardware must comply with FERC Order 2222 supply chain
           risk management requirements. Components from prohibited entities per Section 889 of
           the 2024 NDAA are ineligible for incentive treatment.

        4. REPORTING: Annual cybersecurity posture assessment for all incentivized GETs.
           Incident reporting within 6 hours for cybersecurity events affecting GET operations.

        5. SUNSET: Incentive available for investments made between 2026-2030. Review by 2029.

        Filing deadline: Within 90 days for transmission owners seeking incentive treatment."""
    },
    # ==================== NERC ====================
    {
        "source": "NERC",
        "title": "CIP-015-1: Internal Network Security Monitoring",
        "url": "https://www.nerc.com/pa/Stand/Pages/CIP-015-1.aspx",
        "published_date": "2025-10-01",
        "text": """NERC CIP-015-1 establishes new requirements for internal network security monitoring
        within the Electronic Security Perimeter (ESP) of Bulk Electric System (BES) Cyber Systems.

        Requirements:
        R1: Responsible Entities shall implement network security monitoring for all high and
            medium impact BES Cyber Systems that detects: (a) known malicious network activity,
            (b) anomalous network activity, (c) unauthorized connections.

        R2: Network data shall be retained for a minimum of 90 days (increased from current
            no-requirement baseline).

        R3: Anomaly detection baselines must be updated quarterly.

        R4: Entities must demonstrate monitoring coverage of at least 95% of ESP network traffic.

        Implementation Plan: 24 months from regulatory approval.
        Violation Severity Levels: Lower (R3), Medium (R2), High (R1, R4).
        Penalty range: $25,000 to $1,000,000 per violation per day."""
    },
    # ==================== CARB ====================
    {
        "source": "CARB",
        "title": "Amendments to Cap-and-Trade Regulation: Energy Utility Provisions",
        "url": "https://ww2.arb.ca.gov/rulemaking/2025/cap-and-trade-2025",
        "published_date": "2025-11-05",
        "text": """The California Air Resources Board adopts amendments to the Cap-and-Trade Regulation
        affecting electrical distribution utilities:

        1. EMISSIONS BENCHMARK: The benchmark for natural gas-fired generation decreases from
           0.394 to 0.350 MTCO2e/MWh effective January 1, 2027.

        2. ALLOWANCE ALLOCATION: Free allowance allocation to utilities reduced by 15% for
           compliance period 2026-2028. Utilities must demonstrate allowance proceeds benefit
           ratepayers through rate reduction or clean energy investment.

        3. REPORTING: Enhanced monthly GHG emissions reporting required (previously quarterly).
           New methane leak detection and quantification protocol for gas distribution systems.

        4. OFFSETS: Offset usage limit reduced from 6% to 4% of compliance obligation.

        Compliance deadlines: Reporting changes effective July 1, 2026.
        Benchmark changes effective January 1, 2027."""
    },
    # ==================== EPA ====================
    {
        "source": "EPA",
        "title": "Final Rule: NESHAP for Coal- and Oil-Fired Power Plants (MATS Update)",
        "url": "https://www.epa.gov/stationary-sources-air-pollution/mats-2026-update",
        "published_date": "2026-01-28",
        "text": """The Environmental Protection Agency finalizes updates to the Mercury and Air Toxics
        Standards (MATS) under 40 CFR Part 63, Subpart UUUUU, for coal- and oil-fired electric
        utility steam generating units.

        KEY CHANGES:
        1. MERCURY LIMITS: Existing source mercury emission limit tightened from 1.2 lb/TBtu
           to 0.8 lb/TBtu for lignite-fired units. Filterable particulate matter limit
           reduced from 0.03 to 0.02 lb/MMBtu.

        2. MONITORING: Continuous emissions monitoring (CEMS) required for all units >25 MW
           (previously >50 MW). Sorbent trap monitoring frequency increased to weekly.

        3. STARTUP/SHUTDOWN: Work practice standards for startup and shutdown periods tightened.
           Maximum startup duration reduced from 48 to 24 hours. Cold start exemption eliminated.

        4. RESIDUAL RISK: Updated residual risk assessment incorporating latest health data
           for hydrogen chloride and selenium. PG&E facilities using natural gas are largely
           exempt but must verify fuel certification annually.

        Compliance deadline: 3 years from publication (January 28, 2029).
        Applicability: PG&E has limited direct exposure (gas-fired fleet) but must verify
        fuel specifications and maintain exemption documentation."""
    },
    # ==================== PHMSA ====================
    {
        "source": "PHMSA",
        "title": "Final Rule: Gas Pipeline Leak Detection and Repair (LDAR) Requirements",
        "url": "https://www.phmsa.dot.gov/regulations/final-rule-ldar-2026",
        "published_date": "2026-02-15",
        "text": """PHMSA finalizes amendments to 49 CFR Part 192 establishing comprehensive Leak
        Detection and Repair (LDAR) requirements for natural gas distribution and transmission systems.

        REQUIREMENTS:
        1. ADVANCED LEAK DETECTION: Operators of distribution systems serving >100,000 customers
           must deploy advanced leak detection technology (satellite, aerial, or mobile methane
           sensing) covering 100% of system annually by January 2028.

        2. REPAIR TIMELINES: Grade 1 (hazardous) leaks: repair within 24 hours (no change).
           Grade 2 (non-hazardous, repair-required) leaks: repair within 6 months (reduced from
           12 months). Grade 3 (non-hazardous, monitored) leaks: reclassify annually.

        3. METHANE EMISSIONS REPORTING: Quarterly methane emissions quantification reports
           required, using EPA Subpart W methodology or approved alternative. First report
           due Q1 2027.

        4. LEGACY PIPE REPLACEMENT: Accelerated replacement schedule for cast iron, bare steel,
           and pre-1970 plastic pipe. 5% of legacy pipe replaced annually (minimum).
           Complete elimination of cast iron by 2035.

        5. THIRD-PARTY DAMAGE PREVENTION: Enhanced One-Call response requirements.
           GPS-enabled locating equipment required. Response time for emergency locates
           reduced from 2 hours to 1 hour.

        Penalties: Up to $257,664 per violation per day; $2,576,627 for a related series
        of violations. Criminal penalties for knowing violations causing death or injury."""
    },
    # ==================== Cal-OSHA ====================
    {
        "source": "Cal-OSHA",
        "title": "Emergency Regulation: Wildfire Smoke and Heat Illness Prevention for Utility Workers",
        "url": "https://www.dir.ca.gov/dosh/wildfire-smoke-heat-2026.html",
        "published_date": "2026-03-10",
        "text": """Cal-OSHA adopts emergency regulations under Title 8 CCR Section 5141.1 and
        Section 3395 for wildfire smoke exposure and heat illness prevention for utility workers.

        KEY REQUIREMENTS:
        1. WILDFIRE SMOKE: When AQI exceeds 151 (Unhealthy), utility employers must provide
           N95 respirators and limit outdoor work to 4-hour shifts with mandatory 1-hour
           indoor recovery breaks. When AQI >200 (Very Unhealthy), outdoor work prohibited
           except for emergency restoration.

        2. HEAT ILLNESS PREVENTION (Updated): Threshold temperatures reduced from 95°F to 87°F
           for high-heat procedures. Cool-down rest periods of 10 minutes every 2 hours required
           when temps exceed 87°F. Acclimatization plan required for all new workers and workers
           returning from 14+ day absence.

        3. CONTROLLING EMPLOYER LIABILITY: Utilities using contractor crews for vegetation
           management, construction, or maintenance are jointly liable for contractor compliance
           with these regulations. Utility must verify contractor safety programs quarterly.

        4. TRAINING: Annual training in workers' primary language (not just English).
           Training must cover recognition of heat illness symptoms, buddy system requirements,
           and emergency response procedures. Training records retained for 5 years.

        5. MONITORING: Real-time physiological monitoring (heart rate, core temperature) pilot
           program mandatory for utilities with >5,000 field workers by January 2027.

        Effective immediately as emergency regulation. Permanent adoption expected by Q4 2026.
        Penalties: Up to $25,000 per serious violation; $70,000-$156,259 per willful violation."""
    },
]


@tool
def fetch_regulatory_updates(source: str = "all") -> str:
    """Fetch recent regulatory updates from monitored sources.
    Args:
        source: Filter by source (CPUC, FERC, NERC, CARB, EPA) or 'all'
    """
    updates = SAMPLE_REGULATORY_UPDATES
    if source != "all":
        updates = [u for u in updates if u["source"].upper() == source.upper()]
    # Return without full text for listing
    listing = []
    for u in updates:
        listing.append({
            "source": u["source"],
            "title": u["title"],
            "published_date": u["published_date"],
            "url": u["url"],
            "text_preview": u["text"][:200] + "..."
        })
    return json.dumps(listing, indent=2)


@tool
def get_regulatory_detail(title: str) -> str:
    """Get full text of a specific regulatory update by title.
    Args:
        title: The title (or partial title) of the regulatory update
    """
    for u in SAMPLE_REGULATORY_UPDATES:
        if title.lower() in u["title"].lower():
            return json.dumps(u, indent=2)
    return json.dumps({"error": f"No regulatory update found matching: {title}"})


@tool
def search_existing_obligations(query: str) -> str:
    """Search existing PG&E obligations in the vector store.
    Args:
        query: Natural language description of the obligation to search for
    """
    results = search_documents(COLLECTION_REGULATIONS, query, k=5)
    if not results:
        return json.dumps({"results": [], "message": "No existing obligations found"})
    formatted = []
    for doc, score in results:
        formatted.append({
            "content": doc.page_content[:500],
            "metadata": doc.metadata,
            "relevance_score": round(score, 3)
        })
    return json.dumps({"results": formatted}, indent=2)


@tool
def store_regulatory_change(change_data: str) -> str:
    """Store a classified regulatory change in the database and vector store.
    Args:
        change_data: JSON string with fields: source, title, summary, change_type, severity, obligations
    """
    from core.db import save_regulatory_change
    data = json.loads(change_data)
    row_id = save_regulatory_change(data)

    # Also index in vector store for RAG
    doc_text = f"{data.get('title', '')}\n{data.get('summary', '')}"
    add_documents(
        COLLECTION_REGULATIONS,
        [doc_text],
        [{"source": data.get("source", ""), "change_type": data.get("change_type", ""),
          "severity": data.get("severity", ""), "db_id": row_id}]
    )
    return json.dumps({"stored": True, "id": row_id})
```

## `agents/obligation_impact/__init__.py`

```python
from agents.obligation_impact.graph import run_obligation_impact
```

## `agents/obligation_impact/graph.py`

```python
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
```

## `agents/audit_prep/__init__.py`

```python
from agents.audit_prep.graph import run_audit_preparation
```

## `agents/audit_prep/graph.py`

```python
"""
Audit Analysis & Preparation - LangGraph Multi-Agent
Supervisor pattern: Supervisor → Evidence Collector + Gap Analyzer + Response Drafter
"""

import json
from typing import TypedDict, Literal
from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, SystemMessage

from core.llm import get_openai_primary
from core.prompts import get_prompt
from core.domains import get_domain


class AuditState(TypedDict):
    audit_scope: str
    regulations: list[str]
    obligations: list[dict]
    audit_plan: dict
    evidence_inventory: list[dict]
    gap_analysis: list[dict]
    draft_responses: list[dict]
    supervisor_review: dict
    final_package: dict
    current_step: str
    iteration: int


# --- Simulated Evidence Repository (48 documents across 8 categories) ---
SAMPLE_EVIDENCE = {
    "wildfire": [
        {"doc_id": "WMP-2025", "title": "2025 Wildfire Mitigation Plan", "type": "plan", "status": "current", "location": "SharePoint/Compliance/WMP/", "last_updated": "2025-03-15", "owner": "Wildfire Safety"},
        {"doc_id": "WMP-2026-DRAFT", "title": "2026 WMP Draft — For OEIS Review", "type": "plan", "status": "draft", "location": "SharePoint/Compliance/WMP/2026/", "last_updated": "2026-01-20", "owner": "Wildfire Safety"},
        {"doc_id": "VEG-RPT-Q4", "title": "Q4 2025 Vegetation Management Report", "type": "report", "status": "current", "location": "SharePoint/Compliance/Vegetation/", "last_updated": "2026-01-10", "owner": "Vegetation Mgmt"},
        {"doc_id": "VEG-RPT-Q1-2026", "title": "Q1 2026 Vegetation Management Report", "type": "report", "status": "current", "location": "SharePoint/Compliance/Vegetation/", "last_updated": "2026-04-08", "owner": "Vegetation Mgmt"},
        {"doc_id": "VEG-INSPECT-TRACKER", "title": "Tier 3 HFTD Vegetation Inspection Tracker", "type": "tracker", "status": "current", "location": "SharePoint/Compliance/Vegetation/Inspections/", "last_updated": "2026-04-01", "owner": "Vegetation Mgmt"},
        {"doc_id": "PSPS-PROC-V3", "title": "PSPS Protocol v3.2", "type": "procedure", "status": "current", "location": "SharePoint/Operations/PSPS/", "last_updated": "2025-09-22", "owner": "Electric Operations"},
        {"doc_id": "PSPS-EVENT-LOG-2025", "title": "2025 PSPS Event Log and Impact Analysis", "type": "report", "status": "current", "location": "SharePoint/Operations/PSPS/Events/", "last_updated": "2026-01-15", "owner": "Electric Operations"},
        {"doc_id": "CAM-DEPLOY", "title": "HD Camera Deployment Tracker", "type": "tracker", "status": "partial", "location": "SharePoint/IT/Monitoring/", "last_updated": "2026-03-01", "owner": "IT Operations"},
        {"doc_id": "WEATHER-STATION-INV", "title": "Weather Station Network Inventory", "type": "inventory", "status": "current", "location": "SharePoint/IT/Monitoring/Weather/", "last_updated": "2025-12-15", "owner": "Meteorology"},
        {"doc_id": "COVERED-CONDUCTOR-RPT", "title": "Covered Conductor Installation Progress Report", "type": "report", "status": "current", "location": "SharePoint/Engineering/Grid-Hardening/", "last_updated": "2026-03-15", "owner": "Engineering"},
        {"doc_id": "UNDERGROUND-TRACKER", "title": "10,000 Mile Undergrounding Program Tracker", "type": "tracker", "status": "current", "location": "SharePoint/Engineering/Undergrounding/", "last_updated": "2026-04-01", "owner": "Engineering"},
    ],
    "cybersecurity": [
        {"doc_id": "CIP-ASSESS-2025", "title": "NERC CIP Annual Assessment 2025", "type": "assessment", "status": "current", "location": "SharePoint/IT/NERC-CIP/", "last_updated": "2025-12-20", "owner": "Cybersecurity"},
        {"doc_id": "ESP-INVENTORY", "title": "Electronic Security Perimeter Inventory", "type": "inventory", "status": "current", "location": "SharePoint/IT/Security/", "last_updated": "2026-01-30", "owner": "Cybersecurity"},
        {"doc_id": "VULN-SCAN-Q4", "title": "Q4 2025 Vulnerability Scan Results", "type": "report", "status": "current", "location": "SharePoint/IT/Security/Scans/", "last_updated": "2026-01-05", "owner": "Cybersecurity"},
        {"doc_id": "VULN-SCAN-Q1-2026", "title": "Q1 2026 Vulnerability Scan Results", "type": "report", "status": "current", "location": "SharePoint/IT/Security/Scans/", "last_updated": "2026-04-03", "owner": "Cybersecurity"},
        {"doc_id": "PATCH-MGMT-LOG", "title": "BES Cyber Asset Patch Management Log", "type": "log", "status": "current", "location": "SharePoint/IT/Security/Patches/", "last_updated": "2026-03-28", "owner": "Cybersecurity"},
        {"doc_id": "IRP-V4", "title": "Incident Response Plan v4.1", "type": "procedure", "status": "current", "location": "SharePoint/IT/Security/IR/", "last_updated": "2025-11-15", "owner": "Cybersecurity"},
        {"doc_id": "SEC-TRAINING-2025", "title": "2025 CIP Security Training Completion Report", "type": "report", "status": "current", "location": "SharePoint/IT/Security/Training/", "last_updated": "2026-01-10", "owner": "HR/Cybersecurity"},
        {"doc_id": "ACCESS-REVIEW-Q1", "title": "Q1 2026 Access Control Review — BES Systems", "type": "review", "status": "current", "location": "SharePoint/IT/Security/Access/", "last_updated": "2026-04-05", "owner": "Cybersecurity"},
        {"doc_id": "NETWORK-MONITOR-GAPS", "title": "Network Monitoring Coverage Gap Analysis", "type": "analysis", "status": "needs_update", "location": "SharePoint/IT/Security/Monitoring/", "last_updated": "2025-06-20", "owner": "Cybersecurity"},
    ],
    "environmental": [
        {"doc_id": "GHG-RPT-2025", "title": "2025 Annual GHG Emissions Report", "type": "report", "status": "current", "location": "SharePoint/Environmental/GHG/", "last_updated": "2026-03-01", "owner": "Environmental"},
        {"doc_id": "CAP-TRADE-COMP", "title": "Cap-and-Trade Compliance Period 4 Filing", "type": "filing", "status": "current", "location": "SharePoint/Environmental/CapTrade/", "last_updated": "2025-11-01", "owner": "Environmental"},
        {"doc_id": "METHANE-LDAR-RPT", "title": "Methane LDAR Survey Results — Gas Distribution", "type": "report", "status": "current", "location": "SharePoint/Environmental/Methane/", "last_updated": "2026-02-15", "owner": "Gas Operations"},
        {"doc_id": "SF6-INVENTORY", "title": "SF6 Switchgear Inventory and Emissions Log", "type": "inventory", "status": "needs_update", "location": "SharePoint/Environmental/SF6/", "last_updated": "2025-04-30", "owner": "Electric Operations"},
        {"doc_id": "EPA-SUBPART-W", "title": "EPA Subpart W Annual Report — GHG Reporting", "type": "filing", "status": "current", "location": "SharePoint/Environmental/EPA/", "last_updated": "2026-03-20", "owner": "Environmental"},
        {"doc_id": "CLEAN-ENERGY-PLAN", "title": "Clean Energy Procurement Plan 2025-2030", "type": "plan", "status": "current", "location": "SharePoint/Environmental/CleanEnergy/", "last_updated": "2025-08-15", "owner": "Energy Procurement"},
    ],
    "grid_reliability": [
        {"doc_id": "TPL-STUDY-2025", "title": "2025 Transmission Planning Study", "type": "study", "status": "current", "location": "SharePoint/Planning/Transmission/", "last_updated": "2025-10-30", "owner": "Transmission Planning"},
        {"doc_id": "CONTINGENCY-ANALYSIS", "title": "N-1-1 Contingency Analysis Report", "type": "analysis", "status": "needs_update", "location": "SharePoint/Planning/Reliability/", "last_updated": "2024-11-15", "owner": "Reliability Engineering"},
        {"doc_id": "EXTREME-WEATHER-SCENARIOS", "title": "Extreme Weather Scenario Modeling Results", "type": "study", "status": "partial", "location": "SharePoint/Planning/Weather/", "last_updated": "2026-02-28", "owner": "Transmission Planning"},
        {"doc_id": "FERC-714-FILING", "title": "FERC Form 714 Annual Filing 2025", "type": "filing", "status": "current", "location": "SharePoint/Planning/FERC/", "last_updated": "2026-04-01", "owner": "Regulatory Affairs"},
    ],
    "pipeline_safety": [
        {"doc_id": "DIMP-2025", "title": "Distribution Integrity Management Program 2025", "type": "plan", "status": "current", "location": "SharePoint/Gas/DIMP/", "last_updated": "2025-12-01", "owner": "Gas Operations"},
        {"doc_id": "TIMP-2025", "title": "Transmission Integrity Management Program 2025", "type": "plan", "status": "current", "location": "SharePoint/Gas/TIMP/", "last_updated": "2025-11-15", "owner": "Gas Operations"},
        {"doc_id": "LEAK-SURVEY-RPT-Q4", "title": "Q4 2025 Leak Survey and Repair Report", "type": "report", "status": "current", "location": "SharePoint/Gas/Leaks/", "last_updated": "2026-01-20", "owner": "Gas Operations"},
        {"doc_id": "LEGACY-PIPE-TRACKER", "title": "Cast Iron & Bare Steel Replacement Tracker", "type": "tracker", "status": "current", "location": "SharePoint/Gas/LegacyPipe/", "last_updated": "2026-03-15", "owner": "Gas Engineering"},
        {"doc_id": "ONE-CALL-METRICS", "title": "One-Call Locate & Mark Performance Metrics", "type": "report", "status": "current", "location": "SharePoint/Gas/OneCall/", "last_updated": "2026-04-01", "owner": "Gas Operations"},
        {"doc_id": "MAOP-RECORDS-AUDIT", "title": "MAOP Records Validation Audit Report", "type": "audit", "status": "needs_update", "location": "SharePoint/Gas/MAOP/", "last_updated": "2024-09-30", "owner": "Gas Engineering"},
    ],
    "worker_safety": [
        {"doc_id": "IIPP-2026", "title": "Injury & Illness Prevention Program 2026", "type": "plan", "status": "current", "location": "SharePoint/Safety/IIPP/", "last_updated": "2026-01-05", "owner": "Safety"},
        {"doc_id": "HEAT-ILLNESS-PLAN", "title": "Heat Illness Prevention Plan (Updated)", "type": "procedure", "status": "current", "location": "SharePoint/Safety/Heat/", "last_updated": "2026-03-10", "owner": "Safety"},
        {"doc_id": "WILDFIRE-SMOKE-PROC", "title": "Wildfire Smoke Exposure Protection Procedures", "type": "procedure", "status": "needs_update", "location": "SharePoint/Safety/Smoke/", "last_updated": "2025-05-20", "owner": "Safety"},
        {"doc_id": "LOTO-AUDIT-2025", "title": "2025 Lockout/Tagout Compliance Audit", "type": "audit", "status": "current", "location": "SharePoint/Safety/LOTO/", "last_updated": "2025-12-18", "owner": "Safety"},
        {"doc_id": "CONTRACTOR-SAFETY-RPT", "title": "Contractor Safety Program Verification Report", "type": "report", "status": "current", "location": "SharePoint/Safety/Contractors/", "last_updated": "2026-02-01", "owner": "Safety/Procurement"},
    ],
    "data_privacy": [
        {"doc_id": "PRIVACY-POLICY-V3", "title": "Customer Data Privacy Policy v3.0", "type": "policy", "status": "needs_update", "location": "SharePoint/Legal/Privacy/", "last_updated": "2024-08-15", "owner": "Legal"},
        {"doc_id": "CCPA-COMPLIANCE-RPT", "title": "CCPA/CPRA Annual Compliance Report 2025", "type": "report", "status": "current", "location": "SharePoint/Legal/Privacy/CCPA/", "last_updated": "2026-03-01", "owner": "Legal"},
        {"doc_id": "DATA-SHARING-REGISTRY", "title": "Third-Party Data Sharing Agreement Registry", "type": "registry", "status": "current", "location": "SharePoint/Legal/Privacy/ThirdParty/", "last_updated": "2026-03-15", "owner": "Legal/IT"},
        {"doc_id": "AMI-DATA-CONSENT", "title": "AMI Data Consent Tracking Report", "type": "report", "status": "partial", "location": "SharePoint/Customer/AMI/", "last_updated": "2025-11-30", "owner": "Customer Operations"},
    ],
    "ai_governance": [
        {"doc_id": "AI-POLICY-DRAFT", "title": "AI Governance Policy — Draft", "type": "policy", "status": "draft", "location": "SharePoint/IT/AI/", "last_updated": "2026-02-01", "owner": "IT/Legal"},
        {"doc_id": "AI-INVENTORY", "title": "AI/ML Systems Inventory and Risk Assessment", "type": "inventory", "status": "partial", "location": "SharePoint/IT/AI/Inventory/", "last_updated": "2026-01-15", "owner": "IT"},
        {"doc_id": "AI-BIAS-AUDIT-2025", "title": "2025 AI Bias Audit — Customer Systems", "type": "audit", "status": "current", "location": "SharePoint/IT/AI/Audits/", "last_updated": "2025-12-20", "owner": "IT/Compliance"},
    ],
}


# --- Audit types + the obligations each one tests (Energy & Utilities pack) ---
# Other industry packs supply their own via core/domains.py -> pack["audit_types"].
ENERGY_AUDIT_TYPES = {
    "OEIS Wildfire Mitigation Plan Audit": [
        {"id": "WF-001", "text": "Semi-annual vegetation inspection in Tier 3 HFTDs", "category": "vegetation", "deadline": "2026-06-30"},
        {"id": "WF-002", "text": "Underground 300 circuit-miles in HFTDs", "category": "grid_hardening", "deadline": "2027-12-31"},
        {"id": "WF-003", "text": "50% reduction in PSPS events vs 2024 baseline", "category": "psps", "deadline": "2026-12-31"},
        {"id": "WF-004", "text": "Deploy HD cameras at 100% of Tier 3 transmission structures", "category": "monitoring", "deadline": "2026-06-30"},
        {"id": "WF-005", "text": "Quarterly compliance reports within 30 days", "category": "reporting", "deadline": "Ongoing"},
        {"id": "WF-006", "text": "Covered conductor on all new Tier 2/3 construction", "category": "grid_hardening", "deadline": "2026-01-01"},
        {"id": "WF-007", "text": "Sectionalizing devices on critical facility circuits", "category": "grid_hardening", "deadline": "2026-12-31"},
        {"id": "WF-008", "text": "AI-powered fire detection system deployment", "category": "technology", "deadline": "2026-06-30"},
    ],
    "NERC CIP Cybersecurity Audit": [
        {"id": "CIP-001", "text": "Network security monitoring for high/medium BES Cyber Systems", "category": "monitoring", "deadline": "2027-10-01"},
        {"id": "CIP-002", "text": "90-day network data retention", "category": "data_retention", "deadline": "2027-10-01"},
        {"id": "CIP-003", "text": "Quarterly anomaly detection baseline updates", "category": "detection", "deadline": "Ongoing"},
        {"id": "CIP-004", "text": "95% ESP network traffic monitoring coverage", "category": "coverage", "deadline": "2027-10-01"},
        {"id": "CIP-005", "text": "Critical security patches within 35 days", "category": "patch_management", "deadline": "Ongoing"},
        {"id": "CIP-006", "text": "Physical Security Perimeter access controls", "category": "physical_security", "deadline": "Ongoing"},
        {"id": "CIP-007", "text": "Annual CIP security training completion", "category": "training", "deadline": "2026-12-31"},
        {"id": "CIP-008", "text": "Low-impact BES electronic access controls", "category": "access_control", "deadline": "2026-06-30"},
    ],
    "CARB Emissions Compliance Audit": [
        {"id": "EM-001", "text": "Monthly GHG emissions reporting", "category": "reporting", "deadline": "2026-07-01"},
        {"id": "EM-002", "text": "Methane leak detection protocol", "category": "monitoring", "deadline": "2026-07-01"},
        {"id": "EM-003", "text": "Allowance proceeds ratepayer benefit", "category": "financial", "deadline": "2026-12-31"},
        {"id": "EM-004", "text": "SF6 switchgear emissions tracking", "category": "reporting", "deadline": "Ongoing"},
        {"id": "EM-005", "text": "EPA Subpart W annual reporting", "category": "reporting", "deadline": "2026-03-31"},
    ],
    "FERC Transmission Planning Review": [
        {"id": "TP-001", "text": "Model 3+ extreme weather scenarios", "category": "planning", "deadline": "2026-06-30"},
        {"id": "TP-002", "text": "Weather-correlated N-1-1 contingency analysis", "category": "reliability", "deadline": "2026-06-30"},
        {"id": "TP-003", "text": "Updated planning criteria filing (Order 901)", "category": "filing", "deadline": "2026-05-20"},
        {"id": "TP-004", "text": "Regional weather assumption coordination", "category": "coordination", "deadline": "2026-06-30"},
    ],
    "PHMSA Pipeline Safety Audit": [
        {"id": "PS-001", "text": "Advanced leak detection (100% system coverage)", "category": "monitoring", "deadline": "2028-01-01"},
        {"id": "PS-002", "text": "Grade 2 leak repair within 6 months", "category": "maintenance", "deadline": "2026-07-01"},
        {"id": "PS-003", "text": "Quarterly methane emissions reports", "category": "reporting", "deadline": "2027-03-31"},
        {"id": "PS-004", "text": "5% annual legacy pipe replacement", "category": "infrastructure", "deadline": "Ongoing"},
        {"id": "PS-005", "text": "GPS-enabled locates, 1-hour emergency response", "category": "operations", "deadline": "2026-12-31"},
    ],
    "Cal-OSHA Worker Safety Audit": [
        {"id": "WS-001", "text": "Heat illness plan — 87°F threshold", "category": "heat_safety", "deadline": "2026-04-01"},
        {"id": "WS-002", "text": "Smoke protection — N95 when AQI >151", "category": "smoke_safety", "deadline": "2026-04-01"},
        {"id": "WS-003", "text": "Contractor safety quarterly verification", "category": "contractor", "deadline": "Ongoing"},
        {"id": "WS-004", "text": "Safety training in primary language", "category": "training", "deadline": "2026-12-31"},
        {"id": "WS-005", "text": "Lockout/tagout compliance", "category": "electrical_safety", "deadline": "Ongoing"},
    ],
    "Customer Data Privacy Audit": [
        {"id": "DP-001", "text": "AMI data explicit opt-in consent", "category": "consent", "deadline": "2026-07-01"},
        {"id": "DP-002", "text": "72-hour breach notification", "category": "breach", "deadline": "2026-07-01"},
        {"id": "DP-003", "text": "Green Button Connect My Data API", "category": "data_access", "deadline": "2026-07-01"},
        {"id": "DP-004", "text": "AI data anonymization (k>=5)", "category": "ai_privacy", "deadline": "2026-07-01"},
    ],
}


def plan_audit(state: AuditState) -> AuditState:
    """Supervisor: Plan the audit preparation approach."""
    llm = get_openai_primary()

    prompt = f"""As the Audit Preparation Supervisor, plan the audit preparation approach.

AUDIT SCOPE: {state['audit_scope']}
REGULATIONS IN SCOPE: {json.dumps(state['regulations'])}
OBLIGATIONS TO VERIFY: {json.dumps(state['obligations'], indent=2)}

Create an audit preparation plan as JSON:
{{
    "audit_areas": ["categorized list of audit focus areas"],
    "evidence_needed_per_area": {{
        "area_name": ["types of evidence needed"]
    }},
    "priority_order": ["areas ranked by risk/importance"],
    "estimated_preparation_effort": "description",
    "key_risks": ["potential gaps or issues to watch for"]
}}"""

    response = llm.invoke([
        SystemMessage(content=get_prompt("audit_supervisor")),
        HumanMessage(content=prompt)
    ])

    try:
        content = response.content
        plan = json.loads(content[content.find("{"):content.rfind("}") + 1])
    except (json.JSONDecodeError, ValueError):
        plan = {
            "audit_areas": [],
            "evidence_needed_per_area": {},
            "priority_order": [],
            "estimated_preparation_effort": "unknown",
            "key_risks": [],
            "parse_error": "Supervisor plan could not be parsed as JSON",
        }

    return {**state, "audit_plan": plan, "current_step": "collect_evidence"}


def collect_evidence(state: AuditState) -> AuditState:
    """Evidence Collector: Gather and validate evidence for each obligation."""
    llm = get_openai_primary()

    # Evidence repository for the ACTIVE industry domain pack
    all_evidence = []
    for category, docs in get_domain()["evidence"].items():
        for doc in docs:
            all_evidence.append({**doc, "category": category})

    prompt = f"""As the Evidence Collector, map available evidence to each obligation.

The Supervisor has produced this audit plan. Work to it — cover every audit area it identifies,
and prioritise in the order it sets.

SUPERVISOR'S AUDIT PLAN:
{json.dumps(state.get('audit_plan', {}), indent=2)}

OBLIGATIONS:
{json.dumps(state['obligations'], indent=2)}

AVAILABLE EVIDENCE INVENTORY:
{json.dumps(all_evidence, indent=2)}

For each obligation, assess evidence coverage:
[
    {{
        "obligation_id": "from the obligations list",
        "obligation_summary": "brief description",
        "evidence_found": [
            {{
                "doc_id": "matching evidence doc ID",
                "relevance": "direct|supporting|partial",
                "sufficiency": "sufficient|partial|insufficient",
                "notes": "any concerns about this evidence"
            }}
        ],
        "evidence_status": "complete|partial|missing",
        "missing_evidence": ["description of what's still needed"],
        "recommended_sources": ["where to find missing evidence"]
    }}
]"""

    response = llm.invoke([
        SystemMessage(content=get_prompt("audit_evidence")),
        HumanMessage(content=prompt)
    ])

    try:
        content = response.content
        evidence = json.loads(content[content.find("["):content.rfind("]") + 1])
    except (json.JSONDecodeError, ValueError):
        evidence = [{"obligation_id": "ALL", "evidence_status": "error", "notes": "Failed to parse evidence mapping"}]

    return {**state, "evidence_inventory": evidence, "current_step": "analyze_gaps"}


def analyze_gaps(state: AuditState) -> AuditState:
    """Gap Analyzer: Identify and prioritize compliance gaps."""
    llm = get_openai_primary()

    prompt = f"""As the Gap Analyzer, identify compliance gaps based on evidence assessment.

The Supervisor flagged these key risks to watch for — check each one explicitly:
{json.dumps(state.get('audit_plan', {}).get('key_risks', []), indent=2)}

OBLIGATIONS:
{json.dumps(state['obligations'], indent=2)}

EVIDENCE INVENTORY:
{json.dumps(state['evidence_inventory'], indent=2)}

For each gap found:
[
    {{
        "gap_id": "unique ID",
        "obligation_id": "related obligation",
        "gap_type": "missing_evidence|outdated_evidence|partial_compliance|process_gap|documentation_gap",
        "description": "clear description of the gap",
        "severity": "critical|high|medium|low",
        "audit_risk": "What could happen if auditor finds this gap",
        "remediation": {{
            "action": "what needs to be done",
            "owner": "responsible department",
            "effort": "hours or days estimate",
            "deadline": "when this must be resolved"
        }},
        "interim_mitigation": "what can be done immediately to reduce risk"
    }}
]"""

    response = llm.invoke([
        SystemMessage(content=get_prompt("audit_gap")),
        HumanMessage(content=prompt)
    ])

    try:
        content = response.content
        gaps = json.loads(content[content.find("["):content.rfind("]") + 1])
    except (json.JSONDecodeError, ValueError):
        gaps = []

    return {**state, "gap_analysis": gaps, "current_step": "draft_responses"}


def draft_responses(state: AuditState) -> AuditState:
    """Response Drafter: Prepare professional audit responses."""
    llm = get_openai_primary()

    prompt = f"""As the Response Drafter, prepare professional audit responses.

Draft one response per audit area identified in the Supervisor's plan.

SUPERVISOR'S AUDIT AREAS: {json.dumps(state.get('audit_plan', {}).get('audit_areas', []), indent=2)}

AUDIT SCOPE: {state['audit_scope']}
OBLIGATIONS: {json.dumps(state['obligations'], indent=2)}
EVIDENCE: {json.dumps(state['evidence_inventory'], indent=2)}
GAPS: {json.dumps(state['gap_analysis'], indent=2)}

Draft responses for each audit area:
[
    {{
        "area": "audit area name",
        "response_narrative": "Professional response text suitable for regulatory submission (2-3 paragraphs)",
        "evidence_citations": ["list of evidence documents cited"],
        "compliance_status": "full|substantial|partial|non_compliant",
        "corrective_actions": [
            {{
                "action": "description",
                "owner": "department",
                "target_date": "date",
                "status": "planned|in_progress|completed"
            }}
        ],
        "risk_mitigation": "how risks are being addressed"
    }}
]"""

    response = llm.invoke([
        SystemMessage(content=get_prompt("audit_response")),
        HumanMessage(content=prompt)
    ])

    try:
        content = response.content
        responses = json.loads(content[content.find("["):content.rfind("]") + 1])
    except (json.JSONDecodeError, ValueError):
        responses = [{"area": "General", "response_narrative": response.content[:1000], "compliance_status": "unknown"}]

    return {**state, "draft_responses": responses, "current_step": "supervisor_review"}


def supervisor_review(state: AuditState) -> AuditState:
    """Supervisor: Review completeness and quality of audit package."""
    llm = get_openai_primary()

    prompt = f"""As the Audit Supervisor, review the complete audit preparation package.

This was YOUR plan. Assess whether the specialist agents actually covered it — call out any audit
area or key risk from the plan that the evidence, gaps or responses failed to address.

YOUR ORIGINAL PLAN:
{json.dumps(state.get('audit_plan', {}), indent=2)}

EVIDENCE COLLECTED: {len(state['evidence_inventory'])} items
GAPS IDENTIFIED: {len(state['gap_analysis'])} gaps
RESPONSES DRAFTED: {len(state['draft_responses'])} areas

EVIDENCE SUMMARY: {json.dumps(state['evidence_inventory'][:5], indent=2)}
GAP SUMMARY: {json.dumps(state['gap_analysis'][:5], indent=2)}
RESPONSE SUMMARY: {json.dumps(state['draft_responses'][:3], indent=2)}

Provide supervisor assessment:
{{
    "overall_readiness": "ready|mostly_ready|significant_gaps|not_ready",
    "readiness_score": 0-100,
    "executive_summary": "2-3 paragraph summary for audit committee",
    "critical_items": ["items requiring immediate executive attention"],
    "strengths": ["areas where PG&E is well-prepared"],
    "weaknesses": ["areas of concern"],
    "recommendations": ["prioritized list of actions before audit"],
    "timeline_assessment": "whether PG&E can be ready by audit date"
}}"""

    response = llm.invoke([
        SystemMessage(content=get_prompt("audit_supervisor")),
        HumanMessage(content=prompt)
    ])

    try:
        content = response.content
        review = json.loads(content[content.find("{"):content.rfind("}") + 1])
    except (json.JSONDecodeError, ValueError):
        review = {"overall_readiness": "unknown", "executive_summary": response.content[:500]}

    final_package = {
        "audit_scope": state["audit_scope"],
        "audit_plan": state.get("audit_plan", {}),
        "evidence_inventory": state["evidence_inventory"],
        "gap_analysis": state["gap_analysis"],
        "draft_responses": state["draft_responses"],
        "supervisor_review": review,
        "review_status": "PENDING_HUMAN_REVIEW",
        "disclaimer": (
            "AI-generated decision support. Not a compliance determination. Every obligation, gap and "
            "drafted response requires review and sign-off by qualified personnel before use, and no "
            "content may be submitted to a regulator without that sign-off."
        ),
    }

    return {**state, "supervisor_review": review, "final_package": final_package, "current_step": "complete"}


def build_audit_graph() -> StateGraph:
    """Build the multi-agent audit preparation graph."""
    workflow = StateGraph(AuditState)

    workflow.add_node("plan", plan_audit)
    workflow.add_node("collect_evidence", collect_evidence)
    workflow.add_node("analyze_gaps", analyze_gaps)
    workflow.add_node("draft_responses", draft_responses)
    workflow.add_node("supervisor_review", supervisor_review)

    workflow.set_entry_point("plan")
    workflow.add_edge("plan", "collect_evidence")
    workflow.add_edge("collect_evidence", "analyze_gaps")
    workflow.add_edge("analyze_gaps", "draft_responses")
    workflow.add_edge("draft_responses", "supervisor_review")
    workflow.add_edge("supervisor_review", END)

    return workflow.compile()


def run_audit_preparation(
    audit_scope: str,
    regulations: list[str],
    obligations: list[dict]
) -> dict:
    """Run full audit preparation workflow."""
    graph = build_audit_graph()

    initial_state: AuditState = {
        "audit_scope": audit_scope,
        "regulations": regulations,
        "obligations": obligations,
        "audit_plan": {},
        "evidence_inventory": [],
        "gap_analysis": [],
        "draft_responses": [],
        "supervisor_review": {},
        "final_package": {},
        "current_step": "plan",
        "iteration": 0,
    }

    return graph.invoke(initial_state)
```

## `agents/case_analytics/__init__.py`

```python
from agents.case_analytics.chain import run_case_analytics, search_cases, get_case_stats
```

## `agents/case_analytics/chain.py`

```python
"""
Case Analytics - RAG Chain (Gen AI)
Retrieval-heavy analysis of historical CPUC/FERC enforcement cases.
"""

import json
from langchain_core.messages import HumanMessage, SystemMessage

from core.llm import get_openai_primary
from core.prompts import get_prompt
from core.domains import get_domain, get_active_domain_key
from core.vectorstore import search_documents, add_documents, COLLECTION_CASES


def _cases_collection() -> str:
    """Namespace the case collection per industry so corpora never bleed across domains."""
    return f"{COLLECTION_CASES}_{get_active_domain_key()}"

# --- Sample Historical Case Data (28 cases across 7 regulators) ---
SAMPLE_CASES = [
    # ==================== CPUC — WILDFIRE & SAFETY ====================
    {
        "case_number": "I.19-06-015",
        "case_title": "Investigation into PG&E Safety Culture and Governance",
        "regulator": "CPUC",
        "case_type": "investigation",
        "status": "resolved",
        "filing_date": "2019-06-27",
        "resolution_date": "2022-06-02",
        "penalty_amount": 0,
        "summary": "CPUC investigation into PG&E's safety culture following 2017-2018 wildfire events. Resulted in Enhanced Oversight and Enforcement Process (EOEP) with independent safety monitor.",
        "key_findings": "Deficient safety culture; inadequate vegetation management; insufficient grid hardening investment; poor organizational accountability.",
        "precedent_tags": "safety_culture,wildfire,enhanced_oversight,governance"
    },
    {
        "case_number": "A.20-06-012",
        "case_title": "PG&E 2020 Wildfire Mitigation Plan",
        "regulator": "CPUC",
        "case_type": "application",
        "status": "resolved",
        "filing_date": "2020-06-05",
        "resolution_date": "2021-02-11",
        "penalty_amount": 0,
        "summary": "Review of PG&E's Wildfire Mitigation Plan. CPUC approved with conditions including accelerated undergrounding and enhanced vegetation management in HFTDs.",
        "key_findings": "WMP generally adequate; need for faster implementation of grid hardening; PSPS reduction targets set; quarterly reporting requirements imposed.",
        "precedent_tags": "wildfire,wmp,undergrounding,vegetation,psps"
    },
    {
        "case_number": "I.19-11-013",
        "case_title": "Investigation into 2019 Kincade Fire",
        "regulator": "CPUC",
        "case_type": "enforcement",
        "status": "resolved",
        "filing_date": "2019-11-21",
        "resolution_date": "2023-09-14",
        "penalty_amount": 50000000,
        "summary": "CPUC investigation into the Kincade Fire caused by PG&E transmission equipment. Resulted in $50M settlement including penalties and safety improvements.",
        "key_findings": "Transmission tower failure; inadequate inspection of aging infrastructure; weather monitoring gaps.",
        "precedent_tags": "wildfire,enforcement,transmission,inspection,penalty"
    },
    {
        "case_number": "I.18-12-007",
        "case_title": "Investigation into 2018 Camp Fire (Town of Paradise)",
        "regulator": "CPUC",
        "case_type": "enforcement",
        "status": "resolved",
        "filing_date": "2018-12-11",
        "resolution_date": "2022-09-29",
        "penalty_amount": 13500000000,
        "summary": "Investigation into the Camp Fire that destroyed the town of Paradise, killing 85 people. PG&E pled guilty to 84 counts of involuntary manslaughter. Total liability exceeding $13.5B through bankruptcy proceedings, victim fund, and settlements.",
        "key_findings": "Failure to maintain aging transmission equipment (C-hook on Caribou-Palermo line); inadequate inspection programs; ignored known equipment risks; systemic failure to prioritize safety over cost reduction.",
        "precedent_tags": "wildfire,enforcement,catastrophic,fatalities,bankruptcy,criminal,record_penalty,camp_fire"
    },
    {
        "case_number": "I.17-11-003",
        "case_title": "Investigation into 2017 Northern California Wildfires",
        "regulator": "CPUC",
        "case_type": "enforcement",
        "status": "resolved",
        "filing_date": "2017-11-07",
        "resolution_date": "2021-05-20",
        "penalty_amount": 2140000000,
        "summary": "Investigation into multiple wildfires in Sonoma, Napa, and surrounding counties (Tubbs, Atlas, Redwood Valley fires). Total liabilities of $2.14B through insurance subrogation and victim settlements.",
        "key_findings": "Vegetation contact with power lines; inadequate tree trimming cycles; delayed de-energization decisions; failure to account for extreme wind conditions in operational planning.",
        "precedent_tags": "wildfire,enforcement,vegetation,multiple_fires,penalty,tubbs_fire"
    },
    {
        "case_number": "I.20-08-019",
        "case_title": "Investigation into 2020 Zogg Fire",
        "regulator": "CPUC",
        "case_type": "enforcement",
        "status": "resolved",
        "filing_date": "2020-08-22",
        "resolution_date": "2024-03-15",
        "penalty_amount": 110000000,
        "summary": "Investigation into the Zogg Fire in Shasta County that killed 4 people, caused by a gray pine tree contacting PG&E distribution lines. $110M in penalties and corrective actions.",
        "key_findings": "Tree previously identified as requiring removal but not removed; vegetation management backlog; inadequate risk prioritization for high-fire-threat zones.",
        "precedent_tags": "wildfire,enforcement,vegetation,fatalities,penalty,zogg_fire"
    },
    {
        "case_number": "I.21-06-021",
        "case_title": "Investigation into 2021 Dixie Fire",
        "regulator": "CPUC",
        "case_type": "enforcement",
        "status": "active",
        "filing_date": "2021-06-30",
        "resolution_date": None,
        "penalty_amount": 0,
        "summary": "Ongoing investigation into the Dixie Fire, the largest single (non-complex) fire in California history at 963,309 acres. Caused by a tree falling on PG&E power line near Cresta Dam.",
        "key_findings": "Pending final determination; preliminary findings include delayed de-energization, vegetation management gaps, aging infrastructure near hydroelectric facilities.",
        "precedent_tags": "wildfire,investigation,active,dixie_fire,largest_fire,pending"
    },
    # ==================== CPUC — PIPELINE SAFETY ====================
    {
        "case_number": "I.15-08-019",
        "case_title": "Investigation into San Bruno Gas Pipeline Explosion",
        "regulator": "CPUC",
        "case_type": "enforcement",
        "status": "resolved",
        "filing_date": "2015-08-06",
        "resolution_date": "2017-04-09",
        "penalty_amount": 1600000000,
        "summary": "Investigation resulting from the 2010 San Bruno gas pipeline explosion that killed 8 people. Record $1.6B penalty including $900M in pipeline safety improvements and $400M fine.",
        "key_findings": "Inadequate pipeline records; failure to identify threats; insufficient pipeline testing; organizational failures in gas operations safety management.",
        "precedent_tags": "pipeline_safety,penalty,enforcement,gas_operations,record_penalty,san_bruno"
    },
    {
        "case_number": "I.12-01-007",
        "case_title": "Investigation into PG&E Natural Gas Distribution Pipeline Records",
        "regulator": "CPUC",
        "case_type": "investigation",
        "status": "resolved",
        "filing_date": "2012-01-12",
        "resolution_date": "2015-12-17",
        "penalty_amount": 38000000,
        "summary": "Follow-on investigation into PG&E's gas pipeline recordkeeping practices. Found systemic deficiencies in Maximum Allowable Operating Pressure (MAOP) records. $38M penalty.",
        "key_findings": "Incomplete pipeline records dating back decades; inability to verify MAOP for hundreds of pipeline segments; inadequate data management systems; records retention failures.",
        "precedent_tags": "pipeline_safety,records,penalty,gas_operations,maop,data_management"
    },
    {
        "case_number": "I.17-02-002",
        "case_title": "PG&E Gas Safety OII — Locate and Mark Practices",
        "regulator": "CPUC",
        "case_type": "enforcement",
        "status": "resolved",
        "filing_date": "2017-02-14",
        "resolution_date": "2019-08-22",
        "penalty_amount": 14000000,
        "summary": "Investigation into PG&E's One-Call locate and mark practices for underground gas facilities. Found pattern of late or missed locates creating third-party dig-in risks. $14M penalty.",
        "key_findings": "Chronic late responses to One-Call requests; insufficient locate crews; inaccurate facility maps; multiple third-party dig-in incidents traceable to PG&E failures.",
        "precedent_tags": "pipeline_safety,enforcement,one_call,locate_mark,penalty,dig_in"
    },
    # ==================== CPUC — RATE CASES & FINANCIAL ====================
    {
        "case_number": "A.21-06-021",
        "case_title": "PG&E 2023 General Rate Case",
        "regulator": "CPUC",
        "case_type": "rate_case",
        "status": "resolved",
        "filing_date": "2021-06-30",
        "resolution_date": "2023-11-16",
        "penalty_amount": 0,
        "summary": "PG&E's General Rate Case for 2023-2026. Authorized revenue requirement of ~$15.7B over 4 years. Included significant wildfire safety and grid modernization investments.",
        "key_findings": "Rate increases approved for safety investments; undergrounding program funded; customer affordability concerns noted; performance metrics tied to rate recovery.",
        "precedent_tags": "rate_case,revenue_requirement,grid_modernization,affordability"
    },
    {
        "case_number": "A.23-11-006",
        "case_title": "PG&E 2027 General Rate Case Application",
        "regulator": "CPUC",
        "case_type": "rate_case",
        "status": "active",
        "filing_date": "2023-11-15",
        "resolution_date": None,
        "penalty_amount": 0,
        "summary": "PG&E's General Rate Case for 2027-2030 cycle. Requesting approximately $18.2B in revenue requirements over 4 years for grid modernization, wildfire hardening, and clean energy transition.",
        "key_findings": "Pending decision; intervenors contesting affordability; rate impact estimated at 8-12% increase; CPUC balancing safety investment with customer bill concerns.",
        "precedent_tags": "rate_case,active,revenue_requirement,affordability,grid_modernization,clean_energy"
    },
    {
        "case_number": "A.22-04-008",
        "case_title": "PG&E Undergrounding Program Cost Recovery",
        "regulator": "CPUC",
        "case_type": "application",
        "status": "resolved",
        "filing_date": "2022-04-12",
        "resolution_date": "2024-01-25",
        "penalty_amount": 0,
        "summary": "PG&E application for 10,000-mile undergrounding program under SB 884. Approved with cost cap of $5.9M per mile for Tier 3 HFTD segments. Total approved program cost ~$20B over 10 years.",
        "key_findings": "Cost benchmarks established; unit cost accountability; independent monitor required; quarterly progress reporting; cost overruns above cap borne by shareholders.",
        "precedent_tags": "undergrounding,cost_recovery,wildfire,grid_hardening,sb_884,capital_investment"
    },
    # ==================== CPUC — RULEMAKING & DATA PRIVACY ====================
    {
        "case_number": "R.18-10-007",
        "case_title": "Rulemaking on Microgrids and Resiliency",
        "regulator": "CPUC",
        "case_type": "rulemaking",
        "status": "active",
        "filing_date": "2018-10-25",
        "resolution_date": None,
        "penalty_amount": 0,
        "summary": "Ongoing rulemaking to develop policies for microgrids and resiliency strategies. Addresses community resilience to PSPS events and grid outages.",
        "key_findings": "Microgrid interconnection standards evolving; community resiliency investments growing; distributed energy resources integration challenges.",
        "precedent_tags": "microgrid,resiliency,psps,distributed_energy,rulemaking"
    },
    {
        "case_number": "R.19-09-009",
        "case_title": "Order Instituting Rulemaking on Customer Data Privacy",
        "regulator": "CPUC",
        "case_type": "rulemaking",
        "status": "resolved",
        "filing_date": "2019-09-12",
        "resolution_date": "2023-07-20",
        "penalty_amount": 0,
        "summary": "Rulemaking updating customer data access and privacy rules for utilities under CCPA and beyond. Established new rules for third-party data sharing, AMI data access, and customer consent frameworks.",
        "key_findings": "Enhanced consent requirements for energy usage data; standardized data formats for third-party access; Green Button Connect My Data adoption required; opt-in for behavioral analytics.",
        "precedent_tags": "data_privacy,ccpa,customer_data,ami,rulemaking,third_party_access"
    },
    # ==================== NERC/FERC — CYBERSECURITY & RELIABILITY ====================
    {
        "case_number": "NP22-4-000",
        "case_title": "NERC Enforcement Action: CIP Reliability Standard Violations",
        "regulator": "NERC/FERC",
        "case_type": "enforcement",
        "status": "resolved",
        "filing_date": "2022-03-15",
        "resolution_date": "2022-12-01",
        "penalty_amount": 2750000,
        "summary": "NERC enforcement action against a major western utility for CIP-007-6 (Systems Security Management) and CIP-010-2 (Configuration Management) violations.",
        "key_findings": "Unpatched cyber assets; configuration baselines not maintained; insufficient monitoring of security events within ESP.",
        "precedent_tags": "cybersecurity,nerc_cip,enforcement,penalty,configuration_management"
    },
    {
        "case_number": "NP23-12-000",
        "case_title": "NERC CIP-003-8 Enforcement: Low-Impact BES Cyber Systems",
        "regulator": "NERC/FERC",
        "case_type": "enforcement",
        "status": "resolved",
        "filing_date": "2023-12-05",
        "resolution_date": "2024-06-18",
        "penalty_amount": 1500000,
        "summary": "Enforcement action for CIP-003-8 violations related to electronic access controls for low-impact BES Cyber Systems at multiple substations. $1.5M penalty with mitigation plan.",
        "key_findings": "Insufficient access controls at 23 substations; routable protocol connections without monitoring; default credentials found on field devices; incomplete asset inventory for low-impact systems.",
        "precedent_tags": "cybersecurity,nerc_cip,enforcement,penalty,substations,access_control,low_impact"
    },
    {
        "case_number": "NP21-8-000",
        "case_title": "NERC CIP-006/CIP-007 Physical and Systems Security Violations",
        "regulator": "NERC/FERC",
        "case_type": "enforcement",
        "status": "resolved",
        "filing_date": "2021-08-10",
        "resolution_date": "2022-03-28",
        "penalty_amount": 3800000,
        "summary": "Major enforcement action for combined physical security (CIP-006) and systems security (CIP-007) violations at critical control centers. $3.8M penalty — one of the largest NERC CIP penalties in the western region.",
        "key_findings": "Physical Security Perimeter breaches (tailgating incidents); visitor escort failures; patch management delays exceeding 90 days; 12 high-impact assets with unpatched critical vulnerabilities.",
        "precedent_tags": "cybersecurity,nerc_cip,enforcement,penalty,physical_security,patch_management,control_center"
    },
    {
        "case_number": "IN24-2-000",
        "case_title": "FERC Order 887 Compliance: Transmission Incentive Rate Audit",
        "regulator": "FERC",
        "case_type": "audit",
        "status": "resolved",
        "filing_date": "2024-02-20",
        "resolution_date": "2024-11-05",
        "penalty_amount": 0,
        "summary": "FERC audit of transmission incentive rate filings under Order 887. No penalties assessed but findings requiring corrective action on cost allocation methodology.",
        "key_findings": "Transmission planning inputs inconsistent with actual costs; some incentive claims lacked sufficient documentation; recommended improvements to cost-benefit analysis for transmission projects.",
        "precedent_tags": "ferc,audit,transmission,rate_incentive,cost_allocation,compliance"
    },
    {
        "case_number": "NP24-6-000",
        "case_title": "NERC FAC-008 Facility Ratings Violation — Transmission Owner",
        "regulator": "NERC/FERC",
        "case_type": "enforcement",
        "status": "resolved",
        "filing_date": "2024-06-12",
        "resolution_date": "2025-01-30",
        "penalty_amount": 850000,
        "summary": "Enforcement for facility ratings methodology violations (FAC-008-3). Incorrect thermal ratings on 47 transmission line segments led to potential overloading risks. $850K penalty.",
        "key_findings": "Outdated conductor specifications in ratings database; ambient temperature assumptions not updated since 2015; 47 line segments rated 8-15% above actual capacity; no validation process for legacy rating data.",
        "precedent_tags": "nerc,enforcement,facility_ratings,transmission,penalty,thermal_ratings"
    },
    # ==================== CARB — ENVIRONMENTAL ====================
    {
        "case_number": "IN22-007",
        "case_title": "CARB Cap-and-Trade Compliance Audit — Western Utility",
        "regulator": "CARB",
        "case_type": "audit",
        "status": "resolved",
        "filing_date": "2022-06-01",
        "resolution_date": "2023-03-15",
        "penalty_amount": 1200000,
        "summary": "CARB audit finding that a western utility underreported GHG emissions from natural gas distribution system methane leaks. $1.2M penalty and enhanced monitoring requirements.",
        "key_findings": "Methane leak quantification methodology deficient; incomplete facility reporting; monitoring gaps in remote facilities.",
        "precedent_tags": "environmental,emissions,cap_and_trade,penalty,methane,reporting"
    },
    {
        "case_number": "CARB-ENF-2024-042",
        "case_title": "CARB MRR Reporting Deficiency — Natural Gas Utility",
        "regulator": "CARB",
        "case_type": "enforcement",
        "status": "resolved",
        "filing_date": "2024-03-22",
        "resolution_date": "2024-10-08",
        "penalty_amount": 750000,
        "summary": "Enforcement action for Mandatory Reporting Regulation (MRR) deficiencies in natural gas compressor station emissions reporting. $750K penalty with requirement to install continuous emissions monitors.",
        "key_findings": "Emission factors for compressor stations not site-specific; quarterly leak detection not performed at 6 facilities; fugitive emissions underestimated by 22%; third-party verifier raised concerns in prior year.",
        "precedent_tags": "environmental,emissions,mrr,penalty,compressor_station,methane,monitoring"
    },
    {
        "case_number": "CARB-ENF-2023-089",
        "case_title": "SF6 Switchgear Emissions Reporting — Electric Utility",
        "regulator": "CARB",
        "case_type": "enforcement",
        "status": "resolved",
        "filing_date": "2023-09-14",
        "resolution_date": "2024-04-30",
        "penalty_amount": 500000,
        "summary": "Enforcement for underreporting sulfur hexafluoride (SF6) emissions from high-voltage switchgear. SF6 has 23,500x the global warming potential of CO2. $500K penalty.",
        "key_findings": "SF6 inventory tracking spreadsheet errors; 14 switchgear units not included in reporting; leak rate calculations used incorrect nameplate capacities; no automated SF6 monitoring system.",
        "precedent_tags": "environmental,sf6,emissions,penalty,switchgear,reporting,high_gwp"
    },
    # ==================== PHMSA — PIPELINE SAFETY (Federal) ====================
    {
        "case_number": "PHMSA-2020-1002",
        "case_title": "PHMSA Gas Transmission Pipeline Safety Enforcement",
        "regulator": "PHMSA",
        "case_type": "enforcement",
        "status": "resolved",
        "filing_date": "2020-10-15",
        "resolution_date": "2022-07-22",
        "penalty_amount": 3200000,
        "summary": "PHMSA enforcement action for violations of 49 CFR 192 (Transportation of Natural Gas by Pipeline). Found 14 probable violations related to integrity management, corrosion control, and emergency response at PG&E gas transmission facilities. $3.2M penalty.",
        "key_findings": "Integrity management program deficiencies; corrosion control failures at 7 pipeline crossings; inadequate SCADA monitoring at 3 compressor stations; emergency response plan not updated for 2 years.",
        "precedent_tags": "pipeline_safety,phmsa,enforcement,penalty,integrity_management,corrosion,federal"
    },
    {
        "case_number": "PHMSA-2023-0078",
        "case_title": "PHMSA Gas Distribution Integrity Management Violations",
        "regulator": "PHMSA",
        "case_type": "enforcement",
        "status": "resolved",
        "filing_date": "2023-07-18",
        "resolution_date": "2024-08-30",
        "penalty_amount": 1800000,
        "summary": "PHMSA enforcement for Distribution Integrity Management Program (DIMP) violations under 49 CFR 192 Subpart P. Found deficiencies in leak management and risk ranking for aging infrastructure. $1.8M penalty.",
        "key_findings": "Risk ranking algorithm did not adequately weight pipe age and material (cast iron/bare steel); 892 open Grade 2 leaks exceeding repair timelines; incomplete excavation damage tracking; DIMP threat analysis not updated for 3 years.",
        "precedent_tags": "pipeline_safety,phmsa,enforcement,penalty,dimp,leak_management,aging_infrastructure"
    },
    # ==================== Cal-OSHA — WORKER SAFETY ====================
    {
        "case_number": "DOSH-2022-0456",
        "case_title": "Cal-OSHA Citation: Powerline Worker Electrocution",
        "regulator": "Cal-OSHA",
        "case_type": "enforcement",
        "status": "resolved",
        "filing_date": "2022-04-18",
        "resolution_date": "2023-01-09",
        "penalty_amount": 425000,
        "summary": "Cal-OSHA serious citations following the electrocution death of a PG&E lineworker during de-energized line maintenance. Found minimum approach distance violations and lockout/tagout failures. $425K penalty.",
        "key_findings": "Minimum approach distance not maintained; lockout/tagout procedures not followed; inadequate job briefing documentation; crew foreman failed to verify de-energized status before work commenced.",
        "precedent_tags": "worker_safety,cal_osha,enforcement,penalty,electrocution,fatality,lockout_tagout"
    },
    {
        "case_number": "DOSH-2023-1289",
        "case_title": "Cal-OSHA Citation: Gas Service Worker Trench Collapse",
        "regulator": "Cal-OSHA",
        "case_type": "enforcement",
        "status": "resolved",
        "filing_date": "2023-12-05",
        "resolution_date": "2024-07-15",
        "penalty_amount": 285000,
        "summary": "Cal-OSHA citations for serious and willful violations following a trench collapse during gas service line installation. Worker hospitalized with crush injuries. $285K penalty.",
        "key_findings": "Trench exceeding 5 feet without shoring; competent person not present on site; soil classification not performed; prior OSHA warnings for similar violations at PG&E worksites within 18 months.",
        "precedent_tags": "worker_safety,cal_osha,enforcement,penalty,trench,gas_operations,willful_violation"
    },
    {
        "case_number": "DOSH-2024-0723",
        "case_title": "Cal-OSHA Citation: Vegetation Management Crew Heat Illness",
        "regulator": "Cal-OSHA",
        "case_type": "enforcement",
        "status": "resolved",
        "filing_date": "2024-07-23",
        "resolution_date": "2025-02-10",
        "penalty_amount": 180000,
        "summary": "Citations for heat illness prevention failures involving a contracted vegetation management crew working in Tier 3 HFTD. Two workers hospitalized with heat stroke. $180K penalty against PG&E as controlling employer.",
        "key_findings": "Shade structures not provided; water inadequately supplied; no acclimatization plan for new workers; heat illness prevention plan not communicated in workers' primary language (Spanish); PG&E liable as controlling employer of contractor crew.",
        "precedent_tags": "worker_safety,cal_osha,enforcement,penalty,heat_illness,vegetation,contractor,controlling_employer"
    },
    # ==================== CEC — ENERGY COMMISSION ====================
    {
        "case_number": "CEC-2024-SIP-001",
        "case_title": "CEC Strategic Reliability Reserve: PG&E Compliance Review",
        "regulator": "CEC",
        "case_type": "audit",
        "status": "resolved",
        "filing_date": "2024-01-10",
        "resolution_date": "2024-09-15",
        "penalty_amount": 0,
        "summary": "CEC review of PG&E's compliance with Strategic Reliability Reserve requirements under SB 846. No penalties but findings on demand response program integration and battery storage deployment timelines.",
        "key_findings": "Battery storage interconnection delays (avg 14 months vs 9 month target); demand response participation rates below forecast; load forecasting methodology needs updating for EV adoption curves.",
        "precedent_tags": "cec,reliability,battery_storage,demand_response,ev,compliance_review"
    },
]

# --- Penalty Timeline Data (for trend analysis charts) ---
PENALTY_TIMELINE = [
    {"year": 2012, "regulator": "CPUC", "total_penalties": 38000000, "case_count": 1, "categories": ["pipeline_safety"]},
    {"year": 2013, "regulator": "CPUC", "total_penalties": 15000000, "case_count": 2, "categories": ["pipeline_safety", "vegetation"]},
    {"year": 2014, "regulator": "CPUC", "total_penalties": 25000000, "case_count": 1, "categories": ["pipeline_safety"]},
    {"year": 2015, "regulator": "CPUC", "total_penalties": 52000000, "case_count": 2, "categories": ["pipeline_safety", "gas_operations"]},
    {"year": 2016, "regulator": "CPUC", "total_penalties": 110000000, "case_count": 1, "categories": ["pipeline_safety"]},
    {"year": 2017, "regulator": "CPUC", "total_penalties": 1600000000, "case_count": 1, "categories": ["pipeline_safety"]},
    {"year": 2018, "regulator": "CPUC", "total_penalties": 85000000, "case_count": 3, "categories": ["wildfire", "vegetation", "safety_culture"]},
    {"year": 2019, "regulator": "CPUC", "total_penalties": 2140000000, "case_count": 2, "categories": ["wildfire", "wildfire"]},
    {"year": 2020, "regulator": "CPUC", "total_penalties": 120000000, "case_count": 2, "categories": ["wildfire", "pipeline_safety"]},
    {"year": 2021, "regulator": "CPUC", "total_penalties": 75000000, "case_count": 3, "categories": ["wildfire", "vegetation", "safety_culture"]},
    {"year": 2022, "regulator": "CPUC", "total_penalties": 160000000, "case_count": 2, "categories": ["wildfire", "pipeline_safety"]},
    {"year": 2023, "regulator": "CPUC", "total_penalties": 165000000, "case_count": 3, "categories": ["wildfire", "wildfire", "gas_operations"]},
    {"year": 2024, "regulator": "CPUC", "total_penalties": 110000000, "case_count": 2, "categories": ["wildfire", "undergrounding"]},
    {"year": 2025, "regulator": "CPUC", "total_penalties": 45000000, "case_count": 1, "categories": ["wildfire"]},
    {"year": 2018, "regulator": "NERC/FERC", "total_penalties": 1200000, "case_count": 1, "categories": ["cybersecurity"]},
    {"year": 2019, "regulator": "NERC/FERC", "total_penalties": 2100000, "case_count": 2, "categories": ["cybersecurity", "reliability"]},
    {"year": 2020, "regulator": "NERC/FERC", "total_penalties": 1800000, "case_count": 1, "categories": ["cybersecurity"]},
    {"year": 2021, "regulator": "NERC/FERC", "total_penalties": 3800000, "case_count": 1, "categories": ["cybersecurity"]},
    {"year": 2022, "regulator": "NERC/FERC", "total_penalties": 2750000, "case_count": 1, "categories": ["cybersecurity"]},
    {"year": 2023, "regulator": "NERC/FERC", "total_penalties": 1500000, "case_count": 1, "categories": ["cybersecurity"]},
    {"year": 2024, "regulator": "NERC/FERC", "total_penalties": 850000, "case_count": 1, "categories": ["reliability"]},
    {"year": 2020, "regulator": "PHMSA", "total_penalties": 3200000, "case_count": 1, "categories": ["pipeline_safety"]},
    {"year": 2023, "regulator": "PHMSA", "total_penalties": 1800000, "case_count": 1, "categories": ["pipeline_safety"]},
    {"year": 2022, "regulator": "CARB", "total_penalties": 1200000, "case_count": 1, "categories": ["emissions"]},
    {"year": 2023, "regulator": "CARB", "total_penalties": 500000, "case_count": 1, "categories": ["emissions"]},
    {"year": 2024, "regulator": "CARB", "total_penalties": 750000, "case_count": 1, "categories": ["emissions"]},
    {"year": 2022, "regulator": "Cal-OSHA", "total_penalties": 425000, "case_count": 1, "categories": ["worker_safety"]},
    {"year": 2023, "regulator": "Cal-OSHA", "total_penalties": 285000, "case_count": 1, "categories": ["worker_safety"]},
    {"year": 2024, "regulator": "Cal-OSHA", "total_penalties": 180000, "case_count": 1, "categories": ["worker_safety"]},
]


def load_sample_cases():
    """Load the ACTIVE domain's case corpus into its vector-store collection."""
    texts = []
    metadatas = []
    for case in get_domain()["cases"]:
        text = f"""Case: {case['case_number']} — {case['case_title']}
Regulator: {case['regulator']} | Type: {case['case_type']} | Status: {case['status']}
Filed: {case['filing_date']} | Resolved: {case.get('resolution_date', 'Ongoing')}
Penalty: ${case['penalty_amount']:,.0f}

Summary: {case['summary']}

Key Findings: {case['key_findings']}

Tags: {case['precedent_tags']}"""
        texts.append(text)
        metadatas.append({
            "case_number": case["case_number"],
            "regulator": case["regulator"],
            "case_type": case["case_type"],
            "penalty_amount": case["penalty_amount"],
        })

    add_documents(_cases_collection(), texts, metadatas)
    return len(texts)


def search_cases(query: str, k: int = 5) -> list[dict]:
    """Search the active domain's historical cases."""
    results = search_documents(_cases_collection(), query, k=k)
    return [{"content": doc.page_content, "score": round(score, 3), "metadata": doc.metadata}
            for doc, score in results]


def get_case_stats() -> dict:
    """Get summary statistics for the active domain's case corpus."""
    cases = get_domain()["cases"]
    total_penalties = sum(c["penalty_amount"] for c in cases)
    by_regulator = {}
    by_type = {}
    by_status = {}

    for c in cases:
        by_regulator[c["regulator"]] = by_regulator.get(c["regulator"], 0) + 1
        by_type[c["case_type"]] = by_type.get(c["case_type"], 0) + 1
        by_status[c["status"]] = by_status.get(c["status"], 0) + 1

    penalties = [c for c in cases if c["penalty_amount"] > 0]

    return {
        "total_cases": len(cases),
        "total_penalties": total_penalties,
        "average_penalty": total_penalties / len(penalties) if penalties else 0,
        "max_penalty": max((c["penalty_amount"] for c in cases), default=0),
        "by_regulator": by_regulator,
        "by_type": by_type,
        "by_status": by_status,
        "penalty_cases": len(penalties),
    }


def run_case_analytics(query: str, analysis_type: str = "precedent") -> dict:
    """Run case analytics with Claude analysis over RAG results.

    analysis_type: 'precedent' | 'trend' | 'risk' | 'summary'
    """
    llm = get_openai_primary()
    domain = get_domain()

    # Retrieval gates what reaches the model. At production corpus size the full database
    # must NOT be injected — retrieval is the context boundary, not a decoration.
    relevant_cases = search_cases(query, k=8)
    stats = get_case_stats()
    case_data = json.dumps(relevant_cases, indent=2, default=str)

    analysis_instructions = {
        "precedent": "Find precedent cases most relevant to the query. Analyze how similar situations were resolved and what penalties were imposed.",
        "trend": "Identify enforcement trends over time. Are penalties increasing? Are certain violation types becoming more common?",
        "risk": "Assess compliance risk based on enforcement history. What areas face the highest enforcement risk and potential penalties?",
        "summary": "Provide a comprehensive summary of all relevant cases, key patterns, and strategic implications for PG&E.",
    }

    prompt = f"""Analyze {domain['company']}'s regulatory enforcement history based on this query.

QUERY: {query}
ANALYSIS TYPE: {analysis_type}
INSTRUCTIONS: {analysis_instructions.get(analysis_type, analysis_instructions['summary'])}

RETRIEVED CASES (these are the ONLY cases you may cite — do not introduce any others):
{case_data}

AGGREGATE STATISTICS (computed deterministically over the full corpus):
{json.dumps(stats, indent=2)}

Provide a comprehensive analysis as JSON:
{{
    "analysis_type": "{analysis_type}",
    "query": "{query}",
    "executive_summary": "2-3 paragraph analysis",
    "relevant_cases": [
        {{
            "case_number": "ID",
            "relevance": "why this case is relevant",
            "key_takeaway": "main lesson for PG&E"
        }}
    ],
    "patterns_identified": ["list of patterns"],
    "risk_assessment": {{
        "overall_risk": "low|medium|high|critical",
        "highest_risk_areas": ["areas"],
        "estimated_penalty_exposure": "dollar range"
    }},
    "recommendations": ["actionable recommendations for PG&E"],
    "data_visualizations": {{
        "penalties_by_year": {{"year": amount}},
        "cases_by_type": {{"type": count}},
        "cases_by_regulator": {{"regulator": count}}
    }}
}}"""

    response = llm.invoke([
        SystemMessage(content=get_prompt("case_analytics")),
        HumanMessage(content=prompt)
    ])

    try:
        content = response.content
        analysis = json.loads(content[content.find("{"):content.rfind("}") + 1])
    except (json.JSONDecodeError, ValueError):
        analysis = {
            "analysis_type": analysis_type,
            "executive_summary": response.content[:2000],
            "error": "Structured parsing failed — raw analysis provided"
        }

    analysis["stats"] = stats
    analysis["domain"] = domain["label"]
    analysis["retrieved_case_count"] = len(relevant_cases)
    return analysis
```

## `core/__init__.py`

```python
# Regulatory Compliance AI - Core Module
```

## `core/prompts.py`

```python
"""
Regulatory Compliance AI — System Prompts for All Agents
========================================================

Centralized prompt management for consistency and auditability.

Prompts are COMPOSED AT CALL TIME from the active industry domain pack
(see core/domains.py), not frozen at import. That is what allows the same seven
agents to serve Energy & Utilities, Retail, Resources or Services without any
change to the agent graphs.

    get_prompt("regulatory_monitor")  ->  <active domain context> + <role instructions>

Call get_prompt(role) inside a node. Do NOT bind these to module-level constants —
that would freeze the domain at import time and break industry switching.
"""

from core.domains import build_system_context


# --- Role instructions (domain-independent) ---------------------------------------------

_ROLE_INSTRUCTIONS = {
    "regulatory_monitor": """
You are the Regulatory Change Monitor Agent. Your job is to:
1. Analyze regulatory text and identify material changes
2. Classify changes by type: rule_change, guidance, notice, enforcement, proposed_rule
3. Assess severity: critical, high, medium, low
4. Extract specific obligations (who must do what, by when, measured how, penalty if not)
5. Map obligations to the organisation's departments

When analyzing regulatory text, be precise and cite specific sections. Every obligation you
extract must quote the source text verbatim. Output structured JSON.
""",

    "obligation_impact": """
You are the Obligation Impact Analysis Agent. Your job is to:
1. Decompose complex regulations into atomic, independently testable obligations
2. Identify which departments, systems, and processes are affected
3. Detect conflicts and overlaps between new and existing obligations
4. Score impact on four dimensions: cost, operational disruption, timeline, penalty risk
5. Recommend a compliance approach with effort estimates

For each obligation produce: affected departments and systems, gap analysis (current vs.
required state), estimated cost range, recommended timeline, and the risk if non-compliant.
Ground every cost and penalty figure in the source text or in stated enforcement history —
never invent a number.
""",

    "audit_supervisor": """
You are the Audit Preparation Supervisor Agent. You coordinate three specialist agents:
1. Evidence Collector — gathers and validates documentary evidence
2. Gap Analyzer — compares evidence against regulatory requirements
3. Response Drafter — prepares audit responses with proper citations

Your job is to:
- Plan the audit approach and set the priority order the specialists will work to
- Ensure completeness: verify every obligation has mapped evidence
- Flag gaps that need remediation before the audit
- Maintain a traceable chain: regulation -> obligation -> evidence -> gap -> response
- On review, explicitly check whether the specialists covered the plan YOU set. Name anything
  in your plan that they failed to address.
""",

    "audit_evidence": """
You are the Evidence Collector Agent. Your job is to:
1. Identify what evidence is needed for each obligation
2. Search the document repository for matching evidence
3. Validate that evidence is current, complete, and properly formatted
4. Flag missing, partial or outdated evidence items — an out-of-date document is NOT coverage
5. Suggest where missing evidence could be found

Be conservative. Rating weak evidence as 'sufficient' is the single most damaging error you can
make: it produces false confidence going into an audit. When in doubt, rate it 'partial'.
""",

    "audit_gap": """
You are the Gap Analyzer Agent. Your job is to:
1. Compare collected evidence against each regulatory requirement
2. Identify gaps: missing evidence, outdated evidence, partial compliance, process gaps
3. Assess gap severity and the specific audit risk it creates
4. Prioritize gaps by audit risk and remediation effort
5. Recommend remediation with a named owner, effort estimate and deadline

State plainly what could go wrong if an auditor finds each gap. Do not soften findings.
""",

    "audit_response": """
You are the Response Drafter Agent. Your job is to:
1. Draft professional audit responses for each finding area
2. Cite specific evidence documents and regulatory references
3. Maintain formal tone appropriate for regulatory submissions
4. Include corrective action plans for identified gaps
5. Generate an executive summary for audit committee review

Never assert compliance that the evidence does not support. Where a gap exists, say so and
describe the corrective action — a drafted response that overstates compliance is worse than
no draft at all, because it will be relied upon.
""",

    "case_analytics": """
You are the Case Analytics Agent. Your job is to:
1. Analyze historical enforcement cases involving the organisation and its peers
2. Identify patterns in enforcement actions, penalties, and resolutions
3. Find precedent cases relevant to current compliance concerns
4. Anticipate enforcement trends based on regulatory signals
5. Generate statistical summaries of case outcomes

Cite specific cases, penalty amounts and dates from the provided corpus. Do not introduce cases
that are not in the corpus, and do not estimate penalty figures that the corpus does not contain.
""",
}


def get_prompt(role: str, domain: str | None = None) -> str:
    """Compose an agent's system prompt from the active domain pack + its role instructions.

    Args:
        role: one of regulatory_monitor | obligation_impact | audit_supervisor |
              audit_evidence | audit_gap | audit_response | case_analytics
        domain: optional explicit domain key; defaults to the active domain.
    """
    if role not in _ROLE_INSTRUCTIONS:
        raise ValueError(f"Unknown agent role '{role}'. Known: {list(_ROLE_INSTRUCTIONS)}")
    return build_system_context(domain) + _ROLE_INSTRUCTIONS[role]


AGENT_ROLES = list(_ROLE_INSTRUCTIONS)
```

## `core/domains.py`

```python
"""
Regulatory Compliance AI — Industry Domain Packs
=================================================

The four agent workflows (Regulatory Monitor, Obligation Impact, Audit Prep, Case Analytics)
contain NO industry-specific logic. Everything that makes the platform "a utility compliance
tool" or "a retail compliance tool" lives here, in a swappable domain pack.

A pack supplies six things:
  1. company / enterprise_profile — who the agents work for (used in impact scoring)
  2. regulators                   — the monitored perimeter
  3. departments                  — obligation routing targets
  4. existing_obligations         — the register used for conflict/overlap detection
  5. categories                   — the obligation taxonomy
  6. corpora                      — regulations, audit types, evidence repository, case history

Swapping the pack re-targets the entire platform to a new industry without touching a graph.
That is the reuse thesis: one agentic architecture, many regulated industries.

Aligned to the SURE / EURS verticals: Services, Utilities, Resources, Energy — plus Retail.

DATA PROVENANCE: all corpora in this module are ILLUSTRATIVE and synthetic, authored to be
realistic in structure and vocabulary. They are demonstration fixtures, not verified records
of real regulations or real enforcement actions. In production these are replaced by live
ingestion connectors (see BLUEPRINT.md §11 G1).
"""

import os

DEFAULT_DOMAIN = "energy_utilities"


# ==========================================================================================
# PACK 1 — ENERGY & UTILITIES  (reference implementation: Pacific Gas and Electric Company)
# ==========================================================================================
# The corpora for this pack live in the agent modules (they predate the pack abstraction and
# are the deepest of the four). They are attached lazily in _load_corpora() to avoid a circular
# import at module load.

ENERGY_UTILITIES = {
    "key": "energy_utilities",
    "label": "Energy & Utilities",
    "vertical": "Utilities / Energy (SURE)",
    "company": "PG&E",
    "company_full": "Pacific Gas and Electric Company",
    "tagline": "Combined electric and gas investor-owned utility, northern and central California",
    "regulators": [
        {"code": "CPUC", "name": "California Public Utilities Commission", "scope": "State economic + safety regulator; SED conducts audits and enforcement"},
        {"code": "OEIS", "name": "Office of Energy Infrastructure Safety", "scope": "State wildfire-safety regulator; reviews and approves Wildfire Mitigation Plans; issues Safety Certification"},
        {"code": "FERC", "name": "Federal Energy Regulatory Commission", "scope": "Interstate transmission, planning, wholesale rates"},
        {"code": "NERC", "name": "North American Electric Reliability Corporation", "scope": "Grid reliability and OT cybersecurity (NERC CIP); WECC is the regional entity"},
        {"code": "CARB", "name": "California Air Resources Board", "scope": "Emissions, cap-and-trade"},
        {"code": "EPA", "name": "Environmental Protection Agency", "scope": "Federal environmental compliance"},
        {"code": "PHMSA", "name": "Pipeline & Hazardous Materials Safety Administration", "scope": "Federal pipeline safety; CPUC is the state pipeline safety agent"},
        {"code": "Cal-OSHA", "name": "California Division of Occupational Safety and Health", "scope": "Worker safety"},
        {"code": "CEC", "name": "California Energy Commission", "scope": "Energy policy, load forecasting, reliability reserve"},
    ],
    "departments": [
        "Electric Operations (grid, transmission, distribution)",
        "Gas Operations (pipeline, distribution, storage)",
        "Wildfire Safety (vegetation mgmt, fire prevention, PSPS)",
        "IT/Cybersecurity (NERC CIP, data systems)",
        "Environmental & Sustainability (emissions, compliance)",
        "Regulatory Affairs (filings, rate cases)",
        "Legal & Compliance (enforcement, litigation)",
        "Customer Operations (billing, service, data privacy)",
        "Generation (power plants, procurement)",
        "Corporate (finance, governance, reporting)",
    ],
    "existing_obligations": [
        "OEIS Wildfire Mitigation Plan (base WMP + annual updates; OEIS approves, CPUC ratifies)",
        "OEIS Safety Certification (annual; affects AB 1054 cost-recovery presumption)",
        "CPUC General Order 95 (overhead line construction)",
        "CPUC General Order 165 (inspection cycles)",
        "CPUC Rule 20 (underground conversion)",
        "FERC Form 714 (transmission planning)",
        "NERC CIP-002 through CIP-015 (cybersecurity)",
        "CARB MRR (Mandatory Reporting Regulation) and Cap-and-Trade",
        "Cal-OSHA Title 8 (worker safety)",
        "PHMSA 49 CFR 192 (gas pipeline safety)",
        "CCPA/CPRA (customer data privacy)",
    ],
    "enterprise_profile": """- Annual revenue: ~$24B
- Workforce: ~26,000-28,000 employees
- Combined electric + gas utility serving ~16 million people in northern/central California
- Active wildfire liabilities; emerged from Chapter 11 in 2020
- Under enhanced regulatory oversight since 2019
- Significant ongoing capital investment programme (~$7-8B annually), including multi-year undergrounding
- AB 1054 framework: Safety Certification and demonstrated WMP compliance affect the cost-recovery
  presumption and Wildfire Fund access — evidence quality is a direct financial lever""",
    "categories": ["wildfire", "grid_reliability", "cybersecurity", "environmental", "reporting", "safety", "ai_governance", "financial"],
    "financial_hook": (
        "Under AB 1054, Safety Certification and demonstrated WMP compliance affect the cost-recovery "
        "presumption and Wildfire Fund access. The CPUC can disallow claimed costs where compliance "
        "cannot be evidenced. Evidence quality is therefore an input to cost recovery, not overhead."
    ),
    # corpora attached lazily — see _load_corpora()
    "regulations": None,
    "audit_types": None,
    "evidence": None,
    "cases": None,
    "penalty_timeline": None,
}


# ==========================================================================================
# PACK 2 — RETAIL & CONSUMER
# ==========================================================================================

RETAIL = {
    "key": "retail",
    "label": "Retail & Consumer",
    "vertical": "Retail (RCL)",
    "company": "the Retailer",
    "company_full": "a national omni-channel retailer (grocery, general merchandise, e-commerce)",
    "tagline": "Omni-channel retailer: stores, e-commerce, private-label food, consumer products",
    "regulators": [
        {"code": "FTC", "name": "Federal Trade Commission", "scope": "Unfair/deceptive practices (FTC Act §5), advertising, Green Guides, data security"},
        {"code": "FDA", "name": "Food and Drug Administration", "scope": "Food safety (FSMA), labelling, cosmetics, OTC"},
        {"code": "CPSC", "name": "Consumer Product Safety Commission", "scope": "Product safety, recalls, §15(b) reporting"},
        {"code": "CA-AG", "name": "California Attorney General / CPPA", "scope": "CCPA/CPRA consumer privacy enforcement"},
        {"code": "PCI-SSC", "name": "PCI Security Standards Council", "scope": "PCI DSS v4.0 cardholder data security (contractual, acquirer-enforced)"},
        {"code": "DOL", "name": "Department of Labor / state labor agencies", "scope": "Wage & hour, predictive scheduling, worker classification"},
        {"code": "SEC", "name": "Securities and Exchange Commission", "scope": "Disclosure, climate and cyber incident reporting"},
        {"code": "EPA", "name": "Environmental Protection Agency / state EPR", "scope": "Packaging EPR, hazardous waste, refrigerants"},
    ],
    "departments": [
        "Store Operations",
        "E-commerce & Digital",
        "Supply Chain & Logistics",
        "Merchandising & Sourcing",
        "Food Safety & Quality Assurance",
        "IT/Cybersecurity",
        "Legal & Compliance",
        "HR / People (wage & hour, scheduling)",
        "Finance & Treasury (payments, PCI scope)",
        "Marketing & Advertising",
        "Sustainability & ESG",
        "Customer Care",
    ],
    "existing_obligations": [
        "PCI DSS v4.0 (cardholder data environment)",
        "CCPA/CPRA (consumer privacy, opt-out of sale/share, sensitive PI)",
        "FTC Act §5 (unfair or deceptive acts or practices)",
        "FTC Green Guides (environmental marketing claims)",
        "CPSC §15(b) (24-hour substantial product hazard reporting)",
        "FDA FSMA Preventive Controls + Food Traceability Rule (§204)",
        "California Prop 65 (warnings)",
        "ADA Title III / WCAG 2.1 AA (digital accessibility)",
        "State Extended Producer Responsibility (EPR) packaging laws (CA SB 54, CO, ME, OR)",
        "FLSA + state wage/hour and predictive scheduling ordinances",
        "SOX (financial controls)",
    ],
    "enterprise_profile": """- Annual revenue: ~$40B
- Workforce: ~250,000 associates (high proportion hourly, high turnover)
- ~1,800 stores across 30+ states, plus a national e-commerce and fulfilment operation
- Private-label food and consumer-product manufacturing (own-brand liability)
- Large card-present + card-not-present payments footprint (PCI scope is broad)
- Thin operating margins: penalty and recall exposure is material relative to net income
- Brand trust is the core asset — a privacy or food-safety failure is a revenue event, not just a fine""",
    "categories": ["product_safety", "food_safety", "data_privacy", "payments_security", "advertising", "labor", "environmental", "reporting", "ai_governance"],
    "financial_hook": (
        "In retail the dominant exposure is rarely the fine — it is the recall cost, the class action, "
        "and the brand damage that follows. A CPSC §15(b) reporting failure or an FSMA traceability gap "
        "converts a contained incident into an uncontained one. Evidence quality determines which."
    ),
    "regulations": [
        {
            "source": "FDA",
            "title": "FSMA Section 204: Food Traceability Rule — Compliance Requirements",
            "url": "https://www.fda.gov/food/food-safety-modernization-act-fsma/fsma-final-rule-requirements-additional-traceability-records-certain-foods",
            "published_date": "2026-01-20",
            "text": """The Food and Drug Administration establishes additional traceability recordkeeping
            requirements for persons who manufacture, process, pack, or hold foods on the Food Traceability List (FTL).

            1. KEY DATA ELEMENTS (KDEs): For each Critical Tracking Event (CTE) — harvesting, cooling,
               initial packing, shipping, receiving, transformation — the Retailer must maintain Key Data
               Elements including traceability lot code, product description, quantity, location
               identifiers, and date of the event.

            2. TRACEABILITY LOT CODE: A traceability lot code must be assigned and carried forward through
               every subsequent CTE. Lot codes may not be broken or re-assigned at store receiving.

            3. 24-HOUR RESPONSE: On request from FDA during an outbreak investigation, the Retailer must
               produce an electronic sortable spreadsheet of all traceability records within 24 hours.

            4. SCOPE: Applies to all FTL foods including leafy greens, fresh-cut fruits and vegetables,
               shell eggs, nut butters, and ready-to-eat deli salads. Private-label and own-brand products
               are in scope regardless of manufacturer.

            5. RECORDS RETENTION: Traceability records must be retained for 2 years.

            Compliance date: January 20, 2028. Failure to produce records within 24 hours during an
            outbreak may result in the food being deemed adulterated or misbranded, expanded recall scope,
            and FDA enforcement including warning letters, seizure, and injunction."""
        },
        {
            "source": "CA-AG",
            "title": "CCPA/CPRA Enforcement Advisory: Dark Patterns and Opt-Out Preference Signals",
            "url": "https://cppa.ca.gov/regulations/",
            "published_date": "2026-02-10",
            "text": """The California Privacy Protection Agency issues binding requirements on consent
            interfaces and opt-out mechanisms for businesses subject to the CCPA as amended by the CPRA.

            1. OPT-OUT PREFERENCE SIGNAL (OOPS): Businesses MUST honour the Global Privacy Control (GPC)
               browser signal as a valid request to opt out of sale/sharing. Honouring GPC is mandatory,
               not optional. The signal must be honoured at the browser level without requiring the
               consumer to also interact with a banner.

            2. SYMMETRY IN CHOICE: The path to opt out must require no more steps than the path to opt in.
               A single-click "Accept All" paired with a multi-step "Manage Preferences" flow constitutes
               a dark pattern and renders any consent obtained invalid.

            3. SENSITIVE PERSONAL INFORMATION: Precise geolocation, and inferences drawn from purchase
               history that reveal health conditions, require a "Limit the Use of My Sensitive Personal
               Information" mechanism.

            4. LOYALTY PROGRAMMES: Financial incentives tied to data collection require a good-faith
               estimate of the value of consumer data and a description of the calculation method.

            5. SERVICE PROVIDER CONTRACTS: All ad-tech, analytics and personalisation vendors must be
               under a compliant service-provider or contractor agreement. Absent that, disclosure to the
               vendor is a "sale" requiring opt-out.

            Effective immediately. Administrative fines up to $2,500 per violation, or $7,500 per
            intentional violation or violation involving the personal information of minors. Each affected
            consumer is a separate violation."""
        },
        {
            "source": "CPSC",
            "title": "Final Rule: eFiling of Certificates of Compliance and Section 15(b) Reporting Clarification",
            "url": "https://www.cpsc.gov/Regulations-Laws--Standards",
            "published_date": "2026-03-05",
            "text": """The Consumer Product Safety Commission finalises requirements for electronic filing
            of certificates of compliance and clarifies substantial product hazard reporting obligations.

            1. eFILING: Importers and domestic manufacturers must electronically file Certificate of
               Compliance data with CBP at the time of entry for all regulated consumer products,
               including private-label goods where the Retailer is the importer of record.

            2. SECTION 15(b) REPORTING: A firm must report immediately — interpreted as within 24 hours of
               obtaining information reasonably supporting the conclusion — that a product contains a
               defect which could create a substantial product hazard, creates an unreasonable risk of
               serious injury or death, or fails to comply with an applicable rule.

            3. INFORMATION AGGREGATION: The obligation to report is triggered by information the firm
               collectively holds. A firm may not avoid reporting because complaint data sat in customer
               care and never reached the product safety function. Firms must have a documented internal
               escalation process.

            4. RECALL EFFECTIVENESS: Recall plans must include a target effectiveness rate and monthly
               progress reporting until CPSC releases the firm from reporting.

            Civil penalties: up to $120,000 per violation, with a maximum of $17,150,000 for a related
            series of violations. Knowing violations may result in criminal penalties. Failure to report
            timely is itself a separate violation, independent of the underlying defect."""
        },
    ],
    "audit_types": {
        "PCI DSS v4.0 Assessment": [
            {"id": "PCI-001", "text": "Maintain a documented inventory of all system components in the CDE", "category": "payments_security", "deadline": "Ongoing"},
            {"id": "PCI-002", "text": "Quarterly external ASV scans and annual penetration test", "category": "payments_security", "deadline": "2026-09-30"},
            {"id": "PCI-003", "text": "MFA for all access into the cardholder data environment", "category": "payments_security", "deadline": "2026-03-31"},
            {"id": "PCI-004", "text": "Targeted risk analysis documented for every customised control", "category": "payments_security", "deadline": "2026-03-31"},
            {"id": "PCI-005", "text": "Payment page script integrity monitoring (Req 6.4.3 / 11.6.1)", "category": "payments_security", "deadline": "2026-03-31"},
        ],
        "FDA Food Safety / FSMA Audit": [
            {"id": "FS-001", "text": "Traceability lot code carried through every Critical Tracking Event", "category": "food_safety", "deadline": "2028-01-20"},
            {"id": "FS-002", "text": "Produce sortable electronic traceability records within 24 hours of FDA request", "category": "food_safety", "deadline": "2028-01-20"},
            {"id": "FS-003", "text": "Preventive Controls plan with documented hazard analysis per facility", "category": "food_safety", "deadline": "Ongoing"},
            {"id": "FS-004", "text": "Supplier verification programme for all FTL foods including private label", "category": "food_safety", "deadline": "Ongoing"},
            {"id": "FS-005", "text": "Cold chain temperature monitoring records retained 2 years", "category": "food_safety", "deadline": "Ongoing"},
        ],
        "CCPA/CPRA Privacy Audit": [
            {"id": "PR-001", "text": "Honour Global Privacy Control signal as a valid opt-out", "category": "data_privacy", "deadline": "2026-02-10"},
            {"id": "PR-002", "text": "Symmetry in choice — opt-out path no longer than opt-in path", "category": "data_privacy", "deadline": "2026-02-10"},
            {"id": "PR-003", "text": "Limit Use of Sensitive Personal Information mechanism live", "category": "data_privacy", "deadline": "2026-02-10"},
            {"id": "PR-004", "text": "Compliant service-provider agreements with all ad-tech vendors", "category": "data_privacy", "deadline": "2026-06-30"},
            {"id": "PR-005", "text": "Loyalty programme financial-incentive value estimate published", "category": "data_privacy", "deadline": "2026-06-30"},
        ],
        "CPSC Product Safety Audit": [
            {"id": "PS-001", "text": "24-hour Section 15(b) escalation process documented and tested", "category": "product_safety", "deadline": "2026-03-05"},
            {"id": "PS-002", "text": "Complaint data aggregated across customer care, returns and social", "category": "product_safety", "deadline": "2026-06-30"},
            {"id": "PS-003", "text": "Certificates of Compliance eFiled at entry for all private-label imports", "category": "product_safety", "deadline": "2026-03-05"},
            {"id": "PS-004", "text": "Recall plan with target effectiveness rate and monthly reporting", "category": "product_safety", "deadline": "Ongoing"},
        ],
        "Wage & Hour / Labor Audit": [
            {"id": "WH-001", "text": "Predictive scheduling: 14-day advance notice in covered jurisdictions", "category": "labor", "deadline": "Ongoing"},
            {"id": "WH-002", "text": "Meal and rest break records with premium pay for missed breaks", "category": "labor", "deadline": "Ongoing"},
            {"id": "WH-003", "text": "Off-the-clock work controls (bag checks, closing procedures)", "category": "labor", "deadline": "Ongoing"},
            {"id": "WH-004", "text": "Exempt classification review for store management roles", "category": "labor", "deadline": "2026-12-31"},
        ],
    },
    "evidence": {
        "payments_security": [
            {"doc_id": "PCI-ROC-2025", "title": "PCI DSS v4.0 Report on Compliance 2025", "type": "assessment", "status": "current", "location": "GRC/PCI/ROC/", "last_updated": "2025-11-30", "owner": "IT/Cybersecurity"},
            {"doc_id": "CDE-INVENTORY", "title": "Cardholder Data Environment Component Inventory", "type": "inventory", "status": "needs_update", "location": "GRC/PCI/Scope/", "last_updated": "2025-02-14", "owner": "IT/Cybersecurity"},
            {"doc_id": "ASV-SCAN-Q1", "title": "Q1 2026 ASV External Scan Results", "type": "report", "status": "current", "location": "GRC/PCI/Scans/", "last_updated": "2026-03-28", "owner": "IT/Cybersecurity"},
            {"doc_id": "SCRIPT-INTEGRITY", "title": "Payment Page Script Integrity Monitoring — Implementation Status", "type": "report", "status": "partial", "location": "GRC/PCI/Req6/", "last_updated": "2026-02-01", "owner": "E-commerce & Digital"},
            {"doc_id": "TRA-CUSTOM-CONTROLS", "title": "Targeted Risk Analyses for Customised Controls", "type": "analysis", "status": "missing", "location": "GRC/PCI/TRA/", "last_updated": "—", "owner": "IT/Cybersecurity"},
        ],
        "food_safety": [
            {"doc_id": "HACCP-PLANS", "title": "Preventive Controls / HACCP Plans — All Facilities", "type": "plan", "status": "current", "location": "QA/FoodSafety/PCQI/", "last_updated": "2026-01-15", "owner": "Food Safety & QA"},
            {"doc_id": "FTL-TRACE-PILOT", "title": "FSMA 204 Traceability Lot Code Pilot — Leafy Greens", "type": "report", "status": "partial", "location": "QA/FoodSafety/FSMA204/", "last_updated": "2026-03-01", "owner": "Supply Chain & Logistics"},
            {"doc_id": "SUPPLIER-VERIF", "title": "Supplier Verification Programme Records", "type": "registry", "status": "current", "location": "QA/Suppliers/", "last_updated": "2026-02-20", "owner": "Merchandising & Sourcing"},
            {"doc_id": "COLD-CHAIN-LOGS", "title": "Cold Chain Temperature Monitoring Logs", "type": "log", "status": "current", "location": "SupplyChain/ColdChain/", "last_updated": "2026-04-01", "owner": "Supply Chain & Logistics"},
            {"doc_id": "RECALL-DRILL-2024", "title": "Mock Recall / Traceability Drill Results", "type": "audit", "status": "needs_update", "location": "QA/FoodSafety/Drills/", "last_updated": "2024-10-12", "owner": "Food Safety & QA"},
        ],
        "data_privacy": [
            {"doc_id": "PRIVACY-NOTICE-V4", "title": "Consumer Privacy Notice v4.0", "type": "policy", "status": "current", "location": "Legal/Privacy/", "last_updated": "2026-01-05", "owner": "Legal & Compliance"},
            {"doc_id": "GPC-IMPL", "title": "Global Privacy Control Signal — Implementation Evidence", "type": "report", "status": "partial", "location": "Legal/Privacy/GPC/", "last_updated": "2026-02-25", "owner": "E-commerce & Digital"},
            {"doc_id": "VENDOR-DPA-REGISTRY", "title": "Ad-Tech Vendor Service-Provider Agreement Registry", "type": "registry", "status": "needs_update", "location": "Legal/Privacy/Vendors/", "last_updated": "2025-04-30", "owner": "Legal & Compliance"},
            {"doc_id": "DSAR-LOG", "title": "Consumer Rights Request (DSAR) Fulfilment Log", "type": "log", "status": "current", "location": "Legal/Privacy/DSAR/", "last_updated": "2026-04-02", "owner": "Customer Care"},
            {"doc_id": "LOYALTY-VALUE-CALC", "title": "Loyalty Programme Data Value Estimate", "type": "analysis", "status": "missing", "location": "Legal/Privacy/Loyalty/", "last_updated": "—", "owner": "Marketing & Advertising"},
        ],
        "product_safety": [
            {"doc_id": "15B-ESCALATION-SOP", "title": "Section 15(b) Reporting Escalation Procedure", "type": "procedure", "status": "needs_update", "location": "Legal/ProductSafety/", "last_updated": "2024-06-18", "owner": "Legal & Compliance"},
            {"doc_id": "COMPLAINT-AGGREGATION", "title": "Cross-Channel Complaint Aggregation Dashboard", "type": "report", "status": "partial", "location": "CustomerCare/Complaints/", "last_updated": "2026-01-30", "owner": "Customer Care"},
            {"doc_id": "COC-EFILING", "title": "Certificate of Compliance eFiling Readiness Assessment", "type": "assessment", "status": "partial", "location": "SupplyChain/Imports/", "last_updated": "2026-02-15", "owner": "Supply Chain & Logistics"},
            {"doc_id": "RECALL-PLAYBOOK", "title": "Product Recall Playbook v2", "type": "procedure", "status": "current", "location": "Legal/ProductSafety/Recall/", "last_updated": "2025-09-10", "owner": "Legal & Compliance"},
        ],
        "labor": [
            {"doc_id": "SCHEDULING-COMPLIANCE", "title": "Predictive Scheduling Compliance Report by Jurisdiction", "type": "report", "status": "current", "location": "HR/Scheduling/", "last_updated": "2026-03-15", "owner": "HR / People"},
            {"doc_id": "BREAK-PREMIUM-AUDIT", "title": "Meal & Rest Break Premium Pay Audit", "type": "audit", "status": "needs_update", "location": "HR/WageHour/", "last_updated": "2024-12-01", "owner": "HR / People"},
            {"doc_id": "EXEMPT-CLASS-REVIEW", "title": "Store Management Exempt Classification Review", "type": "review", "status": "partial", "location": "HR/Classification/", "last_updated": "2025-08-22", "owner": "HR / People"},
        ],
    },
    "cases": [
        {"case_number": "FTC-PRIV-2023-014", "case_title": "FTC Enforcement: Retail Loyalty Data Sharing Without Consent", "regulator": "FTC", "case_type": "enforcement", "status": "resolved", "filing_date": "2023-04-11", "resolution_date": "2023-11-02", "penalty_amount": 8500000, "summary": "Illustrative. FTC action over sharing loyalty-programme purchase data with ad-tech partners without adequate disclosure or consent. Consent order requires deletion of unlawfully collected data and algorithmic disgorgement of models trained on it.", "key_findings": "Privacy notice did not describe ad-tech sharing; no service-provider agreements in place; consumers could not effectively opt out; models trained on improperly obtained data ordered destroyed.", "precedent_tags": "data_privacy,ftc,enforcement,adtech,consent,algorithmic_disgorgement"},
        {"case_number": "CPPA-2024-003", "case_title": "CPPA Enforcement: Dark Patterns in Cookie Consent Interface", "regulator": "CA-AG", "case_type": "enforcement", "status": "resolved", "filing_date": "2024-02-20", "resolution_date": "2024-09-14", "penalty_amount": 1200000, "summary": "Illustrative. Enforcement over an asymmetric consent banner — one-click accept vs. a four-step opt-out — and failure to honour the Global Privacy Control signal.", "key_findings": "Symmetry-in-choice violation; GPC signal ignored; each affected consumer counted as a separate violation, driving the penalty calculation.", "precedent_tags": "data_privacy,ccpa,cpra,dark_patterns,gpc,enforcement"},
        {"case_number": "CPSC-2024-RECALL-081", "case_title": "CPSC Civil Penalty: Delayed Section 15(b) Report on Private-Label Appliance", "regulator": "CPSC", "case_type": "enforcement", "status": "resolved", "filing_date": "2024-05-08", "resolution_date": "2025-01-17", "penalty_amount": 15300000, "summary": "Illustrative. Civil penalty for failure to timely report a defect in a private-label small appliance. Complaint data indicating a fire hazard sat in customer care for 11 months before reaching the product safety function.", "key_findings": "Information-aggregation failure — the firm collectively held sufficient information to report; no documented internal escalation process; delayed report expanded the recall population and injury count.", "precedent_tags": "product_safety,cpsc,enforcement,15b,recall,escalation_failure,private_label"},
        {"case_number": "FDA-WL-2025-227", "case_title": "FDA Warning Letter: Traceability Records Not Produced During Outbreak", "regulator": "FDA", "case_type": "enforcement", "status": "resolved", "filing_date": "2025-07-30", "resolution_date": "2025-12-05", "penalty_amount": 0, "summary": "Illustrative. Warning letter following an inability to produce sortable traceability records within 24 hours during a leafy-greens outbreak investigation. No monetary penalty, but the recall scope was expanded from 3 SKUs to 47 because affected lots could not be isolated.", "key_findings": "Lot codes broken at store receiving; records held across four systems with no common key; recall cost driven by inability to narrow scope rather than by the underlying contamination.", "precedent_tags": "food_safety,fda,fsma,traceability,recall_scope,outbreak"},
        {"case_number": "DOL-WH-2023-1142", "case_title": "Wage & Hour Class Settlement: Off-the-Clock Bag Checks", "regulator": "DOL", "case_type": "enforcement", "status": "resolved", "filing_date": "2023-01-19", "resolution_date": "2024-06-28", "penalty_amount": 22000000, "summary": "Illustrative. Class settlement covering unpaid time for mandatory security bag checks conducted after clock-out across store estate.", "key_findings": "Time-clock and security-check records were never reconciled; no evidence the firm had measured the duration of the checks; settlement value driven by class size, not by per-employee amount.", "precedent_tags": "labor,wage_hour,dol,class_action,off_the_clock,recordkeeping"},
        {"case_number": "FTC-GREEN-2024-006", "case_title": "FTC Green Guides: Unsubstantiated 'Recyclable' Packaging Claims", "regulator": "FTC", "case_type": "enforcement", "status": "ongoing", "filing_date": "2024-10-02", "resolution_date": None, "penalty_amount": 3400000, "summary": "Illustrative. Action over 'recyclable' and 'compostable' claims on private-label packaging where recycling facilities were not available to a substantial majority of consumers.", "key_findings": "No substantiation file for the claims; marketing approved copy without sustainability sign-off; state EPR filings contradicted the on-pack claims.", "precedent_tags": "advertising,ftc,green_guides,greenwashing,epr,packaging,substantiation"},
    ],
    "penalty_timeline": [
        {"year": 2020, "regulator": "FTC", "total_penalties": 5000000, "case_count": 1, "categories": ["data_privacy"]},
        {"year": 2021, "regulator": "FTC", "total_penalties": 7200000, "case_count": 2, "categories": ["data_privacy", "advertising"]},
        {"year": 2022, "regulator": "FTC", "total_penalties": 4100000, "case_count": 1, "categories": ["advertising"]},
        {"year": 2023, "regulator": "FTC", "total_penalties": 8500000, "case_count": 1, "categories": ["data_privacy"]},
        {"year": 2024, "regulator": "FTC", "total_penalties": 3400000, "case_count": 1, "categories": ["advertising"]},
        {"year": 2022, "regulator": "CPSC", "total_penalties": 6000000, "case_count": 1, "categories": ["product_safety"]},
        {"year": 2023, "regulator": "CPSC", "total_penalties": 9800000, "case_count": 2, "categories": ["product_safety", "product_safety"]},
        {"year": 2024, "regulator": "CPSC", "total_penalties": 15300000, "case_count": 1, "categories": ["product_safety"]},
        {"year": 2023, "regulator": "CA-AG", "total_penalties": 900000, "case_count": 1, "categories": ["data_privacy"]},
        {"year": 2024, "regulator": "CA-AG", "total_penalties": 1200000, "case_count": 1, "categories": ["data_privacy"]},
        {"year": 2023, "regulator": "DOL", "total_penalties": 22000000, "case_count": 1, "categories": ["labor"]},
        {"year": 2024, "regulator": "DOL", "total_penalties": 6400000, "case_count": 2, "categories": ["labor", "labor"]},
    ],
}


# ==========================================================================================
# PACK 3 — RESOURCES (Oil & Gas, Chemicals, Mining)
# ==========================================================================================

RESOURCES = {
    "key": "resources",
    "label": "Resources (Oil & Gas, Chemicals, Mining)",
    "vertical": "Resources (SURE)",
    "company": "the Operator",
    "company_full": "an integrated resources operator (upstream production, midstream pipelines, downstream processing)",
    "tagline": "Upstream production, midstream transport, downstream processing; high process-safety exposure",
    "regulators": [
        {"code": "EPA", "name": "Environmental Protection Agency", "scope": "Clean Air Act, methane (OOOOb/c), RMP, GHGRP Subpart W, SPCC"},
        {"code": "OSHA", "name": "Occupational Safety and Health Administration", "scope": "Process Safety Management (29 CFR 1910.119)"},
        {"code": "PHMSA", "name": "Pipeline & Hazardous Materials Safety Administration", "scope": "49 CFR 192/195 pipeline integrity"},
        {"code": "BSEE", "name": "Bureau of Safety and Environmental Enforcement", "scope": "Offshore safety, SEMS"},
        {"code": "MSHA", "name": "Mine Safety and Health Administration", "scope": "Mine safety (Part 46/48 training)"},
        {"code": "SEC", "name": "Securities and Exchange Commission", "scope": "Climate-related disclosure, reserves reporting"},
        {"code": "STATE", "name": "State agencies (TCEQ, Texas RRC, CARB, CDPHE)", "scope": "Air permits, flaring, produced water, well integrity"},
    ],
    "departments": [
        "Upstream Operations (wells, production)",
        "Midstream & Pipelines",
        "Downstream / Refining & Processing",
        "HSE (Health, Safety, Environment)",
        "Process Safety Management",
        "Environmental & Emissions",
        "Asset Integrity & Reliability",
        "IT/OT Cybersecurity",
        "Regulatory & Government Affairs",
        "Legal & Compliance",
        "Supply Chain & Contractor Management",
        "Corporate (finance, ESG reporting)",
    ],
    "existing_obligations": [
        "OSHA PSM 29 CFR 1910.119 (Process Safety Management)",
        "EPA RMP 40 CFR 68 (Risk Management Program)",
        "EPA GHGRP Subpart W (petroleum and natural gas systems reporting)",
        "EPA NSPS OOOOa/b/c (methane and VOC standards)",
        "PHMSA 49 CFR 192 (gas) and 195 (hazardous liquid) integrity management",
        "Clean Air Act Title V operating permits",
        "SPCC 40 CFR 112 (spill prevention)",
        "MSHA Part 46/48 (training)",
        "TSCA / hazardous waste (RCRA)",
        "SEC climate-related disclosure",
    ],
    "enterprise_profile": """- Annual revenue: ~$35B
- Workforce: ~18,000 employees plus a large contractor population (contractor safety is a controlling-employer exposure)
- Upstream production, ~9,000 miles of midstream pipeline, three processing facilities
- High process-safety exposure: a single PSM failure can be a fatality event, not a fine
- Methane intensity is now a licence-to-operate issue with investors and regulators, not just a compliance line
- Title V permit deviations and RMP findings compound: they invite consent decrees with multi-year obligations""",
    "categories": ["process_safety", "emissions", "pipeline_integrity", "worker_safety", "environmental", "reporting", "cybersecurity", "governance"],
    "financial_hook": (
        "In resources the tail risk is not the penalty — it is the consent decree. An RMP or PSM finding "
        "that cannot be evidenced away converts into years of court-supervised obligations, capital "
        "commitments and third-party monitors. Evidence quality determines whether a finding closes or escalates."
    ),
    "regulations": [
        {
            "source": "EPA",
            "title": "NSPS OOOOb / EG OOOOc: Methane Standards for the Oil and Natural Gas Sector",
            "url": "https://www.epa.gov/controlling-air-pollution-oil-and-natural-gas-operations",
            "published_date": "2026-01-12",
            "text": """The Environmental Protection Agency finalises standards of performance for methane and
            volatile organic compound emissions from the crude oil and natural gas source category.

            1. SUPER-EMITTER RESPONSE PROGRAM: Operators must investigate and respond to credible
               third-party notifications of super-emitter events (>100 kg/hr methane) within 5 days, and
               report findings and corrective action to EPA within 15 days.

            2. FUGITIVE EMISSIONS MONITORING: Quarterly OGI (optical gas imaging) surveys at well sites
               with a fugitive emissions component; bimonthly AVO inspections. Advanced methane detection
               technology may substitute where it demonstrates equivalent or better detection.

            3. FLARING ELIMINATION: Routine flaring of associated gas from new wells is prohibited.
               Operators must certify one of the enumerated alternatives (capture, reinjection, on-site use)
               or demonstrate technical infeasibility with supporting engineering analysis.

            4. PNEUMATIC CONTROLLERS: Zero-emission requirement for process controllers at all new and
               existing sites, subject to a site-level exemption where no electrical power is available
               and the operator documents the analysis.

            5. STORAGE VESSELS: Control requirements triggered at 6 tpy VOC potential-to-emit,
               with recalculation required after any change to throughput.

            Compliance dates: new sources immediately upon publication; existing sources per state plans
            due within 24 months. Violations subject to Clean Air Act penalties of up to $121,275 per day
            per violation, plus the risk of a federal consent decree with injunctive relief."""
        },
        {
            "source": "OSHA",
            "title": "Process Safety Management: Proposed Update to 29 CFR 1910.119",
            "url": "https://www.osha.gov/process-safety-management",
            "published_date": "2026-02-28",
            "text": """OSHA proposes to update the Process Safety Management of Highly Hazardous Chemicals
            standard, the first substantive revision since 1992.

            1. MECHANICAL INTEGRITY: Expands covered equipment to include all safety-critical instrumentation
               and emergency isolation devices. Inspection and test records must demonstrate that each
               device was tested at the frequency specified by RAGAGEP, with deviations documented and
               risk-assessed.

            2. MANAGEMENT OF CHANGE (MOC): MOC required for organisational changes affecting process safety
               — including staffing reductions in operations and maintenance roles — not only for technical
               changes. This is a significant expansion.

            3. PROCESS HAZARD ANALYSIS: PHA revalidation cycle reduced from 5 years to 3 years for
               processes with a prior incident or a Tier 1 process safety event. Damage mechanism review
               and facility siting analysis become explicit PHA elements.

            4. CONTRACTOR SAFETY: The host employer must evaluate contractor process-safety performance
               using leading indicators, not solely TRIR. Contractor personnel must receive
               process-specific training, evidenced by records held by the host.

            5. INCIDENT INVESTIGATION: Root cause analysis required for all Tier 1 and Tier 2 process
               safety events. Findings must be tracked to closure with documented verification of
               effectiveness — closure without effectiveness verification is not compliance.

            Comment deadline: June 30, 2026. Willful violations: up to $165,514 per violation.
            Repeat and willful citations in PSM commonly precede EPA RMP referral and consent decree."""
        },
        {
            "source": "PHMSA",
            "title": "Gas Transmission Integrity Management: MAOP Reconfirmation and Records Validation",
            "url": "https://www.phmsa.dot.gov/regulations",
            "published_date": "2026-03-18",
            "text": """PHMSA issues requirements for maximum allowable operating pressure (MAOP)
            reconfirmation and traceable, verifiable, complete (TVC) records for gas transmission pipelines.

            1. TVC RECORDS: Operators must hold traceable, verifiable and complete records establishing
               material properties and MAOP for all pipeline segments in High Consequence Areas and
               Moderate Consequence Areas. A record is not "verifiable" if it cannot be corroborated by a
               second independent source.

            2. MAOP RECONFIRMATION: Where TVC records do not exist, the operator must reconfirm MAOP by
               one of six enumerated methods (pressure test, pressure reduction, engineering critical
               assessment, pipe replacement, PRD, or alternative technology) on a defined schedule.

            3. ASSESSMENT SCHEDULE: Reconfirmation of at least 50% of affected mileage by July 2028,
               and 100% by July 2035.

            4. MATERIAL VERIFICATION: Where material properties are unknown, operators must apply the
               material verification process at a defined sampling rate, with results integrated into
               the integrity management programme.

            5. RECORDS RETENTION: MAOP and material records must be retained for the operational life
               of the pipeline. Loss of records is not a defence.

            Penalties: up to $266,015 per violation per day; $2,660,135 for a related series of violations.
            Records inadequacy is itself the violation — the pipeline need not have failed."""
        },
    ],
    "audit_types": {
        "OSHA Process Safety Management (PSM) Audit": [
            {"id": "PSM-001", "text": "Mechanical integrity test records for all safety-critical devices at RAGAGEP frequency", "category": "process_safety", "deadline": "Ongoing"},
            {"id": "PSM-002", "text": "MOC completed for organisational changes affecting process safety", "category": "process_safety", "deadline": "Ongoing"},
            {"id": "PSM-003", "text": "PHA revalidation within 3 years for processes with prior Tier 1 events", "category": "process_safety", "deadline": "2026-12-31"},
            {"id": "PSM-004", "text": "Contractor process-safety evaluation using leading indicators", "category": "process_safety", "deadline": "2026-09-30"},
            {"id": "PSM-005", "text": "Incident findings tracked to closure with effectiveness verification", "category": "process_safety", "deadline": "Ongoing"},
        ],
        "EPA Methane / Air Compliance Audit": [
            {"id": "ME-001", "text": "Quarterly OGI fugitive emissions surveys at all covered well sites", "category": "emissions", "deadline": "Ongoing"},
            {"id": "ME-002", "text": "Super-emitter response within 5 days; EPA report within 15 days", "category": "emissions", "deadline": "Ongoing"},
            {"id": "ME-003", "text": "Routine flaring eliminated or technical infeasibility documented", "category": "emissions", "deadline": "2026-12-31"},
            {"id": "ME-004", "text": "Zero-emission pneumatic controllers or documented site exemption analysis", "category": "emissions", "deadline": "2027-06-30"},
            {"id": "ME-005", "text": "GHGRP Subpart W annual report reconciled to field measurement data", "category": "reporting", "deadline": "2026-03-31"},
        ],
        "PHMSA Pipeline Integrity Audit": [
            {"id": "PI-001", "text": "TVC records establishing MAOP for all HCA/MCA segments", "category": "pipeline_integrity", "deadline": "2028-07-01"},
            {"id": "PI-002", "text": "MAOP reconfirmation for segments lacking TVC records (50% by 2028)", "category": "pipeline_integrity", "deadline": "2028-07-01"},
            {"id": "PI-003", "text": "Material verification sampling where properties unknown", "category": "pipeline_integrity", "deadline": "2027-12-31"},
            {"id": "PI-004", "text": "Integrity management programme updated with verification results", "category": "pipeline_integrity", "deadline": "Ongoing"},
        ],
        "EPA Risk Management Program (RMP) Audit": [
            {"id": "RMP-001", "text": "Offsite consequence analysis current within 5 years", "category": "process_safety", "deadline": "2026-06-30"},
            {"id": "RMP-002", "text": "Compliance audit every 3 years with findings closed", "category": "process_safety", "deadline": "2026-12-31"},
            {"id": "RMP-003", "text": "Emergency response coordination with local responders documented", "category": "process_safety", "deadline": "Ongoing"},
            {"id": "RMP-004", "text": "Safer technology and alternatives analysis (STAA) for covered processes", "category": "process_safety", "deadline": "2027-03-31"},
        ],
    },
    "evidence": {
        "process_safety": [
            {"doc_id": "PSM-PHA-2024", "title": "Process Hazard Analysis — Refining Unit 3", "type": "analysis", "status": "needs_update", "location": "HSE/PSM/PHA/", "last_updated": "2021-05-14", "owner": "Process Safety Management"},
            {"doc_id": "MI-TEST-RECORDS", "title": "Mechanical Integrity Test Records — Safety Critical Devices", "type": "log", "status": "partial", "location": "HSE/PSM/MI/", "last_updated": "2026-02-10", "owner": "Asset Integrity & Reliability"},
            {"doc_id": "MOC-REGISTER", "title": "Management of Change Register", "type": "registry", "status": "current", "location": "HSE/PSM/MOC/", "last_updated": "2026-03-30", "owner": "Process Safety Management"},
            {"doc_id": "MOC-ORG-CHANGE", "title": "Organisational Change MOC — 2025 Maintenance Restructure", "type": "analysis", "status": "missing", "location": "HSE/PSM/MOC/Org/", "last_updated": "—", "owner": "Process Safety Management"},
            {"doc_id": "INCIDENT-CLOSURE", "title": "Tier 1/2 Incident Action Closure and Effectiveness Verification", "type": "report", "status": "partial", "location": "HSE/Incidents/", "last_updated": "2026-01-22", "owner": "HSE"},
            {"doc_id": "RMP-OCA", "title": "Offsite Consequence Analysis", "type": "analysis", "status": "current", "location": "HSE/RMP/", "last_updated": "2025-06-30", "owner": "HSE"},
        ],
        "emissions": [
            {"doc_id": "OGI-SURVEY-Q1", "title": "Q1 2026 OGI Fugitive Emissions Survey Results", "type": "report", "status": "current", "location": "Environmental/LDAR/", "last_updated": "2026-04-05", "owner": "Environmental & Emissions"},
            {"doc_id": "SUPER-EMITTER-LOG", "title": "Super-Emitter Notification Response Log", "type": "log", "status": "partial", "location": "Environmental/SuperEmitter/", "last_updated": "2026-03-12", "owner": "Environmental & Emissions"},
            {"doc_id": "FLARING-ANALYSIS", "title": "Routine Flaring Elimination — Technical Feasibility Analysis", "type": "analysis", "status": "partial", "location": "Environmental/Flaring/", "last_updated": "2026-02-18", "owner": "Upstream Operations"},
            {"doc_id": "SUBPART-W-2025", "title": "GHGRP Subpart W Annual Report 2025", "type": "filing", "status": "current", "location": "Environmental/GHGRP/", "last_updated": "2026-03-28", "owner": "Environmental & Emissions"},
            {"doc_id": "PNEUMATIC-INVENTORY", "title": "Pneumatic Controller Inventory and Retrofit Plan", "type": "inventory", "status": "needs_update", "location": "Environmental/Pneumatics/", "last_updated": "2025-03-01", "owner": "Upstream Operations"},
            {"doc_id": "TITLEV-DEVIATION", "title": "Title V Permit Deviation Report", "type": "report", "status": "current", "location": "Environmental/TitleV/", "last_updated": "2026-01-31", "owner": "Environmental & Emissions"},
        ],
        "pipeline_integrity": [
            {"doc_id": "MAOP-TVC-AUDIT", "title": "MAOP Traceable/Verifiable/Complete Records Audit", "type": "audit", "status": "needs_update", "location": "Midstream/Integrity/MAOP/", "last_updated": "2024-08-19", "owner": "Midstream & Pipelines"},
            {"doc_id": "IMP-PROGRAM", "title": "Integrity Management Program — Gas Transmission", "type": "plan", "status": "current", "location": "Midstream/Integrity/", "last_updated": "2025-12-05", "owner": "Midstream & Pipelines"},
            {"doc_id": "ILI-RESULTS-2025", "title": "In-Line Inspection Results and Dig Verification", "type": "report", "status": "current", "location": "Midstream/Integrity/ILI/", "last_updated": "2026-02-14", "owner": "Asset Integrity & Reliability"},
            {"doc_id": "MATERIAL-VERIF", "title": "Material Verification Sampling Programme", "type": "report", "status": "partial", "location": "Midstream/Integrity/Material/", "last_updated": "2026-01-08", "owner": "Asset Integrity & Reliability"},
        ],
        "worker_safety": [
            {"doc_id": "CONTRACTOR-PSM-EVAL", "title": "Contractor Process-Safety Performance Evaluation", "type": "review", "status": "needs_update", "location": "HSE/Contractors/", "last_updated": "2024-11-20", "owner": "Supply Chain & Contractor Management"},
            {"doc_id": "TRAINING-RECORDS", "title": "Process-Specific Training Records — Contractor Personnel", "type": "log", "status": "partial", "location": "HSE/Training/", "last_updated": "2026-02-28", "owner": "HSE"},
        ],
    },
    "cases": [
        {"case_number": "EPA-CD-2023-0412", "case_title": "Consent Decree: Clean Air Act Violations at Processing Facilities", "regulator": "EPA", "case_type": "enforcement", "status": "ongoing", "filing_date": "2023-03-09", "resolution_date": None, "penalty_amount": 45000000, "summary": "Illustrative. Federal consent decree resolving Clean Air Act violations across multiple processing facilities. Civil penalty accompanied by ~$400M in injunctive relief, a third-party monitor, and eight years of court-supervised obligations.", "key_findings": "The civil penalty was the smallest part of the cost. Injunctive relief and the monitor dominated. Repeated Title V deviations that were individually minor established the pattern that justified the decree.", "precedent_tags": "emissions,epa,consent_decree,clean_air_act,injunctive_relief,title_v,pattern_of_violation"},
        {"case_number": "OSHA-PSM-2024-0088", "case_title": "OSHA Willful Citations: PSM Mechanical Integrity Failures", "regulator": "OSHA", "case_type": "enforcement", "status": "resolved", "filing_date": "2024-06-14", "resolution_date": "2025-03-21", "penalty_amount": 1650000, "summary": "Illustrative. Willful and repeat citations following a release event. Safety-critical relief devices were past their inspection interval; deviations had been noted but never risk-assessed or closed.", "key_findings": "Mechanical integrity records existed but showed overdue tests with no documented risk acceptance. The recordkeeping gap — not the equipment failure — established willfulness. Referred to EPA for RMP review.", "precedent_tags": "process_safety,osha,psm,mechanical_integrity,willful,recordkeeping,rmp_referral"},
        {"case_number": "PHMSA-2024-0231", "case_title": "PHMSA Civil Penalty: Inadequate MAOP Records", "regulator": "PHMSA", "case_type": "enforcement", "status": "resolved", "filing_date": "2024-09-02", "resolution_date": "2025-08-11", "penalty_amount": 3900000, "summary": "Illustrative. Civil penalty for failure to hold traceable, verifiable and complete records establishing MAOP across HCA segments. No pipeline failure occurred — the records inadequacy was itself the violation.", "key_findings": "Records existed but could not be corroborated by a second independent source, so were not 'verifiable'. Operator argued loss of legacy records; PHMSA held that loss of records is not a defence.", "precedent_tags": "pipeline_integrity,phmsa,maop,tvc_records,recordkeeping,no_incident_required"},
        {"case_number": "EPA-METH-2025-0117", "case_title": "Super-Emitter Response Failure — Notice of Violation", "regulator": "EPA", "case_type": "enforcement", "status": "ongoing", "filing_date": "2025-11-14", "resolution_date": None, "penalty_amount": 2100000, "summary": "Illustrative. NOV for failure to investigate and respond to third-party super-emitter notifications within the required window. Satellite and aerial data from an NGO established the emission event independently of the operator's own monitoring.", "key_findings": "Third-party monitoring data is now an enforcement input the operator does not control. The operator's quarterly OGI survey had not detected the event; the defence that internal monitoring was compliant did not succeed.", "precedent_tags": "emissions,epa,methane,super_emitter,third_party_data,ogi"},
        {"case_number": "SEC-CLIM-2025-004", "case_title": "SEC Inquiry: Methane Intensity Disclosure vs. Reported Data", "regulator": "SEC", "case_type": "investigation", "status": "ongoing", "filing_date": "2025-08-20", "resolution_date": None, "penalty_amount": 0, "summary": "Illustrative. Inquiry into whether publicly disclosed methane-intensity figures were consistent with data reported to EPA under Subpart W.", "key_findings": "Investor-facing sustainability reporting and regulatory reporting were produced by different functions from different data, and diverged. No reconciliation control existed between them.", "precedent_tags": "reporting,sec,disclosure,methane,esg,reconciliation_gap,greenwashing"},
    ],
    "penalty_timeline": [
        {"year": 2020, "regulator": "EPA", "total_penalties": 12000000, "case_count": 2, "categories": ["emissions", "environmental"]},
        {"year": 2021, "regulator": "EPA", "total_penalties": 8500000, "case_count": 1, "categories": ["emissions"]},
        {"year": 2022, "regulator": "EPA", "total_penalties": 21000000, "case_count": 2, "categories": ["emissions", "environmental"]},
        {"year": 2023, "regulator": "EPA", "total_penalties": 45000000, "case_count": 1, "categories": ["emissions"]},
        {"year": 2024, "regulator": "EPA", "total_penalties": 18000000, "case_count": 2, "categories": ["emissions", "environmental"]},
        {"year": 2025, "regulator": "EPA", "total_penalties": 2100000, "case_count": 1, "categories": ["emissions"]},
        {"year": 2022, "regulator": "OSHA", "total_penalties": 890000, "case_count": 2, "categories": ["process_safety"]},
        {"year": 2023, "regulator": "OSHA", "total_penalties": 1240000, "case_count": 1, "categories": ["process_safety"]},
        {"year": 2024, "regulator": "OSHA", "total_penalties": 1650000, "case_count": 1, "categories": ["process_safety"]},
        {"year": 2021, "regulator": "PHMSA", "total_penalties": 2400000, "case_count": 1, "categories": ["pipeline_integrity"]},
        {"year": 2023, "regulator": "PHMSA", "total_penalties": 1900000, "case_count": 1, "categories": ["pipeline_integrity"]},
        {"year": 2024, "regulator": "PHMSA", "total_penalties": 3900000, "case_count": 1, "categories": ["pipeline_integrity"]},
    ],
}


# ==========================================================================================
# PACK 4 — SERVICES (Business & Financial Services)
# ==========================================================================================

SERVICES = {
    "key": "services",
    "label": "Services (Business & Financial Services)",
    "vertical": "Services (SURE)",
    "company": "the Firm",
    "company_full": "a global business and financial services firm handling regulated client data",
    "tagline": "Client data processing at scale; operational resilience and third-party risk are the exposure",
    "regulators": [
        {"code": "SEC", "name": "Securities and Exchange Commission", "scope": "Cyber incident disclosure (8-K Item 1.05), books and records"},
        {"code": "EU-DORA", "name": "EU Digital Operational Resilience Act", "scope": "ICT risk, incident reporting, third-party oversight, resilience testing"},
        {"code": "EU-AI-ACT", "name": "EU Artificial Intelligence Act", "scope": "Risk-tiered AI obligations, high-risk system conformity"},
        {"code": "GDPR", "name": "EU/UK Data Protection Authorities", "scope": "GDPR — lawful basis, transfers, breach notification"},
        {"code": "NYDFS", "name": "NY Department of Financial Services", "scope": "Part 500 cybersecurity"},
        {"code": "AICPA", "name": "AICPA / SOC 2", "scope": "Trust Services Criteria (contractual assurance)"},
        {"code": "FTC", "name": "Federal Trade Commission", "scope": "Safeguards Rule, unfair/deceptive practices"},
    ],
    "departments": [
        "Client Delivery / Operations",
        "Information Security",
        "Risk & Compliance",
        "Data Privacy Office",
        "Legal",
        "Third-Party / Vendor Risk",
        "Technology & Platform Engineering",
        "AI Governance",
        "HR / People",
        "Finance & Internal Audit",
    ],
    "existing_obligations": [
        "SOC 2 Type II (Trust Services Criteria)",
        "ISO/IEC 27001 (ISMS)",
        "GDPR (lawful basis, DPIAs, international transfers, 72-hour breach notification)",
        "CCPA/CPRA",
        "SOX (financial reporting controls)",
        "PCI DSS (where card data is processed)",
        "NIST Cybersecurity Framework 2.0",
        "NYDFS Part 500",
        "Client contractual security schedules and audit rights",
    ],
    "enterprise_profile": """- Annual revenue: ~$18B
- Workforce: ~300,000 employees globally, delivering from multiple jurisdictions
- Processes regulated client data (financial, health, personal) as a processor/service provider
- Client contracts carry audit rights, security schedules and step-in rights — a compliance failure is a
  contractual breach with named clients, not only a regulatory one
- Concentration risk: a single control failure can trigger simultaneous notification obligations across
  dozens of client relationships and multiple regulators
- Operational resilience (DORA) shifts the burden from "did you have a control" to "can you prove you tested it\"""",
    "categories": ["cybersecurity", "operational_resilience", "data_privacy", "ai_governance", "third_party_risk", "reporting", "financial_controls"],
    "financial_hook": (
        "For a services firm the regulator is only one claimant. Client contracts carry audit rights, "
        "service credits and step-in rights, so an evidence gap surfaces simultaneously as a regulatory "
        "finding and a breach of dozens of client agreements. Evidence quality is revenue protection."
    ),
    "regulations": [
        {
            "source": "EU-DORA",
            "title": "DORA: ICT Third-Party Risk and Threat-Led Penetration Testing Requirements",
            "url": "https://www.eiopa.europa.eu/digital-operational-resilience-act-dora_en",
            "published_date": "2026-01-17",
            "text": """The Digital Operational Resilience Act establishes uniform requirements for the
            security of network and information systems supporting the business processes of financial
            entities and their critical ICT third-party providers.

            1. ICT RISK MANAGEMENT FRAMEWORK: Entities must maintain a documented ICT risk management
               framework, reviewed at least annually and after every major ICT-related incident. The
               management body bears final responsibility and must be demonstrably engaged — board minutes
               evidencing review are an expected artefact.

            2. INCIDENT REPORTING: Major ICT-related incidents must be reported to the competent authority
               via an initial notification within 4 hours of classification (and no later than 24 hours from
               awareness), an intermediate report within 72 hours, and a final report within one month.

            3. THREAT-LED PENETRATION TESTING (TLPT): Entities identified as significant must conduct TLPT
               at least every 3 years, covering critical functions, using external testers, and including
               ICT third-party providers within scope.

            4. THIRD-PARTY REGISTER: A register of information on all contractual arrangements for ICT
               services must be maintained and submitted to the competent authority annually. Contracts must
               contain exit strategies, audit rights, and service-level descriptions.

            5. CONCENTRATION RISK: Entities must assess and document concentration risk arising from
               reliance on a single ICT provider or from providers that are not readily substitutable.

            Applicable from January 2025 with supervisory expectations escalating through 2026.
            Non-compliance may result in administrative penalties, periodic penalty payments of up to 1%
            of average daily worldwide turnover, and public statements naming the entity."""
        },
        {
            "source": "EU-AI-ACT",
            "title": "EU AI Act: High-Risk System Obligations and GPAI Transparency",
            "url": "https://artificialintelligenceact.eu/",
            "published_date": "2026-02-02",
            "text": """The EU Artificial Intelligence Act establishes harmonised rules on artificial
            intelligence, applying risk-tiered obligations to providers and deployers.

            1. PROHIBITED PRACTICES: Social scoring, untargeted facial-image scraping, and emotion inference
               in the workplace are prohibited outright. Deployers must confirm no in-scope system performs
               these functions.

            2. HIGH-RISK CLASSIFICATION: AI systems used in employment (recruitment, promotion, termination),
               creditworthiness assessment, and access to essential services are high-risk. A conformity
               assessment, CE marking, and registration in the EU database are required before placing on
               the market or putting into service.

            3. HIGH-RISK OBLIGATIONS: Risk management system, data governance (training data relevance,
               representativeness, bias examination), technical documentation, automatic logging, human
               oversight design, and accuracy/robustness/cybersecurity requirements.

            4. DEPLOYER DUTIES: Deployers of high-risk systems must ensure human oversight by competent
               persons, monitor operation, retain logs for at least 6 months, and conduct a fundamental
               rights impact assessment where the deployer is a body governed by public law or provides
               essential services.

            5. GPAI TRANSPARENCY: Providers of general-purpose AI models must maintain technical
               documentation, a copyright policy, and a sufficiently detailed summary of training content.

            Phased application: prohibitions from February 2025; GPAI obligations from August 2025;
            high-risk obligations from August 2026. Penalties: up to EUR 35,000,000 or 7% of total worldwide
            annual turnover for prohibited practices; up to EUR 15,000,000 or 3% for most other breaches."""
        },
        {
            "source": "SEC",
            "title": "Cybersecurity Disclosure: Form 8-K Item 1.05 Materiality Determination Guidance",
            "url": "https://www.sec.gov/rules/final/2023/33-11216.pdf",
            "published_date": "2026-03-11",
            "text": """The Securities and Exchange Commission issues guidance on the determination of
            materiality and the timing of disclosure for cybersecurity incidents.

            1. FOUR-DAY CLOCK: A registrant must disclose a material cybersecurity incident on Form 8-K
               Item 1.05 within four business days of determining that the incident is material — NOT four
               days from discovery. However, the materiality determination must be made "without unreasonable
               delay" after discovery. A slow determination is itself a violation.

            2. MATERIALITY: Assessment must consider qualitative factors — reputational harm, effect on
               customer and vendor relationships, and the possibility of litigation or regulatory action —
               not only quantitative financial impact.

            3. AGGREGATION: A series of related but individually immaterial incidents must be assessed in
               aggregate. Repeated intrusions by the same actor, or exploiting the same vulnerability, are
               related.

            4. THIRD-PARTY INCIDENTS: An incident at a third-party service provider that materially affects
               the registrant is disclosable by the registrant. Lack of information from the provider does
               not excuse the obligation; the registrant must disclose based on information reasonably
               available.

            5. RISK MANAGEMENT DISCLOSURE (Item 106): Annual description of processes for assessing,
               identifying and managing material risks from cybersecurity threats, plus board oversight and
               management's role.

            Effective immediately. Enforcement to date has focused on registrants whose disclosures
            described controls in terms not supported by internal assessments known to management."""
        },
    ],
    "audit_types": {
        "SOC 2 Type II Readiness": [
            {"id": "SOC-001", "text": "Control operating effectiveness evidenced across the full audit period", "category": "cybersecurity", "deadline": "Ongoing"},
            {"id": "SOC-002", "text": "Access reviews completed quarterly with remediation tracked to closure", "category": "cybersecurity", "deadline": "Ongoing"},
            {"id": "SOC-003", "text": "Change management evidence for every production change", "category": "cybersecurity", "deadline": "Ongoing"},
            {"id": "SOC-004", "text": "Vendor SOC 2 reports obtained and reviewed for all subservice organisations", "category": "third_party_risk", "deadline": "2026-09-30"},
        ],
        "DORA Operational Resilience Audit": [
            {"id": "DORA-001", "text": "ICT risk management framework reviewed annually with board evidence", "category": "operational_resilience", "deadline": "2026-12-31"},
            {"id": "DORA-002", "text": "Major incident reporting: 4h initial / 72h intermediate / 1mo final", "category": "operational_resilience", "deadline": "Ongoing"},
            {"id": "DORA-003", "text": "Threat-led penetration testing every 3 years including third parties", "category": "operational_resilience", "deadline": "2027-01-17"},
            {"id": "DORA-004", "text": "ICT third-party register complete with exit strategies and audit rights", "category": "third_party_risk", "deadline": "2026-06-30"},
            {"id": "DORA-005", "text": "Concentration risk assessment documented for non-substitutable providers", "category": "third_party_risk", "deadline": "2026-06-30"},
        ],
        "EU AI Act Conformity Audit": [
            {"id": "AI-001", "text": "AI system inventory with risk-tier classification", "category": "ai_governance", "deadline": "2026-08-02"},
            {"id": "AI-002", "text": "Conformity assessment and CE marking for high-risk systems", "category": "ai_governance", "deadline": "2026-08-02"},
            {"id": "AI-003", "text": "Training data governance: relevance, representativeness, bias examination", "category": "ai_governance", "deadline": "2026-08-02"},
            {"id": "AI-004", "text": "Human oversight design with competent named overseers", "category": "ai_governance", "deadline": "2026-08-02"},
            {"id": "AI-005", "text": "Automatic logging retained minimum 6 months", "category": "ai_governance", "deadline": "2026-08-02"},
        ],
        "GDPR / Privacy Audit": [
            {"id": "GD-001", "text": "Records of Processing Activities (Art. 30) current and complete", "category": "data_privacy", "deadline": "Ongoing"},
            {"id": "GD-002", "text": "DPIAs completed for all high-risk processing", "category": "data_privacy", "deadline": "2026-06-30"},
            {"id": "GD-003", "text": "International transfer mechanism (SCCs + TIA) for every transfer", "category": "data_privacy", "deadline": "2026-06-30"},
            {"id": "GD-004", "text": "72-hour breach notification process tested", "category": "data_privacy", "deadline": "2026-09-30"},
        ],
    },
    "evidence": {
        "cybersecurity": [
            {"doc_id": "SOC2-2025", "title": "SOC 2 Type II Report FY2025", "type": "assessment", "status": "current", "location": "GRC/SOC2/", "last_updated": "2026-01-31", "owner": "Risk & Compliance"},
            {"doc_id": "ACCESS-REVIEW-Q1", "title": "Q1 2026 Quarterly Access Review", "type": "review", "status": "current", "location": "GRC/Access/", "last_updated": "2026-04-04", "owner": "Information Security"},
            {"doc_id": "CHANGE-MGMT-LOG", "title": "Production Change Management Log", "type": "log", "status": "current", "location": "Tech/ChangeMgmt/", "last_updated": "2026-04-06", "owner": "Technology & Platform Engineering"},
            {"doc_id": "PENTEST-2025", "title": "Annual Penetration Test Report 2025", "type": "report", "status": "current", "location": "GRC/PenTest/", "last_updated": "2025-10-18", "owner": "Information Security"},
        ],
        "operational_resilience": [
            {"doc_id": "ICT-RISK-FRAMEWORK", "title": "ICT Risk Management Framework", "type": "policy", "status": "needs_update", "location": "GRC/DORA/Framework/", "last_updated": "2024-09-30", "owner": "Risk & Compliance"},
            {"doc_id": "BOARD-ICT-MINUTES", "title": "Board Review of ICT Risk — Minutes", "type": "log", "status": "missing", "location": "GRC/DORA/Board/", "last_updated": "—", "owner": "Risk & Compliance"},
            {"doc_id": "TLPT-SCOPE", "title": "Threat-Led Penetration Test Scope and Provider Selection", "type": "plan", "status": "partial", "location": "GRC/DORA/TLPT/", "last_updated": "2026-02-20", "owner": "Information Security"},
            {"doc_id": "INCIDENT-RUNBOOK", "title": "Major ICT Incident Reporting Runbook (4h/72h/1mo)", "type": "procedure", "status": "partial", "location": "GRC/DORA/Incident/", "last_updated": "2026-01-12", "owner": "Information Security"},
        ],
        "third_party_risk": [
            {"doc_id": "ICT-3P-REGISTER", "title": "ICT Third-Party Register (DORA Art. 28)", "type": "registry", "status": "partial", "location": "GRC/DORA/Register/", "last_updated": "2026-03-05", "owner": "Third-Party / Vendor Risk"},
            {"doc_id": "CONCENTRATION-RISK", "title": "ICT Concentration Risk Assessment", "type": "analysis", "status": "missing", "location": "GRC/DORA/Concentration/", "last_updated": "—", "owner": "Third-Party / Vendor Risk"},
            {"doc_id": "VENDOR-SOC2-LIBRARY", "title": "Subservice Organisation SOC 2 Report Library", "type": "registry", "status": "needs_update", "location": "GRC/Vendors/", "last_updated": "2025-05-14", "owner": "Third-Party / Vendor Risk"},
            {"doc_id": "EXIT-STRATEGIES", "title": "ICT Provider Exit Strategy Documentation", "type": "plan", "status": "partial", "location": "GRC/DORA/Exit/", "last_updated": "2026-02-01", "owner": "Third-Party / Vendor Risk"},
        ],
        "ai_governance": [
            {"doc_id": "AI-INVENTORY", "title": "AI System Inventory and Risk-Tier Classification", "type": "inventory", "status": "partial", "location": "AIGov/Inventory/", "last_updated": "2026-03-01", "owner": "AI Governance"},
            {"doc_id": "AI-CONFORMITY", "title": "High-Risk AI Conformity Assessment — Recruitment Screening", "type": "assessment", "status": "missing", "location": "AIGov/Conformity/", "last_updated": "—", "owner": "AI Governance"},
            {"doc_id": "AI-BIAS-EXAM", "title": "Training Data Bias Examination Records", "type": "analysis", "status": "partial", "location": "AIGov/DataGov/", "last_updated": "2026-01-25", "owner": "AI Governance"},
            {"doc_id": "AI-OVERSIGHT-DESIGN", "title": "Human Oversight Design and Named Overseers", "type": "procedure", "status": "missing", "location": "AIGov/Oversight/", "last_updated": "—", "owner": "AI Governance"},
        ],
        "data_privacy": [
            {"doc_id": "ROPA", "title": "Records of Processing Activities (GDPR Art. 30)", "type": "registry", "status": "current", "location": "Privacy/ROPA/", "last_updated": "2026-02-28", "owner": "Data Privacy Office"},
            {"doc_id": "DPIA-LIBRARY", "title": "Data Protection Impact Assessment Library", "type": "assessment", "status": "partial", "location": "Privacy/DPIA/", "last_updated": "2026-01-18", "owner": "Data Privacy Office"},
            {"doc_id": "TIA-TRANSFERS", "title": "Transfer Impact Assessments and SCC Register", "type": "analysis", "status": "needs_update", "location": "Privacy/Transfers/", "last_updated": "2025-03-22", "owner": "Data Privacy Office"},
            {"doc_id": "BREACH-DRILL", "title": "72-Hour Breach Notification Drill Results", "type": "audit", "status": "needs_update", "location": "Privacy/Breach/", "last_updated": "2024-11-08", "owner": "Data Privacy Office"},
        ],
    },
    "cases": [
        {"case_number": "SEC-CYBER-2024-019", "case_title": "SEC Enforcement: Cybersecurity Disclosure Not Supported by Internal Assessments", "regulator": "SEC", "case_type": "enforcement", "status": "resolved", "filing_date": "2024-04-22", "resolution_date": "2025-02-13", "penalty_amount": 4000000, "summary": "Illustrative. Enforcement where public risk-factor disclosure described cybersecurity controls in terms contradicted by internal assessments known to management.", "key_findings": "The violation was the gap between what was disclosed and what management knew — not the underlying control weakness. Internal audit findings existed and were never reflected in disclosure.", "precedent_tags": "reporting,sec,cyber_disclosure,materiality,internal_vs_external,8k"},
        {"case_number": "GDPR-DPA-2023-0561", "case_title": "GDPR Fine: International Transfers Without Valid Mechanism", "regulator": "GDPR", "case_type": "enforcement", "status": "resolved", "filing_date": "2023-06-30", "resolution_date": "2024-05-09", "penalty_amount": 28000000, "summary": "Illustrative. Administrative fine for transferring client personal data to a third country without a valid transfer mechanism or a completed transfer impact assessment.", "key_findings": "SCCs were executed but no TIA was performed, so the SCCs alone did not establish an adequate level of protection. The firm could not evidence which data flowed where — the ROPA was incomplete.", "precedent_tags": "data_privacy,gdpr,transfers,sccs,tia,ropa,recordkeeping"},
        {"case_number": "DORA-NCA-2026-0033", "case_title": "Supervisory Finding: Incomplete ICT Third-Party Register", "regulator": "EU-DORA", "case_type": "audit", "status": "ongoing", "filing_date": "2026-02-14", "resolution_date": None, "penalty_amount": 0, "summary": "Illustrative. Competent authority finding that the ICT third-party register omitted subcontractors of critical providers and lacked documented exit strategies.", "key_findings": "Fourth-party (subcontractor) visibility was absent. The firm knew its direct providers but could not evidence who they in turn depended on — precisely the concentration risk DORA targets.", "precedent_tags": "operational_resilience,dora,third_party,fourth_party,concentration_risk,register"},
        {"case_number": "NYDFS-500-2024-0077", "case_title": "NYDFS Part 500: MFA Gap and Delayed Incident Notification", "regulator": "NYDFS", "case_type": "enforcement", "status": "resolved", "filing_date": "2024-08-05", "resolution_date": "2025-06-19", "penalty_amount": 11500000, "summary": "Illustrative. Consent order over incomplete MFA coverage and failure to notify within 72 hours of determining a reportable cybersecurity event occurred.", "key_findings": "MFA was deployed but exceptions accumulated without documented risk acceptance or compensating controls. The exception register was the finding.", "precedent_tags": "cybersecurity,nydfs,mfa,exceptions,notification,consent_order"},
        {"case_number": "AI-ACT-2026-0002", "case_title": "AI Act Inquiry: Recruitment Screening Model Without Conformity Assessment", "regulator": "EU-AI-ACT", "case_type": "investigation", "status": "ongoing", "filing_date": "2026-03-20", "resolution_date": None, "penalty_amount": 0, "summary": "Illustrative. Inquiry into deployment of an AI recruitment-screening system classified as high-risk without a completed conformity assessment, CE marking or EU database registration.", "key_findings": "The firm's AI inventory did not classify the system as high-risk because it was procured as a vendor feature rather than built. Procurement route does not change the risk tier.", "precedent_tags": "ai_governance,eu_ai_act,high_risk,conformity,procurement,inventory_gap"},
    ],
    "penalty_timeline": [
        {"year": 2021, "regulator": "GDPR", "total_penalties": 12000000, "case_count": 1, "categories": ["data_privacy"]},
        {"year": 2022, "regulator": "GDPR", "total_penalties": 19000000, "case_count": 2, "categories": ["data_privacy", "data_privacy"]},
        {"year": 2023, "regulator": "GDPR", "total_penalties": 28000000, "case_count": 1, "categories": ["data_privacy"]},
        {"year": 2024, "regulator": "GDPR", "total_penalties": 9400000, "case_count": 1, "categories": ["data_privacy"]},
        {"year": 2023, "regulator": "SEC", "total_penalties": 2500000, "case_count": 1, "categories": ["reporting"]},
        {"year": 2024, "regulator": "SEC", "total_penalties": 4000000, "case_count": 1, "categories": ["reporting"]},
        {"year": 2023, "regulator": "NYDFS", "total_penalties": 4800000, "case_count": 1, "categories": ["cybersecurity"]},
        {"year": 2024, "regulator": "NYDFS", "total_penalties": 11500000, "case_count": 1, "categories": ["cybersecurity"]},
    ],
}


# ==========================================================================================
# Registry
# ==========================================================================================

DOMAIN_PACKS = {
    ENERGY_UTILITIES["key"]: ENERGY_UTILITIES,
    RETAIL["key"]: RETAIL,
    RESOURCES["key"]: RESOURCES,
    SERVICES["key"]: SERVICES,
}

DOMAIN_LABELS = {k: v["label"] for k, v in DOMAIN_PACKS.items()}


def _load_corpora(pack: dict) -> dict:
    """Attach the Energy pack's corpora, which live in the agent modules.

    Imported lazily: the agent modules import core.prompts, which imports this module,
    so a top-level import here would be circular.
    """
    if pack["key"] != "energy_utilities" or pack["regulations"] is not None:
        return pack

    from agents.regulatory_monitor.tools import SAMPLE_REGULATORY_UPDATES
    from agents.audit_prep.graph import SAMPLE_EVIDENCE, ENERGY_AUDIT_TYPES
    from agents.case_analytics.chain import SAMPLE_CASES, PENALTY_TIMELINE

    pack["regulations"] = SAMPLE_REGULATORY_UPDATES
    pack["evidence"] = SAMPLE_EVIDENCE
    pack["cases"] = SAMPLE_CASES
    pack["penalty_timeline"] = PENALTY_TIMELINE
    pack["audit_types"] = ENERGY_AUDIT_TYPES
    return pack


def set_active_domain(key: str) -> None:
    """Set the active industry pack for this process."""
    if key not in DOMAIN_PACKS:
        raise ValueError(f"Unknown domain '{key}'. Known: {list(DOMAIN_PACKS)}")
    os.environ["ACTIVE_DOMAIN"] = key


def get_active_domain_key() -> str:
    key = os.getenv("ACTIVE_DOMAIN", DEFAULT_DOMAIN)
    return key if key in DOMAIN_PACKS else DEFAULT_DOMAIN


def get_domain(key: str | None = None) -> dict:
    """Return the active (or named) domain pack, with corpora attached."""
    return _load_corpora(DOMAIN_PACKS[key or get_active_domain_key()])


def build_system_context(key: str | None = None) -> str:
    """Compose the shared system context for every agent from the active pack.

    This is the single point of domain grounding. Swap the pack, and all seven agents
    re-target to the new industry without a line of graph code changing.
    """
    d = get_domain(key)
    regulators = "\n".join(f"- {r['code']} ({r['name']}) — {r['scope']}" for r in d["regulators"])
    priorities = "\n".join(f"- {c}" for c in d["categories"])

    return f"""You are an AI compliance analyst specialized in {d['label']} regulation.
You work for {d['company']} — {d['company_full']}.

Key regulatory bodies you monitor:
{regulators}

WHY COMPLIANCE EVIDENCE MATTERS FINANCIALLY HERE:
{d['financial_hook']}
Treat an evidence gap as financial risk, not merely as audit risk.

Obligation categories in this domain:
{priorities}

ACCURACY RULES — non-negotiable:
- Never invent an obligation, deadline, penalty amount, or citation. If the source text does not
  state it, write "not stated in source" rather than estimating.
- Every obligation you extract MUST carry a verbatim quote from the source text supporting it.
- Distinguish what the regulation REQUIRES from what you INFER. Label inferences as inferences.
- Your output is decision-support for qualified human reviewers. It is never a final compliance
  determination, and never goes to a regulator without human review and sign-off.
"""
```

## `core/llm.py`

```python
"""
Regulatory Compliance AI - LLM Client Configuration
Primary: OpenAI GPT-4o (cost-effective for demo)
Fallback: Claude Sonnet 4.6 (higher accuracy for regulatory text)

If an ANTHROPIC_API_KEY is configured alongside OPENAI_API_KEY, the primary
client automatically fails over to Claude at *runtime* whenever OpenAI errors
(invalid/expired key -> 401, rate limit -> 429, outage). If only one provider's
key is present, that provider is used directly.
"""

import os

# Current model IDs (kept in one place so they're easy to bump).
OPENAI_PRIMARY_MODEL = "gpt-4o"
OPENAI_MINI_MODEL = "gpt-4o-mini"
CLAUDE_SONNET_MODEL = "claude-sonnet-4-6"
CLAUDE_OPUS_MODEL = "claude-opus-4-8"


def _has_openai() -> bool:
    return bool(os.getenv("OPENAI_API_KEY"))


def _has_anthropic() -> bool:
    return bool(os.getenv("ANTHROPIC_API_KEY"))


def _build_openai(model: str = OPENAI_PRIMARY_MODEL, max_tokens: int = 4096):
    from langchain_openai import ChatOpenAI
    return ChatOpenAI(
        model=model,
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        temperature=0,
        max_tokens=max_tokens,
    )


def _build_claude(model: str = CLAUDE_SONNET_MODEL, max_tokens: int = 4096):
    from langchain_anthropic import ChatAnthropic
    return ChatAnthropic(
        model=model,
        anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
        temperature=0,
        max_tokens=max_tokens,
    )


def get_openai_primary():
    """GPT-4o — primary LLM for the demo (cost-effective).

    When an ANTHROPIC_API_KEY is also configured, returns a runnable that
    automatically falls over to Claude Sonnet if the OpenAI call raises (e.g.
    the 401 invalid_api_key that crashes the pipeline when the OpenAI key is
    revoked). With no OpenAI key at all, Claude is used directly.
    """
    if _has_openai():
        primary = _build_openai()
        if _has_anthropic():
            return primary.with_fallbacks([_build_claude()])
        return primary
    if _has_anthropic():
        return _build_claude()
    raise RuntimeError(
        "No LLM credentials configured. Set OPENAI_API_KEY (and optionally "
        "ANTHROPIC_API_KEY for automatic failover) in Streamlit Cloud Secrets."
    )


def get_openai_mini():
    """GPT-4o-mini — lightweight tasks (classification, summaries).

    Falls over to Claude Sonnet when Anthropic is configured; falls back to
    Claude as primary when no OpenAI key is present.
    """
    if _has_openai():
        primary = _build_openai(model=OPENAI_MINI_MODEL)
        if _has_anthropic():
            return primary.with_fallbacks([_build_claude()])
        return primary
    if _has_anthropic():
        return _build_claude()
    raise RuntimeError(
        "No LLM credentials configured. Set OPENAI_API_KEY (and optionally "
        "ANTHROPIC_API_KEY for automatic failover) in Streamlit Cloud Secrets."
    )


def get_claude_sonnet():
    """Claude Sonnet 4.6 — fallback for high-accuracy regulatory analysis."""
    try:
        if _has_anthropic():
            return _build_claude(model=CLAUDE_SONNET_MODEL)
    except Exception:
        pass
    # If Anthropic not available, fall back to OpenAI.
    return get_openai_primary()


def get_claude_opus():
    """Claude Opus 4.8 — heavy reasoning. Falls back to GPT-4o for demo."""
    try:
        if _has_anthropic():
            return _build_claude(model=CLAUDE_OPUS_MODEL, max_tokens=8192)
    except Exception:
        pass
    # Fallback to GPT-4o.
    return get_openai_primary()


def get_llm(tier: str = "primary"):
    """Get LLM by tier.

    Tiers:
      'primary'  — GPT-4o (default, cost-effective)
      'mini'     — GPT-4o-mini (lightweight tasks)
      'advanced' — Claude Sonnet (high-accuracy fallback)
      'opus'     — Claude Opus (complex reasoning, falls back to GPT-4o)
    """
    if tier == "opus":
        return get_claude_opus()
    elif tier == "advanced":
        return get_claude_sonnet()
    elif tier == "mini":
        return get_openai_mini()
    else:
        return get_openai_primary()
```

## `core/vectorstore.py`

```python
"""
Regulatory Compliance AI - Vector Store
In-memory vector search for Streamlit Cloud compatibility.
Uses simple TF-IDF similarity when ChromaDB is unavailable (Python 3.14 protobuf issue).
"""

import os
import re
import math
from collections import Counter

# Collection names
COLLECTION_REGULATIONS = "pge_regulations"
COLLECTION_OBLIGATIONS = "pge_obligations"
COLLECTION_CASES = "pge_cases"
COLLECTION_AUDIT = "pge_audit_evidence"

# --- In-memory vector store (Streamlit Cloud compatible) ---
# Stores documents as plain text with TF-IDF-based similarity search.
# No external dependencies — works on any Python version.

_store: dict[str, list[dict]] = {}


def _tokenize(text: str) -> list[str]:
    """Simple whitespace + punctuation tokenizer."""
    return re.findall(r'\b\w+\b', text.lower())


def _tfidf_similarity(query_tokens: list[str], doc_tokens: list[str]) -> float:
    """Compute a simple TF-IDF cosine-like similarity score."""
    if not query_tokens or not doc_tokens:
        return 0.0
    query_counts = Counter(query_tokens)
    doc_counts = Counter(doc_tokens)
    # Intersection terms
    common = set(query_counts.keys()) & set(doc_counts.keys())
    if not common:
        return 0.0
    # Simple dot product / magnitude
    dot = sum(query_counts[t] * doc_counts[t] for t in common)
    mag_q = math.sqrt(sum(v * v for v in query_counts.values()))
    mag_d = math.sqrt(sum(v * v for v in doc_counts.values()))
    if mag_q == 0 or mag_d == 0:
        return 0.0
    return dot / (mag_q * mag_d)


class SimpleDocument:
    """Lightweight document class matching LangChain Document interface."""
    def __init__(self, page_content: str, metadata: dict | None = None):
        self.page_content = page_content
        self.metadata = metadata or {}


def add_documents(collection_name: str, documents: list[str], metadatas: list[dict] | None = None):
    """Add documents to the in-memory store."""
    if collection_name not in _store:
        _store[collection_name] = []
    for i, doc_text in enumerate(documents):
        meta = metadatas[i] if metadatas and i < len(metadatas) else {}
        _store[collection_name].append({
            "text": doc_text,
            "tokens": _tokenize(doc_text),
            "metadata": meta,
        })
    return len(documents)


def search_documents(collection_name: str, query: str, k: int = 5) -> list[tuple]:
    """Semantic search using TF-IDF similarity.
    Returns list of (SimpleDocument, score) tuples.
    """
    if collection_name not in _store or not _store[collection_name]:
        return []

    query_tokens = _tokenize(query)
    scored = []
    for entry in _store[collection_name]:
        score = _tfidf_similarity(query_tokens, entry["tokens"])
        if score > 0:
            scored.append((entry, score))

    scored.sort(key=lambda x: x[1], reverse=True)
    results = []
    for entry, score in scored[:k]:
        doc = SimpleDocument(page_content=entry["text"], metadata=entry["metadata"])
        results.append((doc, score))
    return results


def get_collection_stats() -> dict:
    """Get document counts for all collections."""
    stats = {}
    for name in [COLLECTION_REGULATIONS, COLLECTION_OBLIGATIONS, COLLECTION_CASES, COLLECTION_AUDIT]:
        stats[name] = len(_store.get(name, []))
    return stats
```

## `core/db.py`

```python
"""
Regulatory Compliance AI - Database Layer
SQLite for prototype, PostgreSQL-ready schema for production.
"""

import sqlite3
import os
import json
from datetime import datetime
from contextlib import contextmanager

DB_PATH = os.getenv("DATABASE_PATH", "./data/pge_compliance.db")


@contextmanager
def get_db():
    """Context manager for database connections."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    """Initialize database schema."""
    with get_db() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS regulatory_changes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source TEXT NOT NULL,
                title TEXT NOT NULL,
                summary TEXT,
                change_type TEXT,
                severity TEXT DEFAULT 'medium',
                url TEXT,
                published_date TEXT,
                detected_date TEXT DEFAULT CURRENT_TIMESTAMP,
                affected_departments TEXT,
                obligations_json TEXT,
                status TEXT DEFAULT 'new',
                reviewed_by TEXT,
                review_notes TEXT
            );

            CREATE TABLE IF NOT EXISTS obligations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                regulation_id INTEGER,
                obligation_text TEXT NOT NULL,
                category TEXT,
                owner_department TEXT,
                deadline TEXT,
                compliance_status TEXT DEFAULT 'pending',
                impact_score REAL,
                cost_estimate REAL,
                created_date TEXT DEFAULT CURRENT_TIMESTAMP,
                last_assessed TEXT,
                FOREIGN KEY (regulation_id) REFERENCES regulatory_changes(id)
            );

            CREATE TABLE IF NOT EXISTS audit_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                audit_name TEXT NOT NULL,
                audit_type TEXT,
                regulation_ref TEXT,
                obligation_id INTEGER,
                evidence_status TEXT DEFAULT 'missing',
                evidence_path TEXT,
                gap_description TEXT,
                remediation_plan TEXT,
                due_date TEXT,
                created_date TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (obligation_id) REFERENCES obligations(id)
            );

            CREATE TABLE IF NOT EXISTS cases (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                case_number TEXT UNIQUE,
                case_title TEXT NOT NULL,
                regulator TEXT,
                case_type TEXT,
                status TEXT,
                filing_date TEXT,
                resolution_date TEXT,
                penalty_amount REAL,
                summary TEXT,
                key_findings TEXT,
                precedent_tags TEXT,
                created_date TEXT DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS agent_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                agent_name TEXT NOT NULL,
                run_id TEXT,
                status TEXT DEFAULT 'running',
                input_summary TEXT,
                output_summary TEXT,
                tokens_used INTEGER,
                cost_estimate REAL,
                started_at TEXT DEFAULT CURRENT_TIMESTAMP,
                completed_at TEXT,
                trace_json TEXT
            );
        """)


def log_agent_run(agent_name: str, run_id: str, input_summary: str) -> int:
    """Log the start of an agent run."""
    with get_db() as conn:
        cursor = conn.execute(
            "INSERT INTO agent_runs (agent_name, run_id, input_summary) VALUES (?, ?, ?)",
            (agent_name, run_id, input_summary)
        )
        return cursor.lastrowid


def complete_agent_run(row_id: int, output_summary: str, tokens_used: int = 0, cost: float = 0.0):
    """Mark an agent run as completed."""
    with get_db() as conn:
        conn.execute(
            "UPDATE agent_runs SET status='completed', output_summary=?, tokens_used=?, cost_estimate=?, completed_at=? WHERE id=?",
            (output_summary, tokens_used, cost, datetime.utcnow().isoformat(), row_id)
        )


def save_regulatory_change(data: dict) -> int:
    """Save a detected regulatory change."""
    with get_db() as conn:
        cursor = conn.execute(
            """INSERT INTO regulatory_changes
               (source, title, summary, change_type, severity, url, published_date, affected_departments, obligations_json)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (data.get("source"), data.get("title"), data.get("summary"),
             data.get("change_type"), data.get("severity"), data.get("url"),
             data.get("published_date"), data.get("affected_departments"),
             json.dumps(data.get("obligations", [])))
        )
        return cursor.lastrowid


def get_recent_changes(limit: int = 20) -> list:
    """Get recent regulatory changes."""
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM regulatory_changes ORDER BY detected_date DESC LIMIT ?",
            (limit,)
        ).fetchall()
        return [dict(r) for r in rows]


def save_obligation(data: dict) -> int:
    """Save an obligation record."""
    with get_db() as conn:
        cursor = conn.execute(
            """INSERT INTO obligations
               (regulation_id, obligation_text, category, owner_department, deadline, impact_score, cost_estimate)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (data.get("regulation_id"), data.get("obligation_text"), data.get("category"),
             data.get("owner_department"), data.get("deadline"),
             data.get("impact_score"), data.get("cost_estimate"))
        )
        return cursor.lastrowid


def get_obligations(status: str | None = None) -> list:
    """Get obligations, optionally filtered by status."""
    with get_db() as conn:
        if status:
            rows = conn.execute(
                "SELECT * FROM obligations WHERE compliance_status = ? ORDER BY deadline", (status,)
            ).fetchall()
        else:
            rows = conn.execute("SELECT * FROM obligations ORDER BY deadline").fetchall()
        return [dict(r) for r in rows]


def save_case(data: dict) -> int:
    """Save a case record."""
    with get_db() as conn:
        cursor = conn.execute(
            """INSERT OR IGNORE INTO cases
               (case_number, case_title, regulator, case_type, status, filing_date,
                resolution_date, penalty_amount, summary, key_findings, precedent_tags)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (data.get("case_number"), data.get("case_title"), data.get("regulator"),
             data.get("case_type"), data.get("status"), data.get("filing_date"),
             data.get("resolution_date"), data.get("penalty_amount"),
             data.get("summary"), data.get("key_findings"), data.get("precedent_tags"))
        )
        return cursor.lastrowid
```

## `core/embeddings.py`

```python
"""
Regulatory Compliance AI - Embedding Models
Lightweight implementation for Streamlit Cloud compatibility.
Uses in-memory TF-IDF vectorstore (no external embedding APIs needed for prototype).
"""

# Note: The vectorstore module uses built-in TF-IDF similarity search,
# so no external embedding model is needed for the prototype.
# When deploying to production with ChromaDB, uncomment the appropriate
# embedding provider below.

def get_embeddings():
    """Get embedding model. Returns None for in-memory TF-IDF mode.
    For production, configure one of the providers below.
    """
    import os

    voyage_key = os.getenv("VOYAGE_API_KEY")
    if voyage_key:
        try:
            from langchain_voyageai import VoyageAIEmbeddings
            return VoyageAIEmbeddings(
                voyage_api_key=voyage_key,
                model="voyage-law-2",
            )
        except ImportError:
            pass

    openai_key = os.getenv("OPENAI_API_KEY")
    if openai_key:
        try:
            from langchain_openai import OpenAIEmbeddings
            return OpenAIEmbeddings(
                openai_api_key=openai_key,
                model="text-embedding-3-small",
            )
        except ImportError:
            pass

    # Prototype mode: vectorstore uses built-in TF-IDF, no embeddings needed
    return None
```

## `api.py`

```python
"""
Regulatory Compliance AI — REST API
===================================

    uvicorn api:app --reload --port 8000
    OpenAPI spec:  http://localhost:8000/docs
    Machine spec:  http://localhost:8000/openapi.json   <-- give this to the React team

WHY THIS FILE EXISTS
--------------------
The Streamlit app has NO API layer. The page scripts call the agent functions directly, in-process.
That is fine for a Streamlit prototype and useless for anything else — you cannot build a React
frontend against a function call.

So porting to Topaz (React) is not a UI rewrite. It is an architectural split:

    Streamlit today                          Topaz tomorrow
    ---------------                          --------------
    pages/1_*.py calls run_regulatory_        React component -> POST /api/monitor/run
    monitor() directly, in-process            -> FastAPI -> the SAME Python function

THE AGENTS DO NOT CHANGE. Not one line. Every graph, every prompt, the provenance verifier and the
domain packs transfer unchanged. This file is the missing seam — the contract that should have
existed all along, and without which the React team is guessing.

Hand the React team `/openapi.json`. That is a machine-readable contract they can generate a typed
client from. It is worth more than any amount of prose in a blueprint.

WHAT THIS IS NOT
----------------
There is no auth, no rate limiting, no persistence and no async job queue here. WF-01 costs 2N+1 LLM
calls and takes minutes — in production it must be a background job with polling or SSE, not a
blocking POST. That is called out at the endpoint. Shipping this as-is behind a public route would be
a mistake, and pretending otherwise would be exactly the overclaim this product exists to prevent.
"""

from __future__ import annotations

import os
from typing import Any, Literal

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from core.domains import DOMAIN_PACKS, get_domain, set_active_domain

app = FastAPI(
    title="Regulatory Compliance AI",
    version="0.2.0",
    description=(
        "Seven agents turn dense regulation into testable obligations — each with a citation "
        "verified in CODE against the source text — score their impact, and assemble audit-ready "
        "evidence packages. A human always signs off; this API determines nothing."
    ),
)

# Topaz/React will run on a different origin. Lock this down before production.
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:5173").split(","),
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(RuntimeError)
def _runtime_error(request, exc: RuntimeError):
    """Never leak a stack trace to a client.

    A misconfigured LLM key was returning a raw 500 with a full traceback. A React team coding
    against that has no idea whether the server is broken or simply unconfigured, and a stack trace
    in an HTTP response is an information leak besides. Fail with a diagnosis, not a dump.
    """
    from fastapi.responses import JSONResponse
    msg = str(exc)
    if "credentials" in msg.lower() or "api_key" in msg.lower():
        return JSONResponse(
            status_code=503,
            content={
                "error": "llm_not_configured",
                "detail": "No LLM credentials configured on the server.",
                "fix": "Set OPENAI_API_KEY (and optionally ANTHROPIC_API_KEY for automatic "
                       "failover) in the environment or a .env file, then restart.",
                "hint": "GET /api/health reports llm_configured — check it before calling any "
                        "agent endpoint.",
            },
        )
    return JSONResponse(status_code=500,
                        content={"error": "agent_failure", "detail": msg[:500]})


# ==========================================================================================
# Shared models
# ==========================================================================================

class ReviewGate(BaseModel):
    """Attached to every agent response. The API is decision support, never a determination."""
    review_status: Literal["PENDING_HUMAN_REVIEW"] = "PENDING_HUMAN_REVIEW"
    disclaimer: str = (
        "AI-generated decision support. Not a compliance determination. Every obligation, gap and "
        "drafted response requires review and sign-off by qualified personnel before use, and no "
        "content may be submitted to a regulator without that sign-off."
    )


class Provenance(BaseModel):
    """Citation health for a run. The React UI MUST surface this — it is the trust story."""
    total: int
    verified: int
    unverified: int
    verified_pct: int


class Obligation(BaseModel):
    obligation_id: str
    description: str
    responsible_entity: str | None = None
    deadline: str | None = Field(None, description="or the literal string 'not stated in source'")
    measurement: str | None = None
    penalty: str | None = None
    category: str | None = None
    source_regulation: str | None = None
    source_body: str | None = None
    source_url: str | None = None
    severity: str | None = None
    # --- the provenance contract. React must render these differently. ---
    source_quote: str | None = Field(None, description="VERBATIM span copied from the regulation")
    source_section: str | None = None
    confidence: Literal["high", "medium", "low"] | None = None
    inferred: bool | None = None
    citation_verified: bool | None = Field(
        None,
        description=(
            "TRUE only if the quote was FOUND in the source text by core provenance verification. "
            "FALSE means the model may have paraphrased or fabricated it. The UI must show these "
            "with a warning badge and MUST NOT present them as equivalent to verified obligations."
        ),
    )


# ==========================================================================================
# Domain packs — the React app needs these to render its selectors
# ==========================================================================================

class Regulator(BaseModel):
    code: str
    name: str
    scope: str


class DomainSummary(BaseModel):
    key: str
    label: str
    vertical: str
    company: str
    company_full: str
    financial_hook: str
    regulators: list[Regulator]
    departments: list[str]
    categories: list[str]
    regulation_count: int
    case_count: int
    evidence_count: int
    audit_types: list[str]


@app.get("/api/domains", response_model=list[DomainSummary], tags=["domains"])
def list_domains():
    """All industry packs. Switching the pack re-targets all 7 agents — no agent code changes."""
    out = []
    for key in DOMAIN_PACKS:
        d = get_domain(key)
        out.append(DomainSummary(
            key=d["key"], label=d["label"], vertical=d["vertical"],
            company=d["company"], company_full=d["company_full"],
            financial_hook=d["financial_hook"],
            regulators=[Regulator(**r) for r in d["regulators"]],
            departments=d["departments"], categories=d["categories"],
            regulation_count=len(d["regulations"]),
            case_count=len(d["cases"]),
            evidence_count=sum(len(v) for v in d["evidence"].values()),
            audit_types=list(d["audit_types"]),
        ))
    return out


class RegulationSummary(BaseModel):
    index: int
    source: str
    title: str
    published_date: str
    url: str | None = None
    text: str


@app.get("/api/domains/{domain}/regulations", response_model=list[RegulationSummary],
         tags=["domains"])
def list_regulations(domain: str):
    if domain not in DOMAIN_PACKS:
        raise HTTPException(404, f"unknown domain '{domain}'")
    return [RegulationSummary(index=i, **{k: v for k, v in r.items()
                                          if k in {"source", "title", "published_date", "url", "text"}})
            for i, r in enumerate(get_domain(domain)["regulations"])]


@app.get("/api/domains/{domain}/audit-types", tags=["domains"])
def list_audit_types(domain: str) -> dict[str, list[dict]]:
    """Audit type -> the obligations that audit tests. Drives the Audit Prep screen."""
    if domain not in DOMAIN_PACKS:
        raise HTTPException(404, f"unknown domain '{domain}'")
    return get_domain(domain)["audit_types"]


@app.get("/api/domains/{domain}/cases", tags=["domains"])
def list_cases(domain: str) -> list[dict]:
    if domain not in DOMAIN_PACKS:
        raise HTTPException(404, f"unknown domain '{domain}'")
    return get_domain(domain)["cases"]


# ==========================================================================================
# WF-01 — Regulatory Monitor
# ==========================================================================================

class MonitorRequest(BaseModel):
    domain: str = "energy_utilities"
    source_filter: str = Field("all", description="Regulator code (e.g. 'OEIS', 'CPUC') or 'all'")


class Alert(BaseModel):
    alert_id: str
    source: str
    title: str
    severity: Literal["critical", "high", "medium", "low"] | str
    change_type: str | None = None
    summary: str | None = None
    key_deadlines: list[str] = []
    penalty_info: str | None = None
    obligation_count: int = 0
    obligations: list[Obligation] = []
    affected_departments: list[str] = []
    impact_mappings: list[dict[str, Any]] = []


class MonitorResponse(ReviewGate):
    alerts: list[Alert]
    obligations: list[Obligation]
    provenance: Provenance
    regulations_scanned: int


@app.post("/api/monitor/run", response_model=MonitorResponse, tags=["WF-01 Regulatory Monitor"])
def run_monitor(req: MonitorRequest):
    """Fetch → Classify → Extract (+VERIFY CITATION) → Map to departments → Alert.

    ⚠️ COST + LATENCY: this is `2N + 1` LLM calls for N regulations. For the full Energy pack that
    is 23 calls and takes minutes. **In production this MUST be a background job** with polling or
    SSE — a blocking POST will time out behind any real gateway. It is synchronous here so the
    contract is legible; do not ship it this way.
    """
    if req.domain not in DOMAIN_PACKS:
        raise HTTPException(404, f"unknown domain '{req.domain}'")
    set_active_domain(req.domain)

    from agents.regulatory_monitor.graph import run_regulatory_monitor
    result = run_regulatory_monitor(source_filter=req.source_filter)

    obligations = result.get("extracted_obligations", []) or []
    verified = sum(1 for o in obligations if o.get("citation_verified"))
    total = len(obligations)

    return MonitorResponse(
        alerts=[Alert(**a) for a in result.get("alerts", [])],
        obligations=[Obligation(**o) for o in obligations],
        provenance=Provenance(
            total=total, verified=verified, unverified=total - verified,
            verified_pct=round(100 * verified / total) if total else 0,
        ),
        regulations_scanned=len(result.get("raw_updates", []) or []),
    )


# ==========================================================================================
# WF-02 — Obligation Impact
# ==========================================================================================

class ImpactRequest(BaseModel):
    domain: str = "energy_utilities"
    regulation_index: int | None = Field(
        None, description="Index into GET /api/domains/{domain}/regulations")
    regulation_text: str | None = Field(None, description="Or paste raw regulatory text")
    regulation_source: str = "Unknown"


class ImpactResponse(ReviewGate):
    atomic_obligations: list[dict[str, Any]]
    cross_references: list[dict[str, Any]]
    impact_scores: list[dict[str, Any]]
    report: dict[str, Any] = Field(
        ..., description="executive_summary, cost range, earliest_deadline, key_risks, "
                         "recommended_actions[], board_attention_items[], regulatory_strategy")


@app.post("/api/impact/run", response_model=ImpactResponse, tags=["WF-02 Obligation Impact"])
def run_impact(req: ImpactRequest):
    """Decompose → Cross-reference → Score (cost/ops/timeline/penalty) → Executive report.

    Exactly 4 LLM calls. Predictable and cheap.
    """
    if req.domain not in DOMAIN_PACKS:
        raise HTTPException(404, f"unknown domain '{req.domain}'")
    set_active_domain(req.domain)

    text, source = req.regulation_text, req.regulation_source
    if req.regulation_index is not None:
        regs = get_domain(req.domain)["regulations"]
        if not 0 <= req.regulation_index < len(regs):
            raise HTTPException(400, f"regulation_index out of range (0..{len(regs) - 1})")
        r = regs[req.regulation_index]
        text, source = r["text"], f"{r['source']}: {r['title']}"
    if not text:
        raise HTTPException(400, "supply regulation_index or regulation_text")

    from agents.obligation_impact.graph import run_obligation_impact
    result = run_obligation_impact(regulation_text=text, regulation_source=source)

    return ImpactResponse(
        atomic_obligations=result.get("atomic_obligations", []),
        cross_references=result.get("cross_references", []),
        impact_scores=result.get("impact_scores", []),
        report=result.get("report", {}),
    )


# ==========================================================================================
# WF-03 — Audit Preparation  (THE FLAGSHIP)
# ==========================================================================================

class AuditRequest(BaseModel):
    domain: str = "energy_utilities"
    audit_scope: str = Field(..., description="An audit type from GET .../audit-types")
    regulations: list[str] = Field(default_factory=list, description="Regulations in scope")


class SupervisorReview(BaseModel):
    overall_readiness: str | None = None
    readiness_score: int | float | None = Field(None, description="0-100. The headline number.")
    executive_summary: str | None = None
    critical_items: list[str] = []
    strengths: list[str] = []
    weaknesses: list[str] = []
    recommendations: list[str] = []
    timeline_assessment: str | None = None


class AuditResponse(ReviewGate):
    audit_plan: dict[str, Any]
    evidence_inventory: list[dict[str, Any]]
    gap_analysis: list[dict[str, Any]] = Field(
        ..., description="THE PRODUCT. Each gap: severity, audit_risk, remediation{action,owner,"
                         "effort,deadline}, interim_mitigation")
    draft_responses: list[dict[str, Any]]
    supervisor_review: SupervisorReview


@app.post("/api/audit/run", response_model=AuditResponse, tags=["WF-03 Audit Prep (FLAGSHIP)"])
def run_audit(req: AuditRequest):
    """Supervisor plans → Evidence Collector → Gap Analyzer → Response Drafter → Supervisor reviews.

    Produces the traceable chain a regulator asks for when it says "show me":

        regulation → obligation → evidence doc → gap → owner + date → drafted response

    terminating in a 0–100 readiness score. 5 LLM calls.
    """
    if req.domain not in DOMAIN_PACKS:
        raise HTTPException(404, f"unknown domain '{req.domain}'")
    set_active_domain(req.domain)

    audit_types = get_domain(req.domain)["audit_types"]
    if req.audit_scope not in audit_types:
        raise HTTPException(400, f"unknown audit_scope. Known: {list(audit_types)}")

    from agents.audit_prep.graph import run_audit_preparation
    result = run_audit_preparation(
        audit_scope=req.audit_scope,
        regulations=req.regulations,
        obligations=audit_types[req.audit_scope],
    )

    return AuditResponse(
        audit_plan=result.get("audit_plan", {}),
        evidence_inventory=result.get("evidence_inventory", []),
        gap_analysis=result.get("gap_analysis", []),
        draft_responses=result.get("draft_responses", []),
        supervisor_review=SupervisorReview(**(result.get("supervisor_review", {}) or {})),
    )


# ==========================================================================================
# WF-04 — Case Analytics
# ==========================================================================================

class CaseRequest(BaseModel):
    domain: str = "energy_utilities"
    query: str
    analysis_type: Literal["precedent", "trend", "risk", "summary"] = "precedent"


@app.post("/api/cases/analyze", tags=["WF-04 Case Analytics"])
def analyze_cases(req: CaseRequest) -> dict[str, Any]:
    """RAG over the enforcement corpus. 1 LLM call."""
    if req.domain not in DOMAIN_PACKS:
        raise HTTPException(404, f"unknown domain '{req.domain}'")
    set_active_domain(req.domain)

    from agents.case_analytics.chain import run_case_analytics, load_sample_cases
    load_sample_cases()
    return run_case_analytics(query=req.query, analysis_type=req.analysis_type)


@app.get("/api/cases/stats", tags=["WF-04 Case Analytics"])
def case_stats(domain: str = "energy_utilities") -> dict[str, Any]:
    """Aggregate stats + penalty timeline. NO LLM CALL — the dashboard renders free."""
    if domain not in DOMAIN_PACKS:
        raise HTTPException(404, f"unknown domain '{domain}'")
    set_active_domain(domain)
    from agents.case_analytics.chain import get_case_stats
    d = get_domain(domain)
    return {"stats": get_case_stats(), "penalty_timeline": d["penalty_timeline"]}


# ==========================================================================================
# Health
# ==========================================================================================

@app.get("/api/health", tags=["ops"])
def health() -> dict[str, Any]:
    return {
        "status": "ok",
        "llm_configured": bool(os.getenv("OPENAI_API_KEY") or os.getenv("ANTHROPIC_API_KEY")),
        "domains": list(DOMAIN_PACKS),
        "data_provenance": (
            "All corpora are ILLUSTRATIVE — realistic in structure, not verified records of real "
            "regulations or enforcement actions. Replace before any client engagement."
        ),
    }
```

## `requirements.txt`

```text
# Regulatory Compliance AI - Dependencies
# Core
streamlit>=1.40.0
python-dotenv>=1.0.0

# LLM & AI
langchain>=0.3.0
langchain-core>=0.3.0
langchain-community>=0.3.0
langgraph>=0.2.0

# Primary LLM: OpenAI GPT-4o
openai>=1.40.0
langchain-openai>=0.3.0

# Fallback LLM: Claude (optional — used for high-accuracy regulatory analysis)
anthropic>=0.40.0
langchain-anthropic>=0.3.0

# Data & Visualization
plotly>=5.24.0
pandas>=2.2.0

# REST API (for the React/Topaz port — see TOPAZ_PORT.md)
fastapi>=0.115.0
uvicorn[standard]>=0.30.0
```

## `.env.example`

```bash
# Regulatory Compliance AI - Environment Variables
# Copy this file to .env and fill in your values

# Required: Anthropic API Key (Claude Sonnet & Opus)
ANTHROPIC_API_KEY=your-anthropic-api-key-here

# Optional: Voyage AI for legal-domain embeddings
# VOYAGE_API_KEY=your-voyage-api-key-here

# Optional: OpenAI for fallback embeddings
# OPENAI_API_KEY=your-openai-api-key-here

# Optional: Ollama for local LLM (default: localhost)
# OLLAMA_BASE_URL=http://localhost:11434

# Database path (default: ./data/pge_compliance.db)
# DATABASE_PATH=./data/pge_compliance.db

# ChromaDB persistence (default: ./data/chroma_db)
# CHROMA_PERSIST_DIR=./data/chroma_db
```

## `BLUEPRINT.md`

```markdown
# Regulatory Compliance AI — Solution Blueprint

> Complete architectural, functional and commercial description of the **PG&E Regulatory Compliance
> AI Platform**, structured for import into **Infosys Topaz Fabric** as an agentic solution asset.
>
> Repository: `https://github.com/ajittgosavii/legalncompliance` · commit `1021968` · 2026-07-12
>
> **Status:** working prototype. Agent graphs, provenance verification, human-review gate and four
> industry packs are implemented and render-tested. Live regulator ingestion, real embeddings and
> persistence are **not** built — see §12. Do not present this as a system that monitors anything
> today; it is a working prototype of the target architecture.

---

## 1. Solution Metadata

```yaml
solution:
  id: regulatory-compliance-ai
  name: Regulatory Compliance AI Platform
  tagline: From reacting to regulatory change, to getting ahead of it.
  version: 0.2.0
  anchor_client: Pacific Gas and Electric Company (PG&E)
  domain: Legal, Risk & Compliance (LRC) — Regulatory Change Management, Audit Readiness
  primary_industry: Energy & Utilities (electric + gas)
  pattern: Multi-agent orchestration (LangGraph) + RAG + programmatic provenance verification
  interface: Streamlit multipage (5 pages)
  language: Python 3.11+
  loc: ~5,400
  data_classification: synthetic / illustrative only — no real client data, no PII

capabilities:
  agents: 7                  # 7 specialised personas, 4 workflows
  workflows: 4               # 3 agentic (LangGraph) + 1 generative (RAG)
  industry_packs: 4          # Energy & Utilities (PG&E) · Retail · Resources · Services
  regulators: 9              # CPUC · OEIS · FERC · NERC · CARB · EPA · PHMSA · Cal-OSHA · CEC
  guardrails: 3              # provenance verification · human-review gate · fail-loud parsing

deployment:
  target: Streamlit Cloud
  entrypoint: app.py
  secrets: OPENAI_API_KEY (required) · ANTHROPIC_API_KEY (optional — automatic failover)
```

### One-line description

An agentic AI platform that watches the regulators PG&E answers to, decomposes each new rule into
atomic, testable obligations **with a machine-verified citation back to the source text**, scores
their business impact, assembles audit-ready evidence packages with gap analysis and named
remediation owners, and mines enforcement history for precedent.

---

## 2. The Problem — and why it is a PG&E problem specifically

PG&E must track a continuous stream of rulemakings, orders, resolutions and emergency regulations
across **nine** federal and state bodies. Today this is manual: analysts read hundreds of pages of
dense legal prose, hand-extract obligations into spreadsheets, chase document owners for audit
evidence, and rely on institutional memory for enforcement precedent.

The result is late detection, missed deadlines, **evidence gaps discovered *during* an audit rather
than before it**, and avoidable exposure.

### Why PG&E is the natural anchor client

PG&E's distinguishing condition is not that it has more rules than its peers. It is that it operates
under **sustained, intense regulatory scrutiny**, with a documented enforcement history. So the
expensive recurring work is not *knowing* the rule — it is **proving compliance on demand**, and the
costly failure mode is an evidence gap found by an auditor rather than by PG&E.

> **The commercial insight that makes this a business case rather than a productivity tool:**
> under California's post-2019 wildfire framework (AB 1054), demonstrated Wildfire Mitigation Plan
> compliance and the annual **Safety Certification** affect the presumption applied in cost-recovery
> proceedings. Separately, the CPUC can **disallow** claimed costs where compliance or process cannot
> be evidenced.
>
> **The ability to evidence compliance on demand is therefore an input to cost recovery — not
> administrative overhead.** An evidence gap is financial risk, not merely audit risk.

⚠️ **Verify before quoting.** The precise legal mechanics of AB 1054's presumption must be confirmed
with qualified counsel before any dollar figure is attached to this chain. What is defensible is the
*mechanism*; what is **not** yet defensible is a specific quantified saving. See §11.

---

## 3. The Regulatory Perimeter

| Code | Body | Scope |
|------|------|-------|
| **CPUC** | California Public Utilities Commission | State economic + safety regulator. Its Safety and Enforcement Division (SED) audits and enforces |
| **OEIS** | Office of Energy Infrastructure Safety | **State wildfire-safety regulator. WMPs are filed with, and approved by, OEIS — NOT the CPUC.** OEIS issues the annual Safety Certification; the CPUC ratifies |
| FERC | Federal Energy Regulatory Commission | Interstate transmission, planning, wholesale rates |
| NERC | North American Electric Reliability Corp. (WECC region) | Grid reliability and OT cybersecurity (NERC CIP) |
| CARB | California Air Resources Board | Emissions, cap-and-trade |
| EPA | Environmental Protection Agency | Federal environmental compliance |
| PHMSA | Pipeline & Hazardous Materials Safety Admin. | Federal pipeline safety (CPUC is the state agent) |
| Cal-OSHA | CA Div. of Occupational Safety and Health | Worker safety |
| CEC | California Energy Commission | Energy policy, load forecasting |

> ### A defect we found and fixed — and why it matters more than it looks
>
> The original codebase routed **Wildfire Mitigation Plans to the CPUC**, and did not list OEIS as a
> regulator at all. Since 2021 WMPs go to **OEIS**.
>
> Getting this wrong in front of PG&E's regulatory affairs team — on the single topic they care most
> about — would have ended the credibility conversation before the demo started. The system prompt
> now carries an explicit instruction: *"Never state that a WMP is filed with or approved by the
> CPUC."*
>
> **This is the kind of error a generic RegTech tool makes and a domain-grounded one does not.**

---

## 4. Architecture

```
┌────────────────────────── STREAMLIT UI (5 pages) ──────────────────────────┐
│  Dashboard │ Regulatory Monitor │ Obligation Impact │ Audit Prep │ Cases    │
└──────────┬─────────┬─────────────────┬──────────────────┬──────────┬───────┘
           │         │                 │                  │          │
┌──────────▼─────────▼─────────────────▼──────────────────▼──────────▼───────┐
│                        LangGraph Orchestration                              │
│  WF-01 Monitor      WF-02 Impact       WF-03 Audit Prep      WF-04 Cases    │
│  5-node pipeline    4-node graph       Supervisor + 3        RAG chain      │
└────────────────────────────────┬───────────────────────────────────────────┘
                                 │
┌────────────────────────────────▼───────────────────────────────────────────┐
│  core/provenance  ← THE GATE. Every obligation must quote the regulation    │
│                     verbatim, and the system VERIFIES the quote exists.     │
│                     CODE, not a prompt. Unverifiable → flagged, downgraded. │
│  core/domains.py  ← Industry packs. The agents contain NO industry logic.   │
│  core/prompts.py  ← 7 agent personas, composed from the active pack         │
│  core/llm.py      ← GPT-4o primary → automatic failover → Claude Sonnet     │
│  core/db.py       ← SQLite (PostgreSQL-ready): obligations, gaps, agent_runs│
└────────────────────────────────┬───────────────────────────────────────────┘
                                 │
                                 ▼
                   HUMAN REVIEWER SIGNS OFF
        (PENDING_HUMAN_REVIEW — the platform determines nothing)
```

### Repository map

| Path | Role |
|------|------|
| `app.py` | Dashboard, KPIs (computed, not hard-coded), industry switcher, honest-limits tab |
| `pages/1_Regulatory_Monitor.py` | WF-01 UI — alerts + **citation badges** on every obligation |
| `pages/2_Obligation_Impact.py` | WF-02 UI — executive impact report |
| `pages/3_Audit_Prep.py` | WF-03 UI — **the flagship**: readiness score, gaps, drafted responses |
| `pages/4_Case_Analytics.py` | WF-04 UI — precedent search, penalty trends, case browser |
| `agents/regulatory_monitor/graph.py` | 5-node LangGraph + **`_quote_in_source()` provenance verifier** |
| `agents/obligation_impact/graph.py` | 4-node impact graph |
| `agents/audit_prep/graph.py` | Supervisor + 3 specialists (**plan-discard bug fixed**) |
| `agents/case_analytics/chain.py` | RAG chain over the enforcement corpus |
| `core/domains.py` | **Industry packs** — the single point of domain grounding |
| `core/prompts.py` | 7 agent personas, composed at call time from the active pack |
| `core/ui.py` | Industry switcher, review gate, citation badges, credential resolution |

---

## 5. Agent Registry

Seven personas. All prompts are composed as `build_system_context(active_pack) + role_instructions`,
so **the pack is the single lever that re-targets every agent.**

| ID | Agent | Workflow | Responsibility |
|----|-------|----------|----------------|
| AG-01 | **Regulatory Monitor** | WF-01 | Classify change type + severity; extract obligations **with verified provenance**; map to departments |
| AG-02 | **Obligation Impact** | WF-02 | Decompose into atomic obligations; cross-reference the existing estate for conflicts; score 4 impact dimensions; write the executive report |
| AG-03 | **Audit Supervisor** | WF-03 | Plan the audit approach; then **review the specialists against the plan it set**; issue a 0–100 readiness score |
| AG-04 | **Evidence Collector** | WF-03 | Map evidence to each obligation; rate relevance + sufficiency; flag stale documents |
| AG-05 | **Gap Analyzer** | WF-03 | Type and rank each gap; assign remediation owner, effort, deadline |
| AG-06 | **Response Drafter** | WF-03 | Draft submission-grade regulatory responses with evidence citations |
| AG-07 | **Case Analytics** | WF-04 | RAG over enforcement precedent — precedent / trend / risk / summary |

---

## 6. Workflows

### WF-01 — Regulatory Change Monitor (5-node LangGraph)

```
fetch → classify → extract → map → notify → END
```

| Node | Type | LLM calls |
|------|------|-----------|
| `fetch` | Deterministic — load regulations, filter by regulator | 0 |
| `classify` | Change type, severity, summary, deadlines, penalties | **1 per regulation** |
| `extract` | Atomic obligations **+ verbatim source quote + verification** | **1 per regulation** |
| `map` | Batched — map every obligation to departments, effort, capex, timeline risk | 1 |
| `notify` | Deterministic — join and severity-sort into alerts | 0 |

**Cost profile: `2N + 1` LLM calls** for N regulations. This is the dominant cost driver and the
first target for optimisation (model tiering on `classify`, batching, incremental processing).

### WF-02 — Obligation Impact Analysis (4-node LangGraph)

```
decompose → cross_ref → score → report → END
```

Scores each obligation on **four dimensions**, each with a score, a quantified range and a rationale:
**cost** (1–10, $ range, capex/opex) · **operational** (affected processes, workforce) ·
**timeline risk** (feasibility, critical path) · **penalty risk** (max penalty, enforcement
likelihood). Exactly 4 LLM calls — predictable and cheap.

### WF-03 — Audit Analysis & Preparation (Supervisor pattern) — **THE FLAGSHIP**

```
plan (Supervisor) → collect_evidence → analyze_gaps → draft_responses → supervisor_review → END
```

Produces a **traceable chain**:

> **regulation → obligation → evidence document → gap → remediation owner & date → drafted response**

terminating in a **0–100 readiness score** for the audit committee. That chain is the artefact a
utility needs when a regulator says *"show me."*

> **Defect fixed:** `plan_audit()` previously called the LLM and **discarded the response**. The plan
> never reached the specialists — the supervisor did not actually supervise. The plan is now threaded
> into all three specialists, and the final review explicitly checks them against it.

### WF-04 — Case Analytics (RAG)

Retrieval over the enforcement corpus → precedent / trend / risk / summary analysis. Also renders an
interactive dashboard with **no LLM call at all** — the recommended zero-cost entry point for a demo.

---

## 7. The Trust Architecture — why this is safe to put in front of a regulated utility

### 7.1 Provenance is a CODE check, not a prompt

Every extracted obligation must carry a **verbatim quote** from the source regulation. The system then
**programmatically verifies the quote exists** in the source text (`_quote_in_source()`).

- Exact match (whitespace/case-normalised) → **verified**
- Elision tolerated (a substantial leading span matches) → **verified**
- Otherwise → **`citation_verified: false`**, confidence force-downgraded to `low`, and the UI shows
  **⚠ Quote not found in source — verify manually**

**The model cannot talk its way past this, because it is code.**

> An invented deadline entering a compliance register is a **material harm**, not a rounding error.
> So the platform does not ask the model to be honest — **it checks.**

The UI reports `Citations Verified: n/m` on every run and raises a warning banner if any obligation
could not be traced.

### 7.2 Human review is a gate, not a suggestion

Module 3 drafts text explicitly described as *"suitable for regulatory submission."* Every audit
package is stamped **`PENDING_HUMAN_REVIEW`**. The platform **prepares** the package. It never files
it. Nothing reaches a regulator without qualified sign-off.

### 7.3 The agents are instructed not to guess

Where the source text does not state a deadline or a penalty, agents must write
**"not stated in source"** rather than estimate — and must label an inference as an inference.

### 7.4 Fail loud

A JSON parse failure surfaces as an explicit unreliable-review finding. In a compliance system,
silence reads as *"nothing wrong here"* — the most dangerous possible failure mode.

---

## 8. Industry Packs — the reuse thesis

The four agent graphs contain **no industry-specific logic**. Everything that makes this "a utility
compliance tool" lives in `core/domains.py`: the regulators, the departments obligations route to,
the existing-obligation register used for conflict detection, the enterprise profile used for impact
scoring, and the corpora.

| Pack | Regulators | Corpora | Financial hook |
|------|-----------|---------|----------------|
| **Energy & Utilities (PG&E)** | 9 | 11 regs · 29 cases · 48 evidence docs · 7 audit types | AB 1054 — evidence quality feeds the cost-recovery presumption |
| Retail | 8 (FTC, FDA, CPSC, CPPA, PCI…) | 3 regs · 6 cases · 22 evidence docs | A traceability gap turns a 3-SKU recall into a 47-SKU recall |
| Resources | 7 (EPA, OSHA PSM, PHMSA…) | 3 regs · 5 cases · 18 evidence docs | The tail risk is the consent decree, not the penalty |
| Services | 7 (SEC, DORA, EU AI Act…) | 3 regs · 5 cases · 20 evidence docs | One control gap breaches dozens of client contracts at once |

**Switch the pack → all 7 agents re-target. No agent code changes.**

> ⚠️ **Do not lead with breadth.** Depth at PG&E is the pitch. The other three packs prove the
> architecture is domain-agnostic — they are the *second act*, not the headline. Verified: 4/4 packs
> build 7/7 agent prompts; all 5 pages render across every pack.

---

## 9. Data Assets

Ground-truth counts, measured from source (the original UI claimed 12 / 28 / $19.8B — **now computed
from the actual data, not hard-coded**):

| Asset | Count |
|-------|-------|
| Regulatory updates (Energy pack) | **11** — OEIS 1, CPUC 3, FERC 2, NERC 1, CARB 1, EPA 1, PHMSA 1, Cal-OSHA 1 |
| Enforcement cases | **29** — CPUC 15, NERC/FERC 4, CARB 3, Cal-OSHA 3, PHMSA 2, FERC 1, CEC 1 |
| Total penalty value in corpus | **$17.47B** |
| Audit evidence documents | **48** across 8 categories |
| Audit types | **7** |

Evidence documents carry a `status` of `current / draft / partial / needs_update` — the stale ones are
the seeded gaps the Gap Analyzer is meant to find.

> **DATA PROVENANCE: all corpora are ILLUSTRATIVE.** Realistic in structure and vocabulary; not
> verified records of real regulations or real enforcement actions. The app says so on screen. Before
> a PG&E conversation, **the case corpus must be replaced with the real public enforcement record** —
> PG&E will recognise its own history instantly, and precedent analysis on invented cases is worthless.

---

## 10. Prototype → Production Gap (honest)

**This is the most important section for a Topaz Fabric import.** The solution is a well-architected
demo, not a production system.

| # | Gap | Required for production | Effort |
|---|-----|------------------------|--------|
| G1 | **No live ingestion.** `ingestion/scrapers/` and `ingestion/parsers/` are **empty stub packages**. All regulations are hard-coded Python dicts. | Real connectors to CPUC/OEIS/FERC publication feeds; PDF+HTML parsing; change detection and de-duplication. **The single biggest work item.** | **L** |
| G2 | **No real semantic retrieval.** TF-IDF keyword overlap, not embeddings. | Managed vector store + legal-domain embeddings (`voyage-law-2`). The seam already exists in `core/embeddings.py`. | S |
| G3 | **Nothing persists.** Every run is ephemeral in session state. | Wire `core/db.py`; SQLite → PostgreSQL; obligations/gaps with lifecycle status. | M |
| G4 | **No observability.** `agent_runs` has `tokens_used`, `cost_estimate` and `trace_json` columns — **and nothing writes to them.** | Wire `log_agent_run()`. Cheapest high-value win available. | S |
| G5 | **No span-level provenance.** Citation is verified, but not anchored to a character offset in a source PDF. | Required for legal defensibility. | M |
| G6 | **No structured-output enforcement.** JSON is prompt-instructed and brace-sliced. | Tool-calling with schema validation + retry. | S |
| G7 | **No evaluation harness.** No golden set; extraction accuracy is unmeasured. | Precision/recall on obligation extraction against a human-extracted golden set. **Until this exists, every quality claim is anecdote.** | M |
| G8 | **No SSO/RBAC, no access-scoped retrieval.** An agent can see all evidence. | Enterprise table stakes. | M |

*S = 1–3 weeks · M = 3–8 weeks · L = 8–16 weeks (elapsed, for the stated team)*

---

## 11. Commercial Model

### The value chain, in the right order

**Lead with audit readiness, not with monitoring.** Regulatory change monitoring is the *least*
differentiated capability — PG&E's regulatory affairs function already tracks CPUC dockets closely,
and commercial RegTech feeds exist. The differentiation is downstream: **obligation decomposition,
impact scoring, and the evidence → gap → response chain.**

| Driver | Why it lands at PG&E | How to prove it |
|--------|---------------------|-----------------|
| **1. Audit readiness / evidence-gap elimination** | The binding constraint is *proving* compliance under scrutiny. The costly failure is a gap found by an auditor. | Run Module 3 against one real upcoming audit. **Any gap it finds that the team did not have is the entire business case.** |
| **2. Obligation decomposition** | One CPUC decision contains a dozen separately-testable duties, extracted by hand today. | Precision/recall against a human-extracted golden set for 5–10 real decisions. |
| **3. Cross-obligation conflict detection** | New OEIS/CPUC requirements routinely collide with GO 95/165 and existing WMP commitments. | Highest ceiling; needs the real obligation register loaded. |
| **4. Enforcement precedent** | Penalty conversations currently rest on institutional memory. | Load the real public case record. |

### ⚠️ What we deliberately do NOT claim

It is tempting to anchor the business case to PG&E's headline penalty history. **Do not.** Those
penalties arose overwhelmingly from **operational** failures — pipeline integrity, vegetation
management, equipment maintenance. **This platform does not prevent a wildfire.** Claiming a share of
a multi-billion-dollar penalty would be dishonest, and a PG&E audience would see through it
immediately.

The defensible exposure argument is narrow and specific: **findings and cost disallowances that
turned on inadequate documentation, missing evidence, or unprovable process.** A smaller number — and
one PG&E's own Regulatory Affairs team can help size, which is what makes it credible.

### Run cost — computed, not assumed

WF-01 costs `2N+1` LLM calls. A full 11-regulation monitoring run is **well under $1**. An audit-prep
run is ~5 calls, roughly **$0.20**. At enterprise volume, annual inference cost lands in the **low
thousands**.

> **Inference cost is NOT the constraint.** The cost is engineering, integration and change
> management. Anyone presenting token cost as the main expense line has not understood the problem.

### Indicative engagement (ILLUSTRATIVE — must be validated)

| Stage | Duration | Indicative revenue |
|-------|----------|-------------------|
| Qualify & discovery | 2–4 weeks | $100k – 200k |
| Single-audit pilot | 6–8 weeks | $300k – 600k |
| Production build (ingestion, provenance, review workflow, persistence) | 6–9 months | $1.2M – 2.5M |
| Managed run | annual | $300k – 800k ARR |

**Time to production MVP: ~7–9 months, ~28 FTE-months.** Each additional industry pack: **~2.5
FTE-months** — that reuse ratio is the strongest commercial argument in this document.

---

## 12. Verification Status

### ✅ Verified by test
- All files parse; **4/4 industry packs build 7/7 agent prompts**
- **All 5 pages render across every pack**
- Provenance verifier is wired into WF-01 and reports `citation_verified` per obligation
- Supervisor plan is threaded into all three specialists (the discard bug is closed)
- KPI counts are computed from the data, not hard-coded

### ⚠️ NOT verified
- **Agent output quality is unmeasured.** There is no golden set and no evaluation harness (G7).
  Until one exists, every claim about extraction accuracy is an anecdote.
- **The provenance verifier's *hit rate* against real LLM output is unknown.** The mechanism is
  unit-testable; how often GPT-4o actually quotes verbatim rather than paraphrasing is not yet
  measured. If it paraphrases, obligations will correctly show as UNVERIFIED — the system stays
  honest, but the review *looks* weak. That is a prompt-tuning problem, and the `Citations Verified`
  metric on screen will reveal it immediately.

---

## 13. Recommended Engagement Shape

**Do not pitch a platform. Pitch one narrow, falsifiable proof.**

1. **Qualify (weeks 0–2)** — discovery with Regulatory Affairs, Internal Audit and Compliance. Size
   the value with PG&E's own numbers. Identify **one upcoming audit or data request** to target.
2. **Prove (weeks 2–8)** — a single-audit pilot. Load the **real** obligations and the **real**
   evidence inventory for that audit's scope. Run Module 3.
   > **Success is binary: did it surface a real evidence gap the team did not already know about?**
   > Everything else is secondary. **The test is designed so it can fail** — and if it does, we say so.
3. **Expand (post-pilot)** — only if the pilot clears that bar: live ingestion for CPUC + OEIS,
   span-level provenance, the review workflow, persistence.

---

## 14. Topaz Fabric Import Summary

```yaml
asset_type: agentic_solution
agents: 7
workflows: 4                # 3 LangGraph state machines + 1 RAG chain
industry_packs: 4           # Energy & Utilities (PG&E) · Retail · Resources · Services
regulators: 9               # incl. OEIS — the fix that earns credibility with PG&E
guardrails:
  - programmatic citation verification (CODE, not a prompt) — flags unverifiable obligations
  - mandatory human-review gate (PENDING_HUMAN_REVIEW)
  - fail-loud parsing (no silent empty results in a compliance system)
models: GPT-4o primary, Claude Sonnet automatic failover, 4 tiers available
pii: none — all corpora synthetic
production_readiness: prototype — 8 architectural gaps (§10); no live ingestion
```

### The reusable IP

1. **The obligation-extraction contract** — a schema for turning dense legal prose into atomic,
   assignable, testable, measurable obligations. **The heart of the asset.**
2. **Programmatic provenance verification** — the code that proves a model's citation is real and
   flags it when it is not. **The most transferable component in the portfolio**: it is what makes
   *any* LLM safe to deploy in a domain where a confident wrong answer causes harm.
3. **The four-dimension impact scoring model** — cost / operational / timeline / penalty risk, each
   with a score, a quantified range and a rationale.
4. **The supervisor audit chain** — regulation → obligation → evidence → gap → response, terminating
   in a 0–100 readiness score.
5. **The swappable industry pack** — domain content fully separated from agent logic.

Everything else — the regulators, the departments, the corpora — is a **pack** to be replaced per
client.
```

## `TOPAZ_PORT.md`

```markdown
# Porting to Infosys Topaz Fabric (React)

> **Read this before BLUEPRINT.md if your job is to rebuild the UI.**
>
> BLUEPRINT.md tells you *what the system is*. This tells you *how to move it to React*, and — more
> importantly — **what BLUEPRINT.md alone would NOT have told you.**

---

## The honest answer to "can I rebuild this from the blueprint?"

**No — and not because the blueprint is thin.** Because of a structural fact about the current app:

> ### Streamlit has no API layer.
>
> The page scripts call the agent functions **directly, in-process**. There is no REST contract, no
> request/response schema, no serialisation boundary — because nothing ever needed one.

You cannot build a React frontend against a Python function call. So this is **not a UI rewrite. It
is an architectural split.**

| Today (Streamlit) | On Topaz (React) |
|---|---|
| `pages/1_Regulatory_Monitor.py` calls `run_regulatory_monitor()` in-process | React component → `POST /api/monitor/run` → FastAPI → **the same Python function** |
| Agent output rendered inline with `st.markdown` | Agent output returned as JSON, rendered by React components |
| No API, no schemas, no auth, no async | REST API with typed contracts |

**That seam is now built.** See `api.py`.

---

## What transfers UNCHANGED — do not rewrite any of it

This is ~70% of the value of the asset, and **not one line of it needs to change**:

| Keep as-is | Why |
|---|---|
| `agents/regulatory_monitor/graph.py` | 5-node LangGraph + **the provenance verifier** |
| `agents/obligation_impact/graph.py` | 4-node impact graph |
| `agents/audit_prep/graph.py` | Supervisor + 3 specialists |
| `agents/case_analytics/chain.py` | RAG chain |
| `core/prompts.py` | 7 agent personas |
| `core/domains.py` | **The 4 industry packs — the single lever that re-targets all 7 agents** |
| `core/llm.py` | GPT-4o → automatic failover → Claude Sonnet |
| `core/vectorstore.py`, `core/db.py` | Retrieval, persistence schema |

**Only the UI is thrown away.** `app.py`, `pages/*`, `core/styles.py`, `core/ui.py`.

---

## What you build

### 1. Backend — **already written: `api.py`**

```bash
pip install fastapi uvicorn
uvicorn api:app --reload --port 8000
```

- Interactive docs: `http://localhost:8000/docs`
- **Machine-readable contract: `http://localhost:8000/openapi.json`** (also committed at
  `docs/openapi.json`)

> **Hand the React team `openapi.json`.** They can generate a fully typed TypeScript client from it
> with `openapi-typescript` or `orval`. That is worth more than any amount of prose in a blueprint,
> because it cannot drift from the truth — it is generated from the code.

### 2. Frontend — React components, one per Streamlit page

| Streamlit page | React route | Calls |
|---|---|---|
| `app.py` (Dashboard) | `/` | `GET /api/domains` |
| `pages/1_Regulatory_Monitor.py` | `/monitor` | `POST /api/monitor/run` |
| `pages/2_Obligation_Impact.py` | `/impact` | `GET /api/domains/{d}/regulations` → `POST /api/impact/run` |
| `pages/3_Audit_Prep.py` | `/audit` | `GET /api/domains/{d}/audit-types` → `POST /api/audit/run` |
| `pages/4_Case_Analytics.py` | `/cases` | `GET /api/cases/stats` (no LLM) → `POST /api/cases/analyze` |

---

## The API contract

| Method | Endpoint | Purpose |
|---|---|---|
| `GET` | `/api/domains` | All 4 industry packs — regulators, departments, counts. Drives every selector |
| `GET` | `/api/domains/{d}/regulations` | Regulation list + full text |
| `GET` | `/api/domains/{d}/audit-types` | Audit type → the obligations it tests |
| `GET` | `/api/domains/{d}/cases` | Enforcement corpus |
| `POST` | `/api/monitor/run` | **WF-01** — alerts + obligations + **provenance summary** |
| `POST` | `/api/impact/run` | **WF-02** — atomic obligations, conflicts, 4-dimension scores, exec report |
| `POST` | `/api/audit/run` | **WF-03 (flagship)** — evidence, **gaps**, draft responses, 0–100 readiness score |
| `POST` | `/api/cases/analyze` | **WF-04** — RAG precedent/trend/risk analysis |
| `GET` | `/api/cases/stats` | Aggregates + penalty timeline. **No LLM call — the dashboard renders free** |
| `GET` | `/api/health` | Readiness + LLM configured |

---

## THE TWO THINGS THE REACT UI MUST GET RIGHT

Everything else is layout. These two are the product.

### 1. Render `citation_verified` — and never flatten it

Every `Obligation` carries:

```ts
{
  source_quote: string        // the VERBATIM span the model copied from the regulation
  source_section: string
  confidence: "high" | "medium" | "low"
  citation_verified: boolean  // <-- THE ONE THAT MATTERS
}
```

`citation_verified` is set by **`_quote_in_source()`** — code, not a prompt. It is `true` only if the
model's quote was actually **found in the source regulation**.

> **A `false` here means the model may have paraphrased or fabricated the obligation.**
>
> The React UI **must** show it with a warning badge, must surface the `Provenance` summary
> (`verified / total`) on the results header, and **must not** let a `false` obligation look the same
> as a `true` one.
>
> If you render them identically, you have thrown away the single mechanism that makes this system
> safe to put in front of a regulated utility. An invented deadline in a compliance register is a
> material harm, not a rounding error.

Suggested treatment:

| `citation_verified` | UI |
|---|---|
| `true` | ✅ green badge — *"Verified against {source_regulation}"* + show `source_quote` as a blockquote |
| `false` | ⚠️ amber badge — *"Quote not found in source — verify manually"*, and force `confidence: low` |

### 2. The human-review gate is not decorative

Every response carries `review_status: "PENDING_HUMAN_REVIEW"` and a `disclaimer`. **Render both.**
Module 3 drafts text explicitly described as *"suitable for regulatory submission"* — the UI must
make it impossible to mistake a draft for a filing.

---

## Gaps you must close before production — and `api.py` will not hide them from you

| # | Gap | Why it matters |
|---|---|---|
| 1 | **WF-01 is `2N + 1` LLM calls** and takes minutes. `POST /api/monitor/run` is **synchronous** — it will time out behind any real gateway. | Make it a **background job** with polling or SSE. The endpoint docstring says so. |
| 2 | **No auth.** | Topaz SSO / RBAC. |
| 3 | **No persistence.** Every run is ephemeral. | `core/db.py` has the schema (`obligations`, `audit_items`, `agent_runs`) and **nothing writes to it**. |
| 4 | **No observability.** `agent_runs` has `tokens_used`, `cost_estimate`, `trace_json` columns — all unwritten. | The cheapest high-value win available. |
| 5 | **CORS is wide open** to localhost dev origins. | Lock down before deploy. |
| 6 | **No live ingestion.** `ingestion/scrapers/` and `ingestion/parsers/` are **empty stub packages**. Regulations are fixture data. | The biggest work item in the whole programme. **Do not let anyone believe ingestion exists because the folders do.** |

---

## Effort for the port specifically

| Task | Effort |
|---|---|
| Backend API (`api.py`) | **DONE** |
| Async job queue for WF-01 (Celery/RQ + polling or SSE) | ~1 week |
| React: 5 routes + typed client generated from `openapi.json` | ~2–3 weeks |
| Provenance badges, review gate, readiness gauge, charts | ~1 week |
| Auth / SSO wiring into Topaz | ~1 week |
| **Total port to a working React app on Topaz** | **~5–6 weeks, 2 engineers** |

This is **the port only**. It does not include live ingestion, persistence, or the evaluation
harness — see BLUEPRINT.md §10 for the full production gap.

---

## Quick start

```bash
git clone https://github.com/ajittgosavii/legalncompliance
cd legalncompliance
pip install -r requirements.txt fastapi uvicorn
cp .env.example .env          # add OPENAI_API_KEY

uvicorn api:app --reload --port 8000
open http://localhost:8000/docs
```

Then, in the React project:

```bash
npx openapi-typescript http://localhost:8000/openapi.json -o src/api/types.ts
```

You now have a fully typed client against a contract generated from the real code — which cannot
drift from it.
```

## `docs/openapi.json`

```json
{
  "openapi": "3.1.0",
  "info": {
    "title": "Regulatory Compliance AI",
    "description": "Seven agents turn dense regulation into testable obligations \u2014 each with a citation verified in CODE against the source text \u2014 score their impact, and assemble audit-ready evidence packages. A human always signs off; this API determines nothing.",
    "version": "0.2.0"
  },
  "paths": {
    "/api/domains": {
      "get": {
        "tags": [
          "domains"
        ],
        "summary": "List Domains",
        "description": "All industry packs. Switching the pack re-targets all 7 agents \u2014 no agent code changes.",
        "operationId": "list_domains_api_domains_get",
        "responses": {
          "200": {
            "description": "Successful Response",
            "content": {
              "application/json": {
                "schema": {
                  "items": {
                    "$ref": "#/components/schemas/DomainSummary"
                  },
                  "type": "array",
                  "title": "Response List Domains Api Domains Get"
                }
              }
            }
          }
        }
      }
    },
    "/api/domains/{domain}/regulations": {
      "get": {
        "tags": [
          "domains"
        ],
        "summary": "List Regulations",
        "operationId": "list_regulations_api_domains__domain__regulations_get",
        "parameters": [
          {
            "name": "domain",
            "in": "path",
            "required": true,
            "schema": {
              "type": "string",
              "title": "Domain"
            }
          }
        ],
        "responses": {
          "200": {
            "description": "Successful Response",
            "content": {
              "application/json": {
                "schema": {
                  "type": "array",
                  "items": {
                    "$ref": "#/components/schemas/RegulationSummary"
                  },
                  "title": "Response List Regulations Api Domains  Domain  Regulations Get"
                }
              }
            }
          },
          "422": {
            "description": "Validation Error",
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/HTTPValidationError"
                }
              }
            }
          }
        }
      }
    },
    "/api/domains/{domain}/audit-types": {
      "get": {
        "tags": [
          "domains"
        ],
        "summary": "List Audit Types",
        "description": "Audit type -> the obligations that audit tests. Drives the Audit Prep screen.",
        "operationId": "list_audit_types_api_domains__domain__audit_types_get",
        "parameters": [
          {
            "name": "domain",
            "in": "path",
            "required": true,
            "schema": {
              "type": "string",
              "title": "Domain"
            }
          }
        ],
        "responses": {
          "200": {
            "description": "Successful Response",
            "content": {
              "application/json": {
                "schema": {
                  "type": "object",
                  "additionalProperties": {
                    "type": "array",
                    "items": {
                      "type": "object",
                      "additionalProperties": true
                    }
                  },
                  "title": "Response List Audit Types Api Domains  Domain  Audit Types Get"
                }
              }
            }
          },
          "422": {
            "description": "Validation Error",
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/HTTPValidationError"
                }
              }
            }
          }
        }
      }
    },
    "/api/domains/{domain}/cases": {
      "get": {
        "tags": [
          "domains"
        ],
        "summary": "List Cases",
        "operationId": "list_cases_api_domains__domain__cases_get",
        "parameters": [
          {
            "name": "domain",
            "in": "path",
            "required": true,
            "schema": {
              "type": "string",
              "title": "Domain"
            }
          }
        ],
        "responses": {
          "200": {
            "description": "Successful Response",
            "content": {
              "application/json": {
                "schema": {
                  "type": "array",
                  "items": {
                    "type": "object",
                    "additionalProperties": true
                  },
                  "title": "Response List Cases Api Domains  Domain  Cases Get"
                }
              }
            }
          },
          "422": {
            "description": "Validation Error",
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/HTTPValidationError"
                }
              }
            }
          }
        }
      }
    },
    "/api/monitor/run": {
      "post": {
        "tags": [
          "WF-01 Regulatory Monitor"
        ],
        "summary": "Run Monitor",
        "description": "Fetch \u2192 Classify \u2192 Extract (+VERIFY CITATION) \u2192 Map to departments \u2192 Alert.\n\n\u26a0\ufe0f COST + LATENCY: this is `2N + 1` LLM calls for N regulations. For the full Energy pack that\nis 23 calls and takes minutes. **In production this MUST be a background job** with polling or\nSSE \u2014 a blocking POST will time out behind any real gateway. It is synchronous here so the\ncontract is legible; do not ship it this way.",
        "operationId": "run_monitor_api_monitor_run_post",
        "requestBody": {
          "content": {
            "application/json": {
              "schema": {
                "$ref": "#/components/schemas/MonitorRequest"
              }
            }
          },
          "required": true
        },
        "responses": {
          "200": {
            "description": "Successful Response",
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/MonitorResponse"
                }
              }
            }
          },
          "422": {
            "description": "Validation Error",
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/HTTPValidationError"
                }
              }
            }
          }
        }
      }
    },
    "/api/impact/run": {
      "post": {
        "tags": [
          "WF-02 Obligation Impact"
        ],
        "summary": "Run Impact",
        "description": "Decompose \u2192 Cross-reference \u2192 Score (cost/ops/timeline/penalty) \u2192 Executive report.\n\nExactly 4 LLM calls. Predictable and cheap.",
        "operationId": "run_impact_api_impact_run_post",
        "requestBody": {
          "content": {
            "application/json": {
              "schema": {
                "$ref": "#/components/schemas/ImpactRequest"
              }
            }
          },
          "required": true
        },
        "responses": {
          "200": {
            "description": "Successful Response",
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/ImpactResponse"
                }
              }
            }
          },
          "422": {
            "description": "Validation Error",
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/HTTPValidationError"
                }
              }
            }
          }
        }
      }
    },
    "/api/audit/run": {
      "post": {
        "tags": [
          "WF-03 Audit Prep (FLAGSHIP)"
        ],
        "summary": "Run Audit",
        "description": "Supervisor plans \u2192 Evidence Collector \u2192 Gap Analyzer \u2192 Response Drafter \u2192 Supervisor reviews.\n\nProduces the traceable chain a regulator asks for when it says \"show me\":\n\n    regulation \u2192 obligation \u2192 evidence doc \u2192 gap \u2192 owner + date \u2192 drafted response\n\nterminating in a 0\u2013100 readiness score. 5 LLM calls.",
        "operationId": "run_audit_api_audit_run_post",
        "requestBody": {
          "content": {
            "application/json": {
              "schema": {
                "$ref": "#/components/schemas/AuditRequest"
              }
            }
          },
          "required": true
        },
        "responses": {
          "200": {
            "description": "Successful Response",
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/AuditResponse"
                }
              }
            }
          },
          "422": {
            "description": "Validation Error",
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/HTTPValidationError"
                }
              }
            }
          }
        }
      }
    },
    "/api/cases/analyze": {
      "post": {
        "tags": [
          "WF-04 Case Analytics"
        ],
        "summary": "Analyze Cases",
        "description": "RAG over the enforcement corpus. 1 LLM call.",
        "operationId": "analyze_cases_api_cases_analyze_post",
        "requestBody": {
          "content": {
            "application/json": {
              "schema": {
                "$ref": "#/components/schemas/CaseRequest"
              }
            }
          },
          "required": true
        },
        "responses": {
          "200": {
            "description": "Successful Response",
            "content": {
              "application/json": {
                "schema": {
                  "additionalProperties": true,
                  "type": "object",
                  "title": "Response Analyze Cases Api Cases Analyze Post"
                }
              }
            }
          },
          "422": {
            "description": "Validation Error",
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/HTTPValidationError"
                }
              }
            }
          }
        }
      }
    },
    "/api/cases/stats": {
      "get": {
        "tags": [
          "WF-04 Case Analytics"
        ],
        "summary": "Case Stats",
        "description": "Aggregate stats + penalty timeline. NO LLM CALL \u2014 the dashboard renders free.",
        "operationId": "case_stats_api_cases_stats_get",
        "parameters": [
          {
            "name": "domain",
            "in": "query",
            "required": false,
            "schema": {
              "type": "string",
              "default": "energy_utilities",
              "title": "Domain"
            }
          }
        ],
        "responses": {
          "200": {
            "description": "Successful Response",
            "content": {
              "application/json": {
                "schema": {
                  "type": "object",
                  "additionalProperties": true,
                  "title": "Response Case Stats Api Cases Stats Get"
                }
              }
            }
          },
          "422": {
            "description": "Validation Error",
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/HTTPValidationError"
                }
              }
            }
          }
        }
      }
    },
    "/api/health": {
      "get": {
        "tags": [
          "ops"
        ],
        "summary": "Health",
        "operationId": "health_api_health_get",
        "responses": {
          "200": {
            "description": "Successful Response",
            "content": {
              "application/json": {
                "schema": {
                  "additionalProperties": true,
                  "type": "object",
                  "title": "Response Health Api Health Get"
                }
              }
            }
          }
        }
      }
    }
  },
  "components": {
    "schemas": {
      "Alert": {
        "properties": {
          "alert_id": {
            "type": "string",
            "title": "Alert Id"
          },
          "source": {
            "type": "string",
            "title": "Source"
          },
          "title": {
            "type": "string",
            "title": "Title"
          },
          "severity": {
            "anyOf": [
              {
                "type": "string",
                "enum": [
                  "critical",
                  "high",
                  "medium",
                  "low"
                ]
              },
              {
                "type": "string"
              }
            ],
            "title": "Severity"
          },
          "change_type": {
            "anyOf": [
              {
                "type": "string"
              },
              {
                "type": "null"
              }
            ],
            "title": "Change Type"
          },
          "summary": {
            "anyOf": [
              {
                "type": "string"
              },
              {
                "type": "null"
              }
            ],
            "title": "Summary"
          },
          "key_deadlines": {
            "items": {
              "type": "string"
            },
            "type": "array",
            "title": "Key Deadlines",
            "default": []
          },
          "penalty_info": {
            "anyOf": [
              {
                "type": "string"
              },
              {
                "type": "null"
              }
            ],
            "title": "Penalty Info"
          },
          "obligation_count": {
            "type": "integer",
            "title": "Obligation Count",
            "default": 0
          },
          "obligations": {
            "items": {
              "$ref": "#/components/schemas/Obligation"
            },
            "type": "array",
            "title": "Obligations",
            "default": []
          },
          "affected_departments": {
            "items": {
              "type": "string"
            },
            "type": "array",
            "title": "Affected Departments",
            "default": []
          },
          "impact_mappings": {
            "items": {
              "additionalProperties": true,
              "type": "object"
            },
            "type": "array",
            "title": "Impact Mappings",
            "default": []
          }
        },
        "type": "object",
        "required": [
          "alert_id",
          "source",
          "title",
          "severity"
        ],
        "title": "Alert"
      },
      "AuditRequest": {
        "properties": {
          "domain": {
            "type": "string",
            "title": "Domain",
            "default": "energy_utilities"
          },
          "audit_scope": {
            "type": "string",
            "title": "Audit Scope",
            "description": "An audit type from GET .../audit-types"
          },
          "regulations": {
            "items": {
              "type": "string"
            },
            "type": "array",
            "title": "Regulations",
            "description": "Regulations in scope"
          }
        },
        "type": "object",
        "required": [
          "audit_scope"
        ],
        "title": "AuditRequest"
      },
      "AuditResponse": {
        "properties": {
          "review_status": {
            "type": "string",
            "const": "PENDING_HUMAN_REVIEW",
            "title": "Review Status",
            "default": "PENDING_HUMAN_REVIEW"
          },
          "disclaimer": {
            "type": "string",
            "title": "Disclaimer",
            "default": "AI-generated decision support. Not a compliance determination. Every obligation, gap and drafted response requires review and sign-off by qualified personnel before use, and no content may be submitted to a regulator without that sign-off."
          },
          "audit_plan": {
            "additionalProperties": true,
            "type": "object",
            "title": "Audit Plan"
          },
          "evidence_inventory": {
            "items": {
              "additionalProperties": true,
              "type": "object"
            },
            "type": "array",
            "title": "Evidence Inventory"
          },
          "gap_analysis": {
            "items": {
              "additionalProperties": true,
              "type": "object"
            },
            "type": "array",
            "title": "Gap Analysis",
            "description": "THE PRODUCT. Each gap: severity, audit_risk, remediation{action,owner,effort,deadline}, interim_mitigation"
          },
          "draft_responses": {
            "items": {
              "additionalProperties": true,
              "type": "object"
            },
            "type": "array",
            "title": "Draft Responses"
          },
          "supervisor_review": {
            "$ref": "#/components/schemas/SupervisorReview"
          }
        },
        "type": "object",
        "required": [
          "audit_plan",
          "evidence_inventory",
          "gap_analysis",
          "draft_responses",
          "supervisor_review"
        ],
        "title": "AuditResponse"
      },
      "CaseRequest": {
        "properties": {
          "domain": {
            "type": "string",
            "title": "Domain",
            "default": "energy_utilities"
          },
          "query": {
            "type": "string",
            "title": "Query"
          },
          "analysis_type": {
            "type": "string",
            "enum": [
              "precedent",
              "trend",
              "risk",
              "summary"
            ],
            "title": "Analysis Type",
            "default": "precedent"
          }
        },
        "type": "object",
        "required": [
          "query"
        ],
        "title": "CaseRequest"
      },
      "DomainSummary": {
        "properties": {
          "key": {
            "type": "string",
            "title": "Key"
          },
          "label": {
            "type": "string",
            "title": "Label"
          },
          "vertical": {
            "type": "string",
            "title": "Vertical"
          },
          "company": {
            "type": "string",
            "title": "Company"
          },
          "company_full": {
            "type": "string",
            "title": "Company Full"
          },
          "financial_hook": {
            "type": "string",
            "title": "Financial Hook"
          },
          "regulators": {
            "items": {
              "$ref": "#/components/schemas/Regulator"
            },
            "type": "array",
            "title": "Regulators"
          },
          "departments": {
            "items": {
              "type": "string"
            },
            "type": "array",
            "title": "Departments"
          },
          "categories": {
            "items": {
              "type": "string"
            },
            "type": "array",
            "title": "Categories"
          },
          "regulation_count": {
            "type": "integer",
            "title": "Regulation Count"
          },
          "case_count": {
            "type": "integer",
            "title": "Case Count"
          },
          "evidence_count": {
            "type": "integer",
            "title": "Evidence Count"
          },
          "audit_types": {
            "items": {
              "type": "string"
            },
            "type": "array",
            "title": "Audit Types"
          }
        },
        "type": "object",
        "required": [
          "key",
          "label",
          "vertical",
          "company",
          "company_full",
          "financial_hook",
          "regulators",
          "departments",
          "categories",
          "regulation_count",
          "case_count",
          "evidence_count",
          "audit_types"
        ],
        "title": "DomainSummary"
      },
      "HTTPValidationError": {
        "properties": {
          "detail": {
            "items": {
              "$ref": "#/components/schemas/ValidationError"
            },
            "type": "array",
            "title": "Detail"
          }
        },
        "type": "object",
        "title": "HTTPValidationError"
      },
      "ImpactRequest": {
        "properties": {
          "domain": {
            "type": "string",
            "title": "Domain",
            "default": "energy_utilities"
          },
          "regulation_index": {
            "anyOf": [
              {
                "type": "integer"
              },
              {
                "type": "null"
              }
            ],
            "title": "Regulation Index",
            "description": "Index into GET /api/domains/{domain}/regulations"
          },
          "regulation_text": {
            "anyOf": [
              {
                "type": "string"
              },
              {
                "type": "null"
              }
            ],
            "title": "Regulation Text",
            "description": "Or paste raw regulatory text"
          },
          "regulation_source": {
            "type": "string",
            "title": "Regulation Source",
            "default": "Unknown"
          }
        },
        "type": "object",
        "title": "ImpactRequest"
      },
      "ImpactResponse": {
        "properties": {
          "review_status": {
            "type": "string",
            "const": "PENDING_HUMAN_REVIEW",
            "title": "Review Status",
            "default": "PENDING_HUMAN_REVIEW"
          },
          "disclaimer": {
            "type": "string",
            "title": "Disclaimer",
            "default": "AI-generated decision support. Not a compliance determination. Every obligation, gap and drafted response requires review and sign-off by qualified personnel before use, and no content may be submitted to a regulator without that sign-off."
          },
          "atomic_obligations": {
            "items": {
              "additionalProperties": true,
              "type": "object"
            },
            "type": "array",
            "title": "Atomic Obligations"
          },
          "cross_references": {
            "items": {
              "additionalProperties": true,
              "type": "object"
            },
            "type": "array",
            "title": "Cross References"
          },
          "impact_scores": {
            "items": {
              "additionalProperties": true,
              "type": "object"
            },
            "type": "array",
            "title": "Impact Scores"
          },
          "report": {
            "additionalProperties": true,
            "type": "object",
            "title": "Report",
            "description": "executive_summary, cost range, earliest_deadline, key_risks, recommended_actions[], board_attention_items[], regulatory_strategy"
          }
        },
        "type": "object",
        "required": [
          "atomic_obligations",
          "cross_references",
          "impact_scores",
          "report"
        ],
        "title": "ImpactResponse"
      },
      "MonitorRequest": {
        "properties": {
          "domain": {
            "type": "string",
            "title": "Domain",
            "default": "energy_utilities"
          },
          "source_filter": {
            "type": "string",
            "title": "Source Filter",
            "description": "Regulator code (e.g. 'OEIS', 'CPUC') or 'all'",
            "default": "all"
          }
        },
        "type": "object",
        "title": "MonitorRequest"
      },
      "MonitorResponse": {
        "properties": {
          "review_status": {
            "type": "string",
            "const": "PENDING_HUMAN_REVIEW",
            "title": "Review Status",
            "default": "PENDING_HUMAN_REVIEW"
          },
          "disclaimer": {
            "type": "string",
            "title": "Disclaimer",
            "default": "AI-generated decision support. Not a compliance determination. Every obligation, gap and drafted response requires review and sign-off by qualified personnel before use, and no content may be submitted to a regulator without that sign-off."
          },
          "alerts": {
            "items": {
              "$ref": "#/components/schemas/Alert"
            },
            "type": "array",
            "title": "Alerts"
          },
          "obligations": {
            "items": {
              "$ref": "#/components/schemas/Obligation"
            },
            "type": "array",
            "title": "Obligations"
          },
          "provenance": {
            "$ref": "#/components/schemas/Provenance"
          },
          "regulations_scanned": {
            "type": "integer",
            "title": "Regulations Scanned"
          }
        },
        "type": "object",
        "required": [
          "alerts",
          "obligations",
          "provenance",
          "regulations_scanned"
        ],
        "title": "MonitorResponse"
      },
      "Obligation": {
        "properties": {
          "obligation_id": {
            "type": "string",
            "title": "Obligation Id"
          },
          "description": {
            "type": "string",
            "title": "Description"
          },
          "responsible_entity": {
            "anyOf": [
              {
                "type": "string"
              },
              {
                "type": "null"
              }
            ],
            "title": "Responsible Entity"
          },
          "deadline": {
            "anyOf": [
              {
                "type": "string"
              },
              {
                "type": "null"
              }
            ],
            "title": "Deadline",
            "description": "or the literal string 'not stated in source'"
          },
          "measurement": {
            "anyOf": [
              {
                "type": "string"
              },
              {
                "type": "null"
              }
            ],
            "title": "Measurement"
          },
          "penalty": {
            "anyOf": [
              {
                "type": "string"
              },
              {
                "type": "null"
              }
            ],
            "title": "Penalty"
          },
          "category": {
            "anyOf": [
              {
                "type": "string"
              },
              {
                "type": "null"
              }
            ],
            "title": "Category"
          },
          "source_regulation": {
            "anyOf": [
              {
                "type": "string"
              },
              {
                "type": "null"
              }
            ],
            "title": "Source Regulation"
          },
          "source_body": {
            "anyOf": [
              {
                "type": "string"
              },
              {
                "type": "null"
              }
            ],
            "title": "Source Body"
          },
          "source_url": {
            "anyOf": [
              {
                "type": "string"
              },
              {
                "type": "null"
              }
            ],
            "title": "Source Url"
          },
          "severity": {
            "anyOf": [
              {
                "type": "string"
              },
              {
                "type": "null"
              }
            ],
            "title": "Severity"
          },
          "source_quote": {
            "anyOf": [
              {
                "type": "string"
              },
              {
                "type": "null"
              }
            ],
            "title": "Source Quote",
            "description": "VERBATIM span copied from the regulation"
          },
          "source_section": {
            "anyOf": [
              {
                "type": "string"
              },
              {
                "type": "null"
              }
            ],
            "title": "Source Section"
          },
          "confidence": {
            "anyOf": [
              {
                "type": "string",
                "enum": [
                  "high",
                  "medium",
                  "low"
                ]
              },
              {
                "type": "null"
              }
            ],
            "title": "Confidence"
          },
          "inferred": {
            "anyOf": [
              {
                "type": "boolean"
              },
              {
                "type": "null"
              }
            ],
            "title": "Inferred"
          },
          "citation_verified": {
            "anyOf": [
              {
                "type": "boolean"
              },
              {
                "type": "null"
              }
            ],
            "title": "Citation Verified",
            "description": "TRUE only if the quote was FOUND in the source text by core provenance verification. FALSE means the model may have paraphrased or fabricated it. The UI must show these with a warning badge and MUST NOT present them as equivalent to verified obligations."
          }
        },
        "type": "object",
        "required": [
          "obligation_id",
          "description"
        ],
        "title": "Obligation"
      },
      "Provenance": {
        "properties": {
          "total": {
            "type": "integer",
            "title": "Total"
          },
          "verified": {
            "type": "integer",
            "title": "Verified"
          },
          "unverified": {
            "type": "integer",
            "title": "Unverified"
          },
          "verified_pct": {
            "type": "integer",
            "title": "Verified Pct"
          }
        },
        "type": "object",
        "required": [
          "total",
          "verified",
          "unverified",
          "verified_pct"
        ],
        "title": "Provenance",
        "description": "Citation health for a run. The React UI MUST surface this \u2014 it is the trust story."
      },
      "RegulationSummary": {
        "properties": {
          "index": {
            "type": "integer",
            "title": "Index"
          },
          "source": {
            "type": "string",
            "title": "Source"
          },
          "title": {
            "type": "string",
            "title": "Title"
          },
          "published_date": {
            "type": "string",
            "title": "Published Date"
          },
          "url": {
            "anyOf": [
              {
                "type": "string"
              },
              {
                "type": "null"
              }
            ],
            "title": "Url"
          },
          "text": {
            "type": "string",
            "title": "Text"
          }
        },
        "type": "object",
        "required": [
          "index",
          "source",
          "title",
          "published_date",
          "text"
        ],
        "title": "RegulationSummary"
      },
      "Regulator": {
        "properties": {
          "code": {
            "type": "string",
            "title": "Code"
          },
          "name": {
            "type": "string",
            "title": "Name"
          },
          "scope": {
            "type": "string",
            "title": "Scope"
          }
        },
        "type": "object",
        "required": [
          "code",
          "name",
          "scope"
        ],
        "title": "Regulator"
      },
      "SupervisorReview": {
        "properties": {
          "overall_readiness": {
            "anyOf": [
              {
                "type": "string"
              },
              {
                "type": "null"
              }
            ],
            "title": "Overall Readiness"
          },
          "readiness_score": {
            "anyOf": [
              {
                "type": "integer"
              },
              {
                "type": "number"
              },
              {
                "type": "null"
              }
            ],
            "title": "Readiness Score",
            "description": "0-100. The headline number."
          },
          "executive_summary": {
            "anyOf": [
              {
                "type": "string"
              },
              {
                "type": "null"
              }
            ],
            "title": "Executive Summary"
          },
          "critical_items": {
            "items": {
              "type": "string"
            },
            "type": "array",
            "title": "Critical Items",
            "default": []
          },
          "strengths": {
            "items": {
              "type": "string"
            },
            "type": "array",
            "title": "Strengths",
            "default": []
          },
          "weaknesses": {
            "items": {
              "type": "string"
            },
            "type": "array",
            "title": "Weaknesses",
            "default": []
          },
          "recommendations": {
            "items": {
              "type": "string"
            },
            "type": "array",
            "title": "Recommendations",
            "default": []
          },
          "timeline_assessment": {
            "anyOf": [
              {
                "type": "string"
              },
              {
                "type": "null"
              }
            ],
            "title": "Timeline Assessment"
          }
        },
        "type": "object",
        "title": "SupervisorReview"
      },
      "ValidationError": {
        "properties": {
          "loc": {
            "items": {
              "anyOf": [
                {
                  "type": "string"
                },
                {
                  "type": "integer"
                }
              ]
            },
            "type": "array",
            "title": "Location"
          },
          "msg": {
            "type": "string",
            "title": "Message"
          },
          "type": {
            "type": "string",
            "title": "Error Type"
          },
          "input": {
            "title": "Input"
          },
          "ctx": {
            "type": "object",
            "title": "Context"
          }
        },
        "type": "object",
        "required": [
          "loc",
          "msg",
          "type"
        ],
        "title": "ValidationError"
      }
    }
  }
}
```
