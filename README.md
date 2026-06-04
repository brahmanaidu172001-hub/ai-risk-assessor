# AI Risk Assessor
### Agentic Business Risk Intelligence System

A production-style AI application that accepts a business, product, vendor, or operational workflow description and returns a structured executive risk report — scored, reasoned, and actionable.

Built to demonstrate agentic AI architecture, multi-agent coordination, tool-using agents, and structured LLM output in a real-world product context.

---

## Why This Project Matters

Most AI demos are wrappers: input → LLM → output. This project is different. It shows:

- **Agentic architecture** — a coordinator dispatches specialized agents, each with its own focus and tools
- **Tool-using agents** — agents call typed Python functions to score, classify, and generate structured outputs
- **Multi-step reasoning** — the workflow runs through defined nodes (intake → analysis → scoring → mitigation → report)
- **Structured AI output** — every result is a typed Pydantic model, not raw text
- **Business + technical thinking** — risk categories, scoring rubrics, and mitigation logic reflect real risk management frameworks
- **Production-style code** — modular, typed, error-handled, and extensible

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        FRONTEND                             │
│                  Streamlit UI (frontend/app.py)             │
└──────────────────────────┬──────────────────────────────────┘
                           │ HTTP
┌──────────────────────────▼──────────────────────────────────┐
│                      BACKEND API                            │
│               FastAPI (backend/main.py)                     │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│                  AGENT ORCHESTRATION                        │
│            Coordinator Agent (agents/coordinator.py)        │
│                                                             │
│   ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────┐  │
│   │Financial │ │Compliance│ │Operations│ │  Cyber/Data  │  │
│   │  Agent   │ │  Agent   │ │  Agent   │ │    Agent     │  │
│   └────┬─────┘ └────┬─────┘ └────┬─────┘ └──────┬───────┘  │
│        └────────────┴────────────┴───────────────┘          │
│                           │                                  │
│              ┌────────────▼────────────┐                    │
│              │   Executive Summary     │                    │
│              │       Agent             │                    │
│              └─────────────────────────┘                    │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│                      TOOL LAYER                             │
│  calculate_risk_score  │  classify_risk_category            │
│  generate_mitigation   │  check_compliance_flags            │
│  summarize_context     │  prioritize_risks                  │
│  generate_action_items │  generate_report                   │
└──────────────────────────┬──────────────────────────────────┘
                           │
          ┌────────────────┴────────────────┐
          │                                 │
┌─────────▼──────────┐           ┌──────────▼──────────┐
│   SCORING ENGINE   │           │  STORAGE / HISTORY  │
│  scoring/engine.py │           │  storage/history.py │
└────────────────────┘           └─────────────────────┘
          │
┌─────────▼──────────┐
│ EVALUATION/LOGGING │
│ evaluation/logger  │
└────────────────────┘
```

---

## LangGraph-Style Workflow Nodes

The agent workflow runs through these sequential nodes (implemented in `backend/workflow/graph.py`):

```
InputIntakeNode
      │
      ▼
ContextAnalysisNode
      │
      ▼
RiskClassificationNode
      │
      ▼
ToolExecutionNode  ──► [calls: calculate_risk_score, check_compliance_flags, etc.]
      │
      ▼
ScoringNode
      │
      ▼
MitigationNode
      │
      ▼
FinalReportNode
```

Each node receives the full workflow state object and returns an updated state. This mirrors LangGraph's `StateGraph` pattern exactly — swapping in LangGraph is a one-file change.

---

## Specialized Agents

| Agent | Responsibility |
|---|---|
| `FinancialRiskAgent` | Revenue, burn rate, funding, capital exposure |
| `ComplianceRiskAgent` | Regulatory, legal, data privacy, licensing |
| `OperationsRiskAgent` | Process gaps, team, execution, dependencies |
| `CyberDataRiskAgent` | Security posture, data handling, third-party exposure |
| `ExecutiveSummaryAgent` | Synthesizes all agent outputs into a final executive brief |
| `CoordinatorAgent` | Dispatches all agents, merges results, drives workflow |

---

## Tools Available to Agents

| Tool | Purpose |
|---|---|
| `calculate_risk_score()` | Computes a weighted 0–100 risk score from factors |
| `classify_risk_category()` | Tags risk items with category and severity |
| `generate_mitigation_plan()` | Returns prioritized mitigation steps per risk |
| `check_compliance_flags()` | Flags regulatory and legal risk indicators |
| `summarize_business_context()` | Extracts structured context from raw description |
| `prioritize_risks()` | Sorts risks by impact × likelihood |
| `generate_action_items()` | Produces a numbered action plan |

---

## Risk Categories

- Financial Risk
- Operational Risk
- Compliance Risk
- Cybersecurity / Data Risk
- Market Risk
- Product Risk
- Vendor / Third-Party Risk
- Execution Risk

---

## Tech Stack

| Layer | Technology |
|---|---|
| LLM Interface | OpenAI-compatible (works with OpenAI or Anthropic via LiteLLM) |
| Agent Framework | Custom LangGraph-style workflow (drop-in LangGraph compatible) |
| Backend API | FastAPI + Uvicorn |
| Data Models | Pydantic v2 |
| Frontend | Streamlit |
| Storage | SQLite (via Python `sqlite3`) |
| Evaluation | Structured JSON logging |
| Config | `python-dotenv` |

---

## Project Structure

```
ai-risk-assessor/
├── README.md
├── .env.example
├── requirements.txt
│
├── backend/
│   ├── main.py                    # FastAPI app, routes
│   ├── config.py                  # Settings, env vars
│   │
│   ├── models/
│   │   ├── risk.py                # Risk, RiskReport, RiskCategory models
│   │   └── session.py             # Session, AssessmentRequest models
│   │
│   ├── tools/
│   │   ├── risk_tools.py          # Tool functions the agent calls
│   │   └── report_tools.py        # Report generation tools
│   │
│   ├── scoring/
│   │   └── engine.py              # Risk scoring logic
│   │
│   ├── agents/
│   │   ├── coordinator.py         # Orchestrates all agents
│   │   ├── financial_agent.py
│   │   ├── compliance_agent.py
│   │   ├── operations_agent.py
│   │   ├── cyber_agent.py
│   │   └── executive_agent.py
│   │
│   ├── workflow/
│   │   └── graph.py               # LangGraph-style StateGraph nodes
│   │
│   ├── storage/
│   │   └── history.py             # SQLite session history
│   │
│   └── evaluation/
│       └── logger.py              # Structured run logging
│
├── frontend/
│   └── app.py                     # Streamlit UI
│
├── sample_data/
│   ├── ai_startup.json
│   ├── vendor_onboarding.json
│   └── financial_ops_automation.json
│
└── sample_outputs/
    └── ai_startup_report.json
