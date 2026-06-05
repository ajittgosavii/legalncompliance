"""
Case Analytics - RAG Chain (Gen AI)
Retrieval-heavy analysis of historical CPUC/FERC enforcement cases.
"""

import json
from langchain_core.messages import HumanMessage, SystemMessage

from core.llm import get_openai_primary
from core.prompts import CASE_ANALYTICS_PROMPT
from core.vectorstore import search_documents, add_documents, COLLECTION_CASES

# --- Sample Historical Case Data (28 cases across 7 regulators) ---
SAMPLE_CASES = [
    # ==================== CPUC — WILDFIRE & SAFETY ====================
    {
        "case_number": "I.19-06-015",
        "case_title": "Investigation into the Company Safety Culture and Governance",
        "regulator": "CPUC",
        "case_type": "investigation",
        "status": "resolved",
        "filing_date": "2019-06-27",
        "resolution_date": "2022-06-02",
        "penalty_amount": 0,
        "summary": "CPUC investigation into the Company's safety culture following 2017-2018 wildfire events. Resulted in Enhanced Oversight and Enforcement Process (EOEP) with independent safety monitor.",
        "key_findings": "Deficient safety culture; inadequate vegetation management; insufficient grid hardening investment; poor organizational accountability.",
        "precedent_tags": "safety_culture,wildfire,enhanced_oversight,governance"
    },
    {
        "case_number": "A.20-06-012",
        "case_title": "the Company 2020 Wildfire Mitigation Plan",
        "regulator": "CPUC",
        "case_type": "application",
        "status": "resolved",
        "filing_date": "2020-06-05",
        "resolution_date": "2021-02-11",
        "penalty_amount": 0,
        "summary": "Review of the Company's Wildfire Mitigation Plan. CPUC approved with conditions including accelerated undergrounding and enhanced vegetation management in HFTDs.",
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
        "summary": "CPUC investigation into the Kincade Fire caused by the Company transmission equipment. Resulted in $50M settlement including penalties and safety improvements.",
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
        "summary": "Investigation into the Camp Fire that destroyed the town of Paradise, killing 85 people. the Company pled guilty to 84 counts of involuntary manslaughter. Total liability exceeding $13.5B through bankruptcy proceedings, victim fund, and settlements.",
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
        "summary": "Investigation into the Zogg Fire in Shasta County that killed 4 people, caused by a gray pine tree contacting the Company distribution lines. $110M in penalties and corrective actions.",
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
        "summary": "Ongoing investigation into the Dixie Fire, the largest single (non-complex) fire in California history at 963,309 acres. Caused by a tree falling on the Company power line near Cresta Dam.",
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
        "case_title": "Investigation into the Company Natural Gas Distribution Pipeline Records",
        "regulator": "CPUC",
        "case_type": "investigation",
        "status": "resolved",
        "filing_date": "2012-01-12",
        "resolution_date": "2015-12-17",
        "penalty_amount": 38000000,
        "summary": "Follow-on investigation into the Company's gas pipeline recordkeeping practices. Found systemic deficiencies in Maximum Allowable Operating Pressure (MAOP) records. $38M penalty.",
        "key_findings": "Incomplete pipeline records dating back decades; inability to verify MAOP for hundreds of pipeline segments; inadequate data management systems; records retention failures.",
        "precedent_tags": "pipeline_safety,records,penalty,gas_operations,maop,data_management"
    },
    {
        "case_number": "I.17-02-002",
        "case_title": "the Company Gas Safety OII — Locate and Mark Practices",
        "regulator": "CPUC",
        "case_type": "enforcement",
        "status": "resolved",
        "filing_date": "2017-02-14",
        "resolution_date": "2019-08-22",
        "penalty_amount": 14000000,
        "summary": "Investigation into the Company's One-Call locate and mark practices for underground gas facilities. Found pattern of late or missed locates creating third-party dig-in risks. $14M penalty.",
        "key_findings": "Chronic late responses to One-Call requests; insufficient locate crews; inaccurate facility maps; multiple third-party dig-in incidents traceable to the Company failures.",
        "precedent_tags": "pipeline_safety,enforcement,one_call,locate_mark,penalty,dig_in"
    },
    # ==================== CPUC — RATE CASES & FINANCIAL ====================
    {
        "case_number": "A.21-06-021",
        "case_title": "the Company 2023 General Rate Case",
        "regulator": "CPUC",
        "case_type": "rate_case",
        "status": "resolved",
        "filing_date": "2021-06-30",
        "resolution_date": "2023-11-16",
        "penalty_amount": 0,
        "summary": "the Company's General Rate Case for 2023-2026. Authorized revenue requirement of ~$15.7B over 4 years. Included significant wildfire safety and grid modernization investments.",
        "key_findings": "Rate increases approved for safety investments; undergrounding program funded; customer affordability concerns noted; performance metrics tied to rate recovery.",
        "precedent_tags": "rate_case,revenue_requirement,grid_modernization,affordability"
    },
    {
        "case_number": "A.23-11-006",
        "case_title": "the Company 2027 General Rate Case Application",
        "regulator": "CPUC",
        "case_type": "rate_case",
        "status": "active",
        "filing_date": "2023-11-15",
        "resolution_date": None,
        "penalty_amount": 0,
        "summary": "the Company's General Rate Case for 2027-2030 cycle. Requesting approximately $18.2B in revenue requirements over 4 years for grid modernization, wildfire hardening, and clean energy transition.",
        "key_findings": "Pending decision; intervenors contesting affordability; rate impact estimated at 8-12% increase; CPUC balancing safety investment with customer bill concerns.",
        "precedent_tags": "rate_case,active,revenue_requirement,affordability,grid_modernization,clean_energy"
    },
    {
        "case_number": "A.22-04-008",
        "case_title": "the Company Undergrounding Program Cost Recovery",
        "regulator": "CPUC",
        "case_type": "application",
        "status": "resolved",
        "filing_date": "2022-04-12",
        "resolution_date": "2024-01-25",
        "penalty_amount": 0,
        "summary": "the Company application for 10,000-mile undergrounding program under SB 884. Approved with cost cap of $5.9M per mile for Tier 3 HFTD segments. Total approved program cost ~$20B over 10 years.",
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
        "summary": "PHMSA enforcement action for violations of 49 CFR 192 (Transportation of Natural Gas by Pipeline). Found 14 probable violations related to integrity management, corrosion control, and emergency response at the Company gas transmission facilities. $3.2M penalty.",
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
        "summary": "Cal-OSHA serious citations following the electrocution death of a the Company lineworker during de-energized line maintenance. Found minimum approach distance violations and lockout/tagout failures. $425K penalty.",
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
        "key_findings": "Trench exceeding 5 feet without shoring; competent person not present on site; soil classification not performed; prior OSHA warnings for similar violations at the Company worksites within 18 months.",
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
        "summary": "Citations for heat illness prevention failures involving a contracted vegetation management crew working in Tier 3 HFTD. Two workers hospitalized with heat stroke. $180K penalty against the Company as controlling employer.",
        "key_findings": "Shade structures not provided; water inadequately supplied; no acclimatization plan for new workers; heat illness prevention plan not communicated in workers' primary language (Spanish); the Company liable as controlling employer of contractor crew.",
        "precedent_tags": "worker_safety,cal_osha,enforcement,penalty,heat_illness,vegetation,contractor,controlling_employer"
    },
    # ==================== CEC — ENERGY COMMISSION ====================
    {
        "case_number": "CEC-2024-SIP-001",
        "case_title": "CEC Strategic Reliability Reserve: the Company Compliance Review",
        "regulator": "CEC",
        "case_type": "audit",
        "status": "resolved",
        "filing_date": "2024-01-10",
        "resolution_date": "2024-09-15",
        "penalty_amount": 0,
        "summary": "CEC review of the Company's compliance with Strategic Reliability Reserve requirements under SB 846. No penalties but findings on demand response program integration and battery storage deployment timelines.",
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
    llm = get_openai_primary()

    # Search for relevant cases
    relevant_cases = search_cases(query, k=5)
    stats = get_case_stats()

    # Also get the raw case data for rich analysis
    case_data = json.dumps(SAMPLE_CASES, indent=2, default=str)

    analysis_instructions = {
        "precedent": "Find precedent cases most relevant to the query. Analyze how similar situations were resolved and what penalties were imposed.",
        "trend": "Identify enforcement trends over time. Are penalties increasing? Are certain violation types becoming more common?",
        "risk": "Assess compliance risk based on enforcement history. What areas face the highest enforcement risk and potential penalties?",
        "summary": "Provide a comprehensive summary of all relevant cases, key patterns, and strategic implications for the Company.",
    }

    prompt = f"""Analyze the Company's regulatory case history based on this query.

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
            "key_takeaway": "main lesson for the Company"
        }}
    ],
    "patterns_identified": ["list of patterns"],
    "risk_assessment": {{
        "overall_risk": "low|medium|high|critical",
        "highest_risk_areas": ["areas"],
        "estimated_penalty_exposure": "dollar range"
    }},
    "recommendations": ["actionable recommendations for the Company"],
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
