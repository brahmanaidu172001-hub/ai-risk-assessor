"""
LangGraph-style workflow graph.

Implements a StateGraph pattern with sequential nodes. Each node is a pure
function that takes a WorkflowState and returns an updated WorkflowState.

This architecture is intentionally LangGraph-compatible: replacing this file
with a LangGraph StateGraph requires no changes to agents, tools, or models.

Node sequence:
  InputIntakeNode
    → ContextAnalysisNode
    → RiskClassificationNode
    → ToolExecutionNode
    → ScoringNode
    → MitigationNode
    → FinalReportNode
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Callable
from datetime import datetime

from backend.models.session import AssessmentRequest, AssessmentStatus
from backend.models.risk import RiskReport
from backend.tools.risk_tools import summarize_business_context, check_compliance_flags


# --- State -------------------------------------------------------------------

@dataclass
class WorkflowState:
    request: AssessmentRequest
    session_id: str
    status: AssessmentStatus = AssessmentStatus.PENDING

    # Populated by nodes as the workflow progresses
    business_context: dict[str, Any] = field(default_factory=dict)
    compliance_flags: list[dict[str, str]] = field(default_factory=list)
    risk_categories_identified: list[str] = field(default_factory=list)
    tool_outputs: dict[str, Any] = field(default_factory=dict)
    category_scores: dict[str, float] = field(default_factory=dict)
    mitigations_applied: bool = False
    final_report: RiskReport | None = None

    errors: list[str] = field(default_factory=list)
    node_trace: list[str] = field(default_factory=list)

    def record_node(self, node_name: str) -> None:
        self.node_trace.append(f"{node_name}:{datetime.utcnow().isoformat()}")


# --- Nodes -------------------------------------------------------------------

def input_intake_node(state: WorkflowState) -> WorkflowState:
    """
    Validates and normalizes the incoming assessment request.
    Flags missing or thin descriptions that may need clarification.
    """
    state.record_node("InputIntakeNode")

    description = state.request.description
    if len(description) < 50:
        state.errors.append(
            "Description is too short for reliable analysis. "
            "Provide at least a few sentences about the business, product, or workflow."
        )

    state.status = AssessmentStatus.RUNNING
    return state


def context_analysis_node(state: WorkflowState) -> WorkflowState:
    """
    Extracts structured business context from the request.
    Populates state.business_context for downstream nodes.
    """
    state.record_node("ContextAnalysisNode")

    state.business_context = summarize_business_context(
        name=state.request.name,
        description=state.request.description,
        additional_context=state.request.additional_context,
    )

    state.compliance_flags = check_compliance_flags(
        industry=state.request.industry,
        additional_context=state.request.additional_context,
    )

    return state


def risk_classification_node(state: WorkflowState) -> WorkflowState:
    """
    Identifies which risk categories are most likely to be material
    based on context signals, before running full agent analysis.
    """
    state.record_node("RiskClassificationNode")

    amplifiers = state.business_context.get("risk_amplifiers", [])
    categories = ["financial", "compliance", "cyber", "operational"]

    # Elevate category priority based on known amplifiers
    if "pii_exposure" in amplifiers:
        if "cyber" not in categories:
            categories.append("cyber")
        if "compliance" not in categories:
            categories.append("compliance")

    if "early_stage" in amplifiers or "pre_revenue" in amplifiers:
        if "execution" not in categories:
            categories.append("execution")

    if len(state.compliance_flags) > 2:
        # Compliance is clearly material
        categories = ["compliance"] + [c for c in categories if c != "compliance"]

    state.risk_categories_identified = categories
    return state


def tool_execution_node(state: WorkflowState) -> WorkflowState:
    """
    Executes deterministic tool calls before agent LLM invocations.
    Outputs are stored in state.tool_outputs for agents to reference.
    """
    state.record_node("ToolExecutionNode")

    state.tool_outputs = {
        "business_context": state.business_context,
        "compliance_flags": state.compliance_flags,
        "risk_categories": state.risk_categories_identified,
        "amplifier_count": state.business_context.get("amplifier_count", 0),
    }

    return state


def scoring_node(state: WorkflowState) -> WorkflowState:
    """
    Placeholder node — category scores are computed inside agents and
    aggregated by the CoordinatorAgent. This node records that scoring
    has been dispatched.
    """
    state.record_node("ScoringNode")
    # Actual scoring happens in agents/coordinator.py → scoring/engine.py
    return state


def mitigation_node(state: WorkflowState) -> WorkflowState:
    """
    Marks that mitigation generation has been triggered.
    Mitigation plans are generated inside agent tool calls.
    """
    state.record_node("MitigationNode")
    state.mitigations_applied = True
    return state


def final_report_node(state: WorkflowState) -> WorkflowState:
    """
    Marks the workflow complete and records completion status.
    The actual RiskReport is attached to state.final_report by the
    CoordinatorAgent after this node runs.
    """
    state.record_node("FinalReportNode")
    state.status = AssessmentStatus.COMPLETE
    return state


# --- Graph -------------------------------------------------------------------

NodeFn = Callable[[WorkflowState], WorkflowState]

WORKFLOW_NODES: list[tuple[str, NodeFn]] = [
    ("InputIntakeNode", input_intake_node),
    ("ContextAnalysisNode", context_analysis_node),
    ("RiskClassificationNode", risk_classification_node),
    ("ToolExecutionNode", tool_execution_node),
    ("ScoringNode", scoring_node),
    ("MitigationNode", mitigation_node),
    ("FinalReportNode", final_report_node),
]


class RiskAssessmentGraph:
    """
    Executes the risk assessment workflow as a linear StateGraph.

    Each node transforms the WorkflowState. On failure, the error is recorded
    in state.errors and execution continues (nodes are fault-tolerant by design).

    To migrate to LangGraph:
      1. Replace this class with a LangGraph StateGraph definition
      2. Register each node function as a graph node
      3. Add edges in WORKFLOW_NODES order
      4. The node functions themselves require no changes
    """

    def __init__(self) -> None:
        self.nodes = WORKFLOW_NODES

    def run(self, state: WorkflowState) -> WorkflowState:
        for node_name, node_fn in self.nodes:
            try:
                state = node_fn(state)
            except Exception as e:
                state.errors.append(f"{node_name} failed: {str(e)}")

        return state
