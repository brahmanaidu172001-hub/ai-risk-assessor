"""
Executive Summary Agent

Synthesizes all specialized agent outputs into a concise board-ready executive summary.
"""

from __future__ import annotations
import json
from typing import Any
import anthropic

from backend.config import settings
from backend.models.risk import CategoryReport, RiskLevel
from backend.tools.risk_tools import generate_action_items


SYSTEM_PROMPT = """You are a senior risk officer writing a board-level executive summary.

You will receive structured risk findings from multiple specialized agents.
Write a concise, plain-English executive summary (3-4 paragraphs) that:
1. States the overall risk posture and score
2. Highlights the top 2-3 risk areas with specific findings
3. Summarizes the most important actions required
4. Closes with a forward-looking risk outlook

Write in a professional, direct tone. No bullet points — prose only.

Return a JSON object: {"executive_summary": "string"}

Respond with JSON only."""


class ExecutiveSummaryAgent:
    def __init__(self) -> None:
        self.client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

    def run(
        self,
        entity_name: str,
        overall_score: float,
        overall_level: RiskLevel,
        category_reports: list[CategoryReport],
    ) -> dict[str, Any]:
        findings_summary = self._build_findings_summary(category_reports)
        action_items = self._build_action_items(category_reports)

        prompt = (
            f"Entity: {entity_name}\n"
            f"Overall Risk Score: {overall_score:.0f}/100 ({overall_level.value})\n\n"
            f"Risk findings by category:\n{findings_summary}\n\n"
            "Write the executive summary. Respond with JSON only."
        )

        try:
            message = self.client.messages.create(
                model=settings.anthropic_model,
                max_tokens=1024,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt}],
            )
            raw = message.content[0].text
            if raw.strip().startswith("```"):
                raw = raw.strip().strip("`").lstrip("json").strip()
            data = json.loads(raw)
            executive_summary = data.get("executive_summary", "")
        except Exception:
            executive_summary = self._fallback_summary(entity_name, overall_score, overall_level, category_reports)

        return {"executive_summary": executive_summary, "action_plan": action_items}

    def _build_findings_summary(self, reports: list[CategoryReport]) -> str:
        lines = []
        for r in sorted(reports, key=lambda x: x.score, reverse=True):
            titles = "; ".join(f.title for f in r.findings[:3])
            lines.append(f"- {r.category.value.title()} ({r.level.value}, score {r.score:.0f}): {titles}")
        return "\n".join(lines)

    def _build_action_items(self, reports: list[CategoryReport]) -> list[dict]:
        all_findings = []
        for r in reports:
            for f in r.findings:
                all_findings.append(f.model_dump(mode="json"))
        return generate_action_items(all_findings, entity_name="")

    def _fallback_summary(self, name, score, level, reports):
        critical = [r for r in reports if r.level == RiskLevel.CRITICAL]
        high = [r for r in reports if r.level == RiskLevel.HIGH]
        top = (critical + high)[:2]
        top_names = " and ".join(r.category.value for r in top) if top else "multiple areas"
        return (
            f"{name} presents a {level.value.lower()} overall risk profile with a score of "
            f"{score:.0f}/100. Key risk concentrations exist in {top_names}. "
            "Immediate remediation actions are recommended for critical findings. "
            "A structured risk management program should be established to track progress."
        )
