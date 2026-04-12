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
    {
        "source": "CPUC",
        "title": "Decision 24-05-079: Updated Wildfire Mitigation Plan Requirements",
        "url": "https://docs.cpuc.ca.gov/PublishedDocs/Published/G000/M530/K123/530123456.PDF",
        "published_date": "2025-12-15",
        "text": """The California Public Utilities Commission hereby orders Pacific Gas and Electric Company
        and all large electrical corporations to submit updated Wildfire Mitigation Plans (WMPs) incorporating
        the following new requirements effective January 1, 2026:

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

        Non-compliance penalties: Up to $100,000 per violation per day under PU Code Section 2107."""
    },
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
    }
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
