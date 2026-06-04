"""
Financial Risk Agent

Analyzes financial exposure: runway, revenue concentration, funding dependency,
burn rate, and capital structure risks.
"""

from __future__ import annotations
import json
from typing import Any
import anthropic

from backend.config import settings
from backend.models.risk import RiskCategory, RiskFinding, CategoryReport, RiskLevel
from backend.scoring.engine import level_from_score, get_category_weight
from backend.tools.risk_tools import calculate_risk_score, generate_mitigation_plan


SYSTEM_PROMPT = """You are a financial risk analyst specializing in startup and enterprise risk assessment.

Given a business description, analyze ONLY the financial risk dimension.
Identify specific financial risks, score their likelihood (1-5) and impact (1-5), and suggest mitigations.

Return a JSON object with this exact structure:
{
  "findings": [
    {
      "title": "string",
      "description": "string (1-2 sentences)",
      "likelihood": int (1-5),
      "impact": int (1-5),
      "evidence": ["string", ...],
      "mitigations": ["string", ...]
    }
  ],
  "summary": "string (2-3 sentences summarizing financial risk)"
}

Be specific and business-relevant. Avoid generic statements."""


class FinancialRiskAgent:
    def __init__(self) -> None:
        self.client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        self.category = RiskCategory.FINANCIAL

    def run(
        self,
        name: str,
        description: str,
        industry: str,
        additional_context: dict[str, Any],
    ) -> CategoryReport:
        prompt = self._build_prompt(name, description, additional_context)

        try:
            message = self.client.messages.create(
                model=settings.anthropic_model,
                max_tokens=settings.max_tokens,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt}],
            )
            raw = message.content[0].text
            # Strip markdown code fences if present
            if raw.strip().startswith("```"):
                raw = raw.strip().strip("`").lstrip("json").strip()
            parsed = json.loads(raw)
        except Exception as e:
            return self._fallback_report(str(e))

        return self._build_category_report(parsed, industry)

    def _build_prompt(self, name: str, description: str, ctx: dict[str, Any]) -> str:
        stage = ctx.get("stage", "unknown")
        team_size = ctx.get("team_size", "unknown")
        revenue_stage = ctx.get("revenue_stage", "unknown")
        return (
            f"Business: {name}\n"
            f"Description: {description}\n"
            f"Stage: {stage} | Team size: {team_size} | Revenue: {revenue_stage}\n\n"
            "Identify all material financial risks. Respond with JSON only."
        )

    def _build_category_report(self, data: dict, industry: str) -> CategoryReport:
        raw_findings = data.get("findings", [])
        weight = get_category_weight(industry, self.category.value)
        findings: list[RiskFinding] = []

        for f in raw_findings:
            likelihood = max(1, min(5, f.get("likelihood", 3)))
            impact = max(1, min(5, f.get("impact", 3)))
            score = calculate_risk_score(likelihood, impact, weight)
            severity = level_from_score(score)

            mitigations = f.get("mitigations") or generate_mitigation_plan(
                {"category": self.category.value, "severity": severity.value, "title": f.get("title", "")}
            )

            findings.append(
                RiskFinding(
                    category=self.category,
                    title=f.get("title", "Unnamed financial risk"),
                    description=f.get("description", ""),
                    severity=severity,
                    likelihood=likelihood,
                    impact=impact,
                    score=score,
                    evidence=f.get("evidence", []),
                    mitigations=mitigations,
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

    def _fallback_report(self, error: str) -> CategoryReport:
        return CategoryReport(
            category=self.category,
            score=50.0,
            level=RiskLevel.MEDIUM,
            findings=[],
            summary=f"Financial risk analysis could not be completed: {error}",
        )
