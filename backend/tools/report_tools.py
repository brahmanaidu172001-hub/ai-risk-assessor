"""
Report generation tools — called by the FinalReportNode and ExecutiveSummaryAgent.
Transforms structured risk data into formatted report sections.
"""

from typing import Any
from backend.models.risk import RiskReport, RiskLevel


def format_executive_summary(report_data: dict[str, Any]) -> str:
    """
    Produce a plain-English executive summary paragraph from a completed
    risk report dict. Used as a fallback when the LLM summary is unavailable.
    """
    name = report_data.get("entity_name", "The entity")
    score = report_data.get("overall_score", 0)
    level = report_data.get("overall_level", "MEDIUM")
    categories = report_data.get("category_reports", [])

    critical = [c for c in categories if c.get("level") == "CRITICAL"]
    high = [c for c in categories if c.get("level") == "HIGH"]

    critical_names = ", ".join(c.get("category", "") for c in critical)
    high_names = ", ".join(c.get("category", "") for c in high)

    summary_parts = [
        f"{name} has an overall risk score of {score:.0f}/100 ({level}).",
    ]

    if critical:
        summary_parts.append(
            f"Critical risk areas requiring immediate attention: {critical_names}."
        )
    if high:
        summary_parts.append(
            f"High-risk areas requiring near-term remediation: {high_names}."
        )

    action_count = len(report_data.get("action_plan", []))
    if action_count:
        summary_parts.append(
            f"The assessment has produced {action_count} prioritized action items."
        )

    return " ".join(summary_parts)


def build_risk_score_breakdown(category_reports: list[dict]) -> dict[str, Any]:
    """
    Build a structured score breakdown table from category reports.
    Useful for frontend rendering and API consumers.
    """
    breakdown = {}
    for report in category_reports:
        cat = report.get("category", "unknown")
        breakdown[cat] = {
            "score": round(report.get("score", 0), 1),
            "level": report.get("level", "LOW"),
            "finding_count": len(report.get("findings", [])),
        }
    return breakdown


def generate_report_markdown(report: RiskReport) -> str:
    """
    Render a full risk report as Markdown. Useful for exporting,
    saving to file, or displaying in a docs interface.
    """
    lines = [
        f"# Risk Assessment Report: {report.entity_name}",
        f"**Session ID:** {report.session_id}  ",
        f"**Date:** {report.created_at.strftime('%Y-%m-%d %H:%M UTC')}  ",
        f"**Industry:** {report.industry}  ",
        f"**Overall Risk Score:** {report.overall_score:.0f}/100 ({report.overall_level.value})",
        "",
        "---",
        "",
        "## Executive Summary",
        "",
        report.executive_summary or report.risk_summary,
        "",
        "---",
        "",
        "## Risk Category Breakdown",
        "",
    ]

    for cr in report.category_reports:
        lines.append(f"### {cr.category.value.title()} Risk — {cr.score:.0f}/100 ({cr.level.value})")
        lines.append("")
        if cr.summary:
            lines.append(cr.summary)
            lines.append("")
        if cr.findings:
            for f in cr.findings:
                lines.append(f"**{f.title}** (Severity: {f.severity.value})")
                lines.append(f"> {f.description}")
                if f.mitigations:
                    lines.append("Mitigations:")
                    for m in f.mitigations:
                        lines.append(f"- {m}")
                lines.append("")

    lines += [
        "---",
        "",
        "## Action Plan",
        "",
    ]

    for item in report.action_plan:
        lines.append(f"**{item.priority}. {item.title}**  ")
        lines.append(f"Owner: {item.owner} | Timeframe: {item.timeframe}  ")
        lines.append(item.description)
        lines.append("")

    return "\n".join(lines)
