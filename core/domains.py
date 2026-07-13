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
