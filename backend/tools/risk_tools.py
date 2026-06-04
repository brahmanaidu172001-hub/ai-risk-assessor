"""
Tool functions available to risk assessment agents.

Each function is a self-contained tool with typed inputs/outputs. Agents call
these tools during the ToolExecutionNode of the workflow. Tools are pure
functions — no side effects, no LLM calls.
"""

from typing import Any
from backend.models.risk import RiskCategory, RiskFinding, RiskLevel, ActionItem
from backend.scoring.engine import compute_risk_score, level_from_score


def calculate_risk_score(
    likelihood: int,
    impact: int,
    category_weight: float = 1.0,
) -> float:
    """
    Compute a 0–100 risk score from likelihood, impact, and an optional
    category-specific weight multiplier.

    likelihood: 1–5 (rare → almost certain)
    impact:     1–5 (negligible → catastrophic)
    category_weight: domain multiplier (e.g. 1.2 for compliance-heavy industries)
    """
    return compute_risk_score(likelihood, impact, category_weight)


def classify_risk_category(
    description: str,
    keywords: list[str],
) -> dict[str, str]:
    """
    Classify a risk item into a RiskCategory based on keyword matching.
    Returns a dict with 'category' and 'confidence' keys.

    This is a deterministic heuristic — LLM-based classification happens
    inside the agent, this function provides a second-pass structural check.
    """
    keyword_map: dict[RiskCategory, list[str]] = {
        RiskCategory.FINANCIAL: [
            "revenue", "cash", "burn", "funding", "debt", "profit", "loss",
            "capital", "investment", "budget", "cost", "expense", "runway",
        ],
        RiskCategory.COMPLIANCE: [
            "gdpr", "ccpa", "pci", "hipaa", "soc2", "regulation", "legal",
            "audit", "license", "compliance", "law", "policy", "penalty",
        ],
        RiskCategory.CYBER: [
            "security", "breach", "hack", "vulnerability", "encryption",
            "data", "privacy", "access control", "authentication", "firewall",
        ],
        RiskCategory.OPERATIONAL: [
            "process", "workflow", "team", "staffing", "operations", "capacity",
            "bottleneck", "dependency", "infrastructure", "downtime",
        ],
        RiskCategory.MARKET: [
            "competition", "market", "demand", "customer", "adoption",
            "churn", "pricing", "market share", "saturation",
        ],
        RiskCategory.PRODUCT: [
            "product", "feature", "bug", "reliability", "performance",
            "quality", "roadmap", "technical debt", "architecture",
        ],
        RiskCategory.VENDOR: [
            "vendor", "third-party", "supplier", "partner", "api",
            "dependency", "sla", "contract", "outsource",
        ],
        RiskCategory.EXECUTION: [
            "timeline", "delivery", "milestone", "scope", "resource",
            "planning", "deadline", "delay", "estimate",
        ],
    }

    text = (description + " " + " ".join(keywords)).lower()
    scores: dict[RiskCategory, int] = {cat: 0 for cat in RiskCategory}

    for category, terms in keyword_map.items():
        for term in terms:
            if term in text:
                scores[category] += 1

    best = max(scores, key=lambda c: scores[c])
    total = sum(scores.values()) or 1
    confidence = "high" if scores[best] / total > 0.4 else "medium"

    return {"category": best.value, "confidence": confidence}


