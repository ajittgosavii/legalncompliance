"""
Case Analytics - RAG Chain (Gen AI)
Retrieval-heavy analysis of historical CPUC/FERC enforcement cases.
"""

import json
from langchain_core.messages import HumanMessage, SystemMessage

from core.llm import get_claude_sonnet
from core.prompts import CASE_ANALYTICS_PROMPT
from core.vectorstore import search_documents, add_documents, COLLECTION_CASES

# --- Sample Historical Case Data ---
SAMPLE_CASES = [
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
        "precedent_tags": "pipeline_safety,penalty,enforcement,gas_operations,record_penalty"
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
]


def load_sample_cases():
    """Load sample cases into the vector store."""
    texts = []
    metadatas = []
    for case in SAMPLE_CASES:
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

    add_documents(COLLECTION_CASES, texts, metadatas)
    return len(texts)


def search_cases(query: str, k: int = 5) -> list[dict]:
    """Search historical cases using semantic search."""
    results = search_documents(COLLECTION_CASES, query, k=k)
    return [{"content": doc.page_content, "score": round(score, 3), "metadata": doc.metadata}
            for doc, score in results]


def get_case_stats() -> dict:
    """Get summary statistics from the case database."""
    total_penalties = sum(c["penalty_amount"] for c in SAMPLE_CASES)
    by_regulator = {}
    by_type = {}
    by_status = {}

    for c in SAMPLE_CASES:
        by_regulator[c["regulator"]] = by_regulator.get(c["regulator"], 0) + 1
        by_type[c["case_type"]] = by_type.get(c["case_type"], 0) + 1
        by_status[c["status"]] = by_status.get(c["status"], 0) + 1

    penalties = [c for c in SAMPLE_CASES if c["penalty_amount"] > 0]

    return {
        "total_cases": len(SAMPLE_CASES),
        "total_penalties": total_penalties,
        "average_penalty": total_penalties / len(penalties) if penalties else 0,
        "max_penalty": max(c["penalty_amount"] for c in SAMPLE_CASES),
        "by_regulator": by_regulator,
        "by_type": by_type,
        "by_status": by_status,
        "penalty_cases": len(penalties),
    }


def run_case_analytics(query: str, analysis_type: str = "precedent") -> dict:
    """Run case analytics with Claude analysis over RAG results.

    analysis_type: 'precedent' | 'trend' | 'risk' | 'summary'
    """
    llm = get_claude_sonnet()

    # Search for relevant cases
    relevant_cases = search_cases(query, k=5)
    stats = get_case_stats()

    # Also get the raw case data for rich analysis
    case_data = json.dumps(SAMPLE_CASES, indent=2, default=str)

    analysis_instructions = {
        "precedent": "Find precedent cases most relevant to the query. Analyze how similar situations were resolved and what penalties were imposed.",
        "trend": "Identify enforcement trends over time. Are penalties increasing? Are certain violation types becoming more common?",
        "risk": "Assess compliance risk based on enforcement history. What areas face the highest enforcement risk and potential penalties?",
        "summary": "Provide a comprehensive summary of all relevant cases, key patterns, and strategic implications for PG&E.",
    }

    prompt = f"""Analyze PG&E's regulatory case history based on this query.

QUERY: {query}
ANALYSIS TYPE: {analysis_type}
INSTRUCTIONS: {analysis_instructions.get(analysis_type, analysis_instructions['summary'])}

RELEVANT CASES FROM SEARCH:
{json.dumps(relevant_cases, indent=2)}

FULL CASE DATABASE:
{case_data}

AGGREGATE STATISTICS:
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
        SystemMessage(content=CASE_ANALYTICS_PROMPT),
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
    return analysis