```

---

## Quick Start

### 1. Clone and install

```bash
git clone https://github.com/yourhandle/ai-risk-assessor
cd ai-risk-assessor
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env — add your OPENAI_API_KEY or compatible key
```

### 3. Run the backend

```bash
uvicorn backend.main:app --reload --port 8000
```

### 4. Run the frontend (separate terminal)

```bash
streamlit run frontend/app.py
```

Open `http://localhost:8501` in your browser.

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/assess` | Submit a new risk assessment |
| `GET` | `/report/{session_id}` | Retrieve a completed report |
| `GET` | `/history` | List all past sessions |
| `GET` | `/health` | Health check |

### Example Request

```json
POST /assess
{
  "name": "NovaPay",
  "description": "Early-stage fintech startup building an AI-powered payments API for SMBs. Pre-revenue, 4-person team, handling live transaction data in production.",
  "context_type": "startup",
  "industry": "fintech",
  "additional_context": {
    "team_size": 4,
    "stage": "seed",
    "handles_pii": true,
    "primary_market": "US"
  }
}
```

### Example Response (abbreviated)

```json
{
  "session_id": "ra-2024-abc123",
  "entity_name": "NovaPay",
  "overall_score": 74,
  "overall_level": "HIGH",
  "risk_summary": "NovaPay carries significant risk across compliance, cybersecurity, and execution dimensions typical of early-stage fintech.",
  "risk_categories": [
    {
      "category": "compliance",
      "score": 85,
      "level": "CRITICAL",
      "findings": ["No SOC 2 certification", "PCI-DSS scope unclear"],
      "mitigations": ["Engage compliance consultant pre-Series A", "Scope PCI-DSS requirements immediately"]
    }
  ],
  "action_plan": [...],
  "executive_summary": "..."
}
```

---

## Sample Use Cases

Three ready-to-run examples in `sample_data/`:

1. **AI Startup** — Early-stage company launching an LLM-powered product
2. **Vendor Onboarding** — Third-party software vendor being evaluated for enterprise integration
3. **Financial Operations Automation** — Internal workflow automation project in a financial services firm

---

## Future Enterprise Improvements

- Real-time data enrichment from Crunchbase, LinkedIn, SEC filings
- RAG layer grounding analysis in regulatory documents and industry benchmarks
- Human-in-the-loop analyst review step between classification and final report
- Full LangGraph migration with checkpointing and state persistence
- Streaming output via SSE for real-time report generation
- Auth + multi-tenancy with per-org history and RBAC
- Risk trend tracking — reassess over time and track trajectory
- Webhook delivery to Slack, email, Notion

---

## How I Built This

I use AI coding tools like Claude as an acceleration layer, but I review the architecture, logic, workflows, and product decisions myself. My focus is on structuring the system, defining the agent workflow, testing the output, and improving the business logic.

The agent workflow, tool signatures, risk scoring rubric, Pydantic model design, and API structure were all defined and validated by me. The goal was to build something a senior engineer would find credible — not something that looks auto-generated in architecture or reasoning.

---

## Interview Positioning

This project was built to demonstrate readiness for a **Product Engineer / AI Product role** at a startup. It shows:

- I can design agentic AI systems, not just prompt wrappers
- I understand separation between orchestration, tool execution, scoring, and output layers
- I think in terms of structured output, typed models, and production API design
- I can position AI as a business tool — risk categories and scoring rubrics map to real frameworks (ISO 31000, NIST, SOC 2)
- I build with AI tools efficiently while maintaining architectural ownership

---

*License: MIT*