def generate_mitigation_plan(
    finding: dict[str, Any],
    max_items: int = 4,
) -> list[str]:
    """
    Generate a structured mitigation checklist for a given risk finding dict.
    Returns a list of actionable mitigation strings ordered by priority.

    This function provides template-based mitigations. The agent layer
    supplements these with LLM-generated context-specific actions.
    """
    category = finding.get("category", "")
    severity = finding.get("severity", "MEDIUM")
    title = finding.get("title", "")

    templates: dict[str, list[str]] = {
        RiskCategory.FINANCIAL.value: [
            "Establish a 6-month financial reserve or credit facility",
            "Implement monthly burn rate reviews with the board",
            "Diversify revenue streams to reduce single-source dependency",
            "Define clear financial triggers for operational adjustments",
        ],
        RiskCategory.COMPLIANCE.value: [
            "Engage a compliance counsel to map applicable regulations",
            "Conduct a gap assessment against required frameworks (SOC 2, GDPR, etc.)",
            "Implement a compliance calendar with quarterly review checkpoints",
            "Establish a data classification and handling policy",
        ],
        RiskCategory.CYBER.value: [
            "Commission an external penetration test within 60 days",
            "Enforce MFA and least-privilege access across all systems",
            "Implement a formal incident response plan and conduct a tabletop exercise",
            "Encrypt all PII and sensitive data at rest and in transit",
        ],
        RiskCategory.OPERATIONAL.value: [
            "Document all critical processes and identify single points of failure",
            "Cross-train team members on key operational functions",
            "Establish SLAs and monitoring for critical dependencies",
            "Create a business continuity and disaster recovery plan",
        ],
        RiskCategory.MARKET.value: [
            "Conduct structured customer discovery interviews (minimum 20)",
            "Define leading indicators of product-market fit",
            "Map competitive landscape and establish differentiation thesis",
            "Implement a churn tracking and win/loss analysis process",
        ],
        RiskCategory.PRODUCT.value: [
            "Implement automated test coverage for critical paths (target >80%)",
            "Establish a public-facing status page and incident communication process",
            "Conduct quarterly technical debt reviews with the engineering team",
            "Define and monitor SLOs for core product functions",
        ],
        RiskCategory.VENDOR.value: [
            "Review and negotiate SLAs with all critical third-party vendors",
            "Identify fallback or alternative vendors for single-source dependencies",
            "Conduct a vendor security assessment for vendors with data access",
            "Establish contractual data handling and breach notification requirements",
        ],
        RiskCategory.EXECUTION.value: [
            "Implement a project tracking system with weekly status reporting",
            "Define scope boundaries and a formal change management process",
            "Break delivery milestones into 2-week sprints with clear acceptance criteria",
            "Establish an escalation path for blocked items and dependencies",
        ],
    }

    mitigations = templates.get(category, ["Review risk with relevant stakeholders", "Define owner and remediation timeline"])

    if severity == RiskLevel.CRITICAL.value:
        mitigations = [f"[URGENT] {m}" for m in mitigations]

    return mitigations[:max_items]


def check_compliance_flags(
    industry: str,
    additional_context: dict[str, Any],
) -> list[dict[str, str]]:
    """
    Check for applicable regulatory and compliance flags based on industry
    and context metadata.

    Returns a list of flag dicts with 'regulation', 'applicability', and 'priority'.
    """
    flags: list[dict[str, str]] = []
    handles_pii = additional_context.get("handles_pii", False)
    primary_market = additional_context.get("primary_market", "").lower()
    handles_payments = additional_context.get("handles_payments", False)
    healthcare = additional_context.get("healthcare_data", False)
    is_public = additional_context.get("publicly_traded", False)

    if handles_pii or industry in ("fintech", "healthcare", "ecommerce"):
        flags.append({
            "regulation": "GDPR",
            "applicability": "Applies if serving EU users or processing EU citizen data",
            "priority": "high" if "eu" in primary_market or "europe" in primary_market else "medium",
        })
        flags.append({
            "regulation": "CCPA",
            "applicability": "Applies if serving California residents",
            "priority": "high" if "us" in primary_market else "medium",
        })

    if handles_payments or industry == "fintech":
        flags.append({
            "regulation": "PCI-DSS",
            "applicability": "Required for any entity storing, processing, or transmitting cardholder data",
            "priority": "critical",
        })
        flags.append({
            "regulation": "SOC 2 Type II",
            "applicability": "Expected by enterprise customers in financial services",
            "priority": "high",
        })

    if healthcare or industry == "healthcare":
        flags.append({
            "regulation": "HIPAA",
            "applicability": "Mandatory for handling protected health information",
            "priority": "critical",
        })

    if is_public:
        flags.append({
            "regulation": "SOX",
            "applicability": "Applies to publicly traded companies for financial reporting controls",
            "priority": "critical",
        })

    if industry in ("ai", "technology", "fintech"):
        flags.append({
            "regulation": "EU AI Act",
            "applicability": "May apply to AI systems deployed in the EU, especially high-risk use cases",
            "priority": "medium",
        })

    return flags


