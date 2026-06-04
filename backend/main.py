"""
FastAPI application — synchronous for demo reliability.
POST /assess runs the full pipeline and returns the completed report in one call.
"""
from __future__ import annotations
import time

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from backend.models.session import (
    AssessmentRequest, AssessmentResponse,
    AssessmentStatus, AssessmentSession,
)
from backend.workflow.graph import RiskAssessmentGraph, WorkflowState
from backend.agents.coordinator import CoordinatorAgent
from backend.storage.history import store
from backend.evaluation.logger import run_logger

app = FastAPI(title="AI Risk Assessor", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

graph = RiskAssessmentGraph()
coordinator = CoordinatorAgent()


@app.post("/assess", response_model=AssessmentResponse)
def submit_assessment(request: AssessmentRequest) -> AssessmentResponse:
    session = AssessmentSession(request=request)
    session_id = session.session_id
    start = time.time()

    store.upsert_session(
        session_id=session_id, entity_name=request.name,
        context_type=request.context_type.value,
        industry=request.industry, status="running",
    )

    try:
        state = WorkflowState(request=request, session_id=session_id)
        state = graph.run(state)
        report = coordinator.run(session_id=session_id, request=request)
        report_dict = report.to_dict()

        store.upsert_session(
            session_id=session_id, entity_name=request.name,
            context_type=request.context_type.value, industry=request.industry,
            status="complete", overall_score=report.overall_score,
            overall_level=report.overall_level.value, report=report_dict,
        )

        duration_ms = int((time.time() - start) * 1000)
        run_logger.log_run(
            session_id=session_id, request_data=request.model_dump(),
            report_data=report_dict, node_trace=state.node_trace,
            errors=state.errors, duration_ms=duration_ms,
        )

        return AssessmentResponse(
            session_id=session_id, status=AssessmentStatus.COMPLETE,
            message=f"Completed in {duration_ms / 1000:.1f}s", report=report_dict,
        )

    except Exception as e:
        error_msg = str(e)
        store.upsert_session(
            session_id=session_id, entity_name=request.name,
            context_type=request.context_type.value, industry=request.industry,
            status="failed", error=error_msg,
        )
        run_logger.log_error(session_id, error_msg)
        return AssessmentResponse(
            session_id=session_id, status=AssessmentStatus.FAILED,
            message=f"Assessment failed: {error_msg}", report=None,
        )


@app.get("/report/{session_id}", response_model=AssessmentResponse)
def get_report(session_id: str) -> AssessmentResponse:
    row = store.get_session(session_id)
    if not row:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
    return AssessmentResponse(
        session_id=session_id, status=AssessmentStatus(row["status"]),
        message=row.get("error", ""), report=row.get("report"),
    )


@app.get("/history")
def list_history(limit: int = 20) -> dict:
    sessions = store.list_sessions(limit=limit)
    return {"sessions": sessions, "count": len(sessions)}


@app.get("/health")
def health_check() -> dict:
    return {"status": "ok", "version": "1.0.0"}
