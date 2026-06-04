"""
Compliance Risk Agent

Analyzes regulatory, legal, data privacy, and licensing risks.
"""

from __future__ import annotations
import json
from typing import Any
import anthropic

from backend.config import settings
from backend.models.risk import RiskCategory, RiskFinding, CategoryReport, RiskLevel
from backend.scoring.engine import level_from_score, get_category_weight
from backend.tools.risk_tools import calculate_risk_score, generate_mitigation_plan, check_compliance_flags


SYSTEM_PROMPT = """You are a regulatory compliance and legal risk analyst.

Given a business description, analyze ONLY the compliance and regulatory risk dimension.
Consider: data privacy (GDPR, CCPA), financial regulations (PCI-DSS, SOX), industry-specific rules (HIPAA),
licensing, IP risk, employment law, and contractual obligations.

Return a JSON object:
{
  "findings": [
    {
      "title": "string",
      "description": "string (1-2 sentences)",
      "regulation": "string",
      "likelihood": int (1-5),
      "impact": int (1-5),
      "evidence": ["string", ...],
      "mitigations": ["string", ...]
    }
  ],
  "summary": "string (2-3 sentences)"
}

Respond with JSON only."""


class ComplianceRiskAgent:
    def __init__(self) -> None:
        self.client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        self.category = RiskCategory.COMPLIANCE

    def run(
        self,
        name: str,
        description: str,
        industry: str,
        additional_context: dict[str, Any],
    ) -> CategoryReport:
        compliance_flags = check_compliance_flags(industry, additional_context)
        prompt = self._build_prompt(name, description, industry, additional_context, compliance_flags)

        try:
            message = self.client.messages.create(
                model=settings.anthropic_model,
                max_tokens=settings.max_tokens,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt}],
            )
            raw = message.content[0].text
            if raw.strip().startswith("```"):
                raw = raw.strip().strip("`").lstrip("json").strip()
            parsed = json.loads(raw)
        except Exception as e:
            return self._fallback_report(str(e))

        return self._build_category_report(parsed, industry, compliance_flags)

    def _build_prompt(self, name, description, industry, ctx, flags):
        flag_str = "\n".join(
            f"- {f['regulation']}: {f['applicability']} (priority: {f['priority']})"
            for f in flags
        ) or "No pre-identified flags."
        return (
            f"Business: {name}\nIndustry: {industry}\nDescription: {description}\n"
            f"Handles PII: {ctx.get('handles_pii', False)}\n"
            f"Primary market: {ctx.get('primary_market', 'unknown')}\n\n"
            f"Pre-identified compliance flags:\n{flag_str}\n\n"
            "Identify all material compliance and regulatory risks. Respond with JSON only."
        )

    def _build_category_report(self, data, industry, flags):
        raw_findings = data.get("findings", [])
        weight = get_category_weight(industry, self.category.value)
        findings: list[RiskFinding] = []

        for f in raw_findings:
            likelihood = max(1, min(5, f.get("likelihood", 3)))
            impact = max(1, min(5, f.get("impact", 4)))
            score = calculate_risk_score(likelihood, impact, weight)
            severity = level_from_score(score)

            findings.append(
                RiskFinding(
                    category=self.category,
                    title=f.get("title", "Unnamed compliance risk"),
                    description=f.get("description", ""),
                    severity=severity,
                    likelihood=likelihood,
                    impact=impact,
                    score=score,
                    evidence=f.get("evidence", []),
                    mitigations=f.get("mitigations") or generate_mitigation_plan(
                        {"category": self.category.value, "severity": severity.value, "title": f.get("title", "")}
                    ),
                )
            )

        flag_titles = {f.title.lower() for f in findings}
        for flag in flags:
            if flag["regulation"].lower() not in flag_titles and flag["priority"] == "critical":
                sev_score = calculate_risk_score(4, 4, weight)
                findings.append(
                    RiskFinding(
                        category=self.category,
                        title=f"Unaddressed {flag['regulation']} requirement",
                        description=flag["applicability"],
                        severity=RiskLevel.HIGH,
                        likelihood=4,
                        impact=4,
                        score=sev_score,
                        evidence=[f"Flagged: {flag['regulation']}"],
                        mitigations=generate_mitigation_plan(
                            {"category": "compliance", "severity": "HIGH", "title": flag["regulation"]}
                        ),
                    )
                )

        category_score = max((f.score for f in findings), default=0.0)
        return CategoryReport(
            category=self.category,
            score=category_score,
            level=level_from_score(category_score),
            findings=findings,
            summary=data.get("summary", ""),
        )

    def _fallback_report(self, error):
        return CategoryReport(
            category=self.category, score=50.0, level=RiskLevel.MEDIUM,
            findings=[], summary=f"Compliance analysis failed: {error}",
        )
