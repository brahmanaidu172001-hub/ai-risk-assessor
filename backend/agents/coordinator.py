"""
Coordinator Agent

Dispatches all specialized agents in parallel (or sequence), collects their
CategoryReport outputs, computes the overall score, and calls the
ExecutiveSummaryAgent to synthesize the final report.

This is the entry point for the entire multi-agent pipeline.
"""

from __future__ import annotations
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any
import uuid
from datetime import datetime

from backend.models.risk import (
    RiskCategory, RiskReport, CategoryReport, RiskLevel, RiskFinding
)
from backend.models.session import AssessmentRequest
from backend.scoring.engine import compute_overall_score, level_from_score
from backend.tools.risk_tools import prioritize_risks
from backend.agents.financial_agent import FinancialRiskAgent
from backend.agents.compliance_agent import ComplianceRiskAgent
from backend.agents.operations_agent import OperationsRiskAgent
from backend.agents.cyber_agent import CyberDataRiskAgent
from backend.agents.executive_agent import ExecutiveSummaryAgent


class CoordinatorAgent:
    """
    Orchestrates the multi-agent risk assessment pipeline.

    Runs specialized agents concurrently where possible, then synthesizes
    all outputs into a single RiskReport via the ExecutiveSummaryAgent.
    """

    def __init__(self) -> None:
        self.financial = FinancialRiskAgent()
        self.compliance = ComplianceRiskAgent()
        self.operations = OperationsRiskAgent()
        self.cyber = CyberDataRiskAgent()
        self.executive = ExecutiveSummaryAgent()

    def run(self, session_id: str, request: AssessmentRequest) -> RiskReport:
        name = request.name
        description = request.description
        industry = request.industry
        ctx = request.additional_context

        # Run specialized agents concurrently
        category_reports = self._run_agents_parallel(name, description, industry, ctx)

        # Compute overall score from category scores
        category_scores = {r.category.value: r.score for r in category_reports}
        overall_score = compute_overall_score(category_scores)
        overall_level = level_from_score(overall_score)

        # Get top risks across all categories
        all_findings: list[RiskFinding] = []
        for r in category_reports:
            all_findings.extend(r.findings)

        findings_dicts = [f.model_dump(mode="json") for f in all_findings]
        top_findings_dicts = prioritize_risks(findings_dicts)[:5]
        top_findings = [f for fd in top_findings_dicts for f in all_findings if f.id == fd["id"]]

        # Executive summary + action plan
        exec_output = self.executive.run(name, overall_score, overall_level, category_reports)

        action_items_raw = exec_output.get("action_plan", [])
        from backend.models.risk import ActionItem
        action_items = [
            ActionItem(
                priority=a["priority"],
                title=a["title"],
                description=a["description"],
                owner=a["owner"],
                timeframe=a["timeframe"],
                category=RiskCategory(a["category"]),
            )
            for a in action_items_raw
        ]

        risk_summary = (
            f"{name} presents a {overall_level.value.lower()} risk profile "
            f"(score: {overall_score:.0f}/100) across {len(category_reports)} assessed dimensions."
        )

        return RiskReport(
            session_id=session_id,
            entity_name=name,
            context_type=request.context_type.value,
            industry=industry,
            overall_score=overall_score,
            overall_level=overall_level,
            risk_summary=risk_summary,
            category_reports=category_reports,
            top_risks=top_findings,
            action_plan=action_items,
            executive_summary=exec_output.get("executive_summary", ""),
            metadata={
                "agent_count": 4,
                "finding_count": len(all_findings),
                "completed_at": datetime.utcnow().isoformat(),
            },
        )

    def _run_agents_parallel(
        self,
        name: str,
        description: str,
        industry: str,
        ctx: dict[str, Any],
    ) -> list[CategoryReport]:
        agents = {
            "financial": lambda: self.financial.run(name, description, industry, ctx),
            "compliance": lambda: self.compliance.run(name, description, industry, ctx),
            "operations": lambda: self.operations.run(name, description, industry, ctx),
            "cyber": lambda: self.cyber.run(name, description, industry, ctx),
        }

        results: dict[str, CategoryReport] = {}

        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = {executor.submit(fn): key for key, fn in agents.items()}
            for future in as_completed(futures):
                key = futures[future]
                try:
                    results[key] = future.result()
                except Exception as e:
                    # Return a minimal fallback report on agent failure
                    cat_map = {
                        "financial": RiskCategory.FINANCIAL,
                        "compliance": RiskCategory.COMPLIANCE,
                        "operations": RiskCategory.OPERATIONAL,
                        "cyber": RiskCategory.CYBER,
                    }
                    results[key] = CategoryReport(
                        category=cat_map[key],
                        score=50.0,
                        level=RiskLevel.MEDIUM,
                        findings=[],
                        summary=f"Agent failed: {str(e)}",
                    )

        # Return in consistent order
        order = ["financial", "compliance", "operations", "cyber"]
        return [results[k] for k in order if k in results]