def summarize_business_context(
    name: str,
    description: str,
    additional_context: dict[str, Any],
) -> dict[str, Any]:
    """
    Extract and structure key business context signals from the input.
    Returns a normalized context dict used across all agents.
    """
    stage = additional_context.get("stage", "unknown")
    team_size = additional_context.get("team_size", 0)
    handles_pii = additional_context.get("handles_pii", False)
    revenue_stage = additional_context.get("revenue_stage", "pre-revenue" if stage in ("seed", "pre-seed") else "unknown")

    risk_amplifiers = []
    if team_size and team_size < 10:
        risk_amplifiers.append("small_team")
    if revenue_stage == "pre-revenue":
        risk_amplifiers.append("pre_revenue")
    if handles_pii:
        risk_amplifiers.append("pii_exposure")
    if stage in ("pre-seed", "seed"):
        risk_amplifiers.append("early_stage")

    return {
        "entity_name": name,
        "description_length": len(description),
        "stage": stage,
        "team_size": team_size,
        "handles_pii": handles_pii,
        "revenue_stage": revenue_stage,
        "risk_amplifiers": risk_amplifiers,
        "amplifier_count": len(risk_amplifiers),
    }


def prioritize_risks(findings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Sort risk findings by composite priority score (impact × likelihood × severity_weight).
    Returns findings in descending priority order.
    """
    severity_weights = {
        RiskLevel.CRITICAL.value: 2.0,
        RiskLevel.HIGH.value: 1.5,
        RiskLevel.MEDIUM.value: 1.0,
        RiskLevel.LOW.value: 0.5,
    }

    def priority_key(f: dict) -> float:
        w = severity_weights.get(f.get("severity", "MEDIUM"), 1.0)
        return f.get("impact", 3) * f.get("likelihood", 3) * w

    return sorted(findings, key=priority_key, reverse=True)


def generate_action_items(
    findings: list[dict[str, Any]],
    entity_name: str,
) -> list[dict[str, Any]]:
    """
    Convert prioritized risk findings into a numbered action plan.
    Each action item includes a priority, owner suggestion, and timeframe.
    """
    timeframe_map = {
        RiskLevel.CRITICAL.value: "Immediate (0–14 days)",
        RiskLevel.HIGH.value: "Short-term (15–30 days)",
        RiskLevel.MEDIUM.value: "Near-term (30–90 days)",
        RiskLevel.LOW.value: "Long-term (90+ days)",
    }

    owner_map = {
        RiskCategory.FINANCIAL.value: "CFO / Finance Lead",
        RiskCategory.COMPLIANCE.value: "Legal / Compliance Officer",
        RiskCategory.CYBER.value: "Head of Security / CTO",
        RiskCategory.OPERATIONAL.value: "COO / Operations Lead",
        RiskCategory.MARKET.value: "CEO / Head of Product",
        RiskCategory.PRODUCT.value: "CTO / Engineering Lead",
        RiskCategory.VENDOR.value: "Procurement / Legal",
        RiskCategory.EXECUTION.value: "Project Manager / CTO",
    }

    prioritized = prioritize_risks(findings)
    actions = []

    for i, finding in enumerate(prioritized[:10], start=1):
        severity = finding.get("severity", "MEDIUM")
        category = finding.get("category", "operational")
        mitigations = finding.get("mitigations", [])
        action_description = mitigations[0] if mitigations else f"Address {finding.get('title', 'identified risk')}"

        actions.append({
            "priority": i,
            "title": finding.get("title", f"Risk #{i}"),
            "description": action_description,
            "owner": owner_map.get(category, "Risk Owner"),
            "timeframe": timeframe_map.get(severity, "30–90 days"),
            "category": category,
        })

    return actions
