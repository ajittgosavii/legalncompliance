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
