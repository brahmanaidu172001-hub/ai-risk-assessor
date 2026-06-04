"""
Operations Risk Agent

Analyzes process, team, infrastructure, and execution dependency risks.
"""

from __future__ import annotations
import json
from typing import Any
import anthropic

from backend.config import settings
from backend.models.risk import RiskCategory, RiskFinding, CategoryReport, RiskLevel
from backend.scoring.engine import level_from_score, get_category_weight
from backend.tools.risk_tools import calculate_risk_score, generate_mitigation_plan


SYSTEM_PROMPT = """You are an operations and organizational risk analyst.

Analyze ONLY operational risks: team structure, process maturity, infrastructure dependencies,
single points of failure, capacity constraints, key-person risk, and business continuity gaps.

Return a JSON object:
{
  "findings": [
    {
      "title": "string",
      "description": "string",
      "likelihood": int (1-5),
      "impact": int (1-5),
      "evidence": ["string", ...],
      "mitigations": ["string", ...]
    }
  ],
  "summary": "string"
}

Respond with JSON only."""


class OperationsRiskAgent:
    def __init__(self) -> None:
        self.client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        self.category = RiskCategory.OPERATIONAL

    def run(self, name, description, industry, additional_context):
        prompt = (
            f"Business: {name}\nDescription: {description}\n"
            f"Team size: {additional_context.get('team_size', 'unknown')} | "
            f"Stage: {additional_context.get('stage', 'unknown')}\n\n"
            "Identify all material operational risks. Respond with JSON only."
        )

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

        return self._build_category_report(parsed, industry)

    def _build_category_report(self, data, industry):
        weight = get_category_weight(industry, self.category.value)
        findings: list[RiskFinding] = []

        for f in data.get("findings", []):
            likelihood = max(1, min(5, f.get("likelihood", 3)))
            impact = max(1, min(5, f.get("impact", 3)))
            score = calculate_risk_score(likelihood, impact, weight)
            severity = level_from_score(score)

            findings.append(
                RiskFinding(
                    category=self.category,
                    title=f.get("title", "Unnamed operational risk"),
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
            findings=[], summary=f"Operations analysis failed: {error}",
        )
