"""
AI Risk Assessor — Premium Enterprise Dark UI
Built by Brahma Naidu | Powered by Anthropic Claude
"""

import requests
import streamlit as st

API_BASE = "http://localhost:8000"

st.set_page_config(
    page_title="AI Risk Assessor",
    page_icon="\U0001f6e1",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Constants ─────────────────────────────────────────────────────────────────
LEVEL_COLOR = {"CRITICAL": "#f43f5e", "HIGH": "#fb923c", "MEDIUM": "#fbbf24", "LOW": "#34d399"}
LEVEL_BG    = {"CRITICAL": "rgba(244,63,94,0.08)", "HIGH": "rgba(251,146,60,0.08)",
               "MEDIUM": "rgba(251,191,36,0.08)", "LOW": "rgba(52,211,153,0.08)"}
LEVEL_BORDER= {"CRITICAL": "rgba(244,63,94,0.3)", "HIGH": "rgba(251,146,60,0.3)",
               "MEDIUM": "rgba(251,191,36,0.3)", "LOW": "rgba(52,211,153,0.3)"}
LEVEL_EMOJI = {"CRITICAL": "\U0001f534", "HIGH": "\U0001f7e0", "MEDIUM": "\U0001f7e1", "LOW": "\U0001f7e2"}
TIMEFRAME_COLOR = {"Immediate": "#f43f5e", "Short-term": "#fb923c",
                   "Near-term": "#fbbf24", "Long-term": "#34d399"}

SAMPLES = {
    "AI Startup \u2014 Luminary AI": {
        "name": "Luminary AI",
        "description": (
            "Early-stage startup building an LLM-powered contract analysis tool for legal teams. "
            "Uses Claude to extract clauses, flag risks, and summarize contracts. "
            "5 employees, $800K seed funding, processing real customer contracts in production. "
            "No formal security review conducted. Pre-revenue, targeting US and EU law firms."
        ),
        "context_type": "startup", "industry": "ai",
        "team_size": 5, "stage": "seed",
        "handles_pii": True, "handles_payments": False,
    },
    "Vendor Onboarding \u2014 DataSync Pro": {
        "name": "DataSync Pro",
        "description": (
            "Third-party data integration vendor for enterprise pipeline evaluation. "
            "Would have read/write access to customer database and analytics warehouse. "
            "SOC 2 Type I only. EU data centers. One prior S3 bucket incident. DPA not reviewed."
        ),
        "context_type": "vendor", "industry": "technology",
        "team_size": 45, "stage": "series_a",
        "handles_pii": True, "handles_payments": False,
    },
    "Financial Ops \u2014 AutoPay Workflow": {
        "name": "AutoPay Workflow",
        "description": (
            "Internal project to automate accounts payable using AI invoice processing. "
            "Handles $12M monthly payments, integrates with SAP ERP, auto-approves invoices "
            "under $5K. 2-person team, 90-day deadline. No formal risk or change management. "
            "Direct write access to payment tables."
        ),
        "context_type": "workflow", "industry": "fintech",
        "team_size": 2, "stage": "internal",
        "handles_pii": True, "handles_payments": True,
    },
}

# -- CSS ----------------------------------------------------------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');

*,*::before,*::after{box-sizing:border-box}
*,html,body{font-family:'Inter',-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif!important}

/* Hide Streamlit chrome */
#MainMenu,[data-testid="stToolbar"],[data-testid="stDecoration"],
[data-testid="stHeader"],footer,header{display:none!important}
[data-testid="stStatusWidget"]{display:none!important}

/* Global background */
html,body,[data-testid="stApp"],[data-testid="stAppViewContainer"],
[data-testid="stMain"],section.main,.main{background:#03050a!important;color:#e2e8f0!important}
section.main>div{padding-top:0.5rem!important}
.block-container{max-width:1280px!important;padding:1rem 2.5rem 3rem!important}

/* Sidebar */
[data-testid="stSidebar"]{background:linear-gradient(180deg,#080c14 0%,#060a11 100%)!important;border-right:1px solid rgba(99,102,241,0.12)!important}
[data-testid="stSidebar"]>div:first-child{padding:2rem 1.25rem!important}
[data-testid="stSidebar"] *,[data-testid="stSidebar"] p,[data-testid="stSidebar"] span,[data-testid="stSidebar"] div{color:#94a3b8!important}
[data-testid="stSidebar"] label{color:#475569!important;font-size:0.78rem!important}

/* Typography */
h1,h2,h3,h4{color:#f1f5f9!important;font-weight:700!important;letter-spacing:-0.3px!important}
code{background:rgba(99,102,241,0.12)!important;color:#a5b4fc!important;padding:2px 6px!important;border-radius:4px!important;font-size:0.82em!important}

/* Inputs */
[data-testid="stTextInput"] input,[data-testid="stTextArea"] textarea{background:#0c1220!important;color:#e2e8f0!important;border:1px solid rgba(99,102,241,0.2)!important;border-radius:10px!important;font-size:0.875rem!important;transition:border-color 0.2s,box-shadow 0.2s!important}
[data-testid="stTextInput"] input:focus,[data-testid="stTextArea"] textarea:focus{border-color:rgba(99,102,241,0.55)!important;box-shadow:0 0 0 3px rgba(99,102,241,0.12)!important;outline:none!important}
[data-testid="stTextInput"] label,[data-testid="stTextArea"] label,[data-testid="stSelectbox"] label,[data-testid="stNumberInput"] label,[data-testid="stCheckbox"] label{color:#475569!important;font-size:0.73rem!important;font-weight:700!important;letter-spacing:0.8px!important;text-transform:uppercase!important}

/* Selectbox */
[data-testid="stSelectbox"]>div>div{background:#0c1220!important;border:1px solid rgba(99,102,241,0.2)!important;border-radius:10px!important;color:#e2e8f0!important}
[data-baseweb="popover"]>div{background:#0f1827!important;border:1px solid rgba(99,102,241,0.25)!important;border-radius:10px!important;box-shadow:0 20px 60px rgba(0,0,0,0.6)!important}
[data-baseweb="option"]{background:transparent!important;color:#cbd5e1!important;font-size:0.875rem!important}
[data-baseweb="option"]:hover{background:rgba(99,102,241,0.12)!important;color:#e2e8f0!important}

/* Number input */
[data-testid="stNumberInput"] input{background:#0c1220!important;color:#e2e8f0!important;border:1px solid rgba(99,102,241,0.2)!important;border-radius:10px!important}

/* Primary button */
[data-testid="baseButton-primary"],[data-testid="baseButton-primary"]>button{background:linear-gradient(135deg,#6366f1 0%,#4f46e5 60%,#4338ca 100%)!important;color:#fff!important;border:none!important;border-radius:10px!important;font-weight:600!important;font-size:0.92rem!important;letter-spacing:0.1px!important;box-shadow:0 4px 16px rgba(99,102,241,0.35),0 1px 3px rgba(0,0,0,0.3)!important;transition:all 0.2s!important}
[data-testid="baseButton-primary"]:hover{transform:translateY(-1px)!important;box-shadow:0 8px 28px rgba(99,102,241,0.45)!important}
[data-testid="baseButton-secondary"],[data-testid="baseButton-secondary"]>button{background:rgba(15,23,42,0.8)!important;color:#64748b!important;border:1px solid rgba(99,102,241,0.18)!important;border-radius:10px!important;font-size:0.85rem!important;transition:all 0.15s!important}
[data-testid="baseButton-secondary"]:hover{border-color:rgba(99,102,241,0.4)!important;color:#94a3b8!important}

/* Tabs */
[data-testid="stTabs"] [role="tablist"]{background:transparent!important;border-bottom:1px solid rgba(99,102,241,0.12)!important;gap:2px!important}
[data-testid="stTabs"] [role="tab"]{background:transparent!important;color:#475569!important;border:none!important;border-radius:8px 8px 0 0!important;font-size:0.875rem!important;font-weight:500!important;padding:0.55rem 1.4rem!important;transition:all 0.15s!important}
[data-testid="stTabs"] [role="tab"][aria-selected="true"]{color:#a5b4fc!important;background:rgba(99,102,241,0.07)!important;border-bottom:2px solid #6366f1!important}

/* Metrics */
[data-testid="stMetric"]{background:linear-gradient(135deg,#0c1220 0%,#09101d 100%)!important;border:1px solid rgba(99,102,241,0.15)!important;border-radius:14px!important;padding:1.1rem 1.3rem!important;box-shadow:0 4px 24px rgba(0,0,0,0.25),inset 0 1px 0 rgba(255,255,255,0.03)!important;transition:border-color 0.2s!important}
[data-testid="stMetric"]:hover{border-color:rgba(99,102,241,0.3)!important}
[data-testid="stMetricLabel"] p{color:#475569!important;font-size:0.7rem!important;font-weight:700!important;letter-spacing:1px!important;text-transform:uppercase!important;margin:0!important}
[data-testid="stMetricValue"]{color:#f1f5f9!important;font-size:1.9rem!important;font-weight:800!important;line-height:1.1!important}
[data-testid="stMetricDelta"]{display:none!important}

/* Expander */
[data-testid="stExpander"]{background:#080e1a!important;border:1px solid rgba(99,102,241,0.13)!important;border-radius:12px!important;overflow:hidden!important;transition:border-color 0.2s!important;margin-bottom:8px!important}
[data-testid="stExpander"]:hover{border-color:rgba(99,102,241,0.28)!important}
[data-testid="stExpander"]>details>summary{padding:0.9rem 1.2rem!important;color:#94a3b8!important;font-weight:500!important;font-size:0.875rem!important;background:transparent!important}
[data-testid="stExpander"]>details[open]>summary{border-bottom:1px solid rgba(99,102,241,0.1)!important;color:#c7d2fe!important}

/* Form */
[data-testid="stForm"]{background:linear-gradient(135deg,#090f1c 0%,#070d18 100%)!important;border:1px solid rgba(99,102,241,0.18)!important;border-radius:18px!important;padding:1.75rem 2rem!important;box-shadow:0 8px 40px rgba(0,0,0,0.3),inset 0 1px 0 rgba(255,255,255,0.02)!important}

/* Divider */
hr{border:none!important;height:1px!important;background:linear-gradient(90deg,transparent,rgba(99,102,241,0.2),transparent)!important;margin:2rem 0!important}

/* Scrollbar */
::-webkit-scrollbar{width:5px;height:5px}
::-webkit-scrollbar-track{background:transparent}
::-webkit-scrollbar-thumb{background:rgba(99,102,241,0.25);border-radius:10px}
::-webkit-scrollbar-thumb:hover{background:rgba(99,102,241,0.45)}

/* Hero */
.hero-wrap{background:linear-gradient(135deg,#0c1422 0%,#090e1a 40%,#0b0918 100%);border:1px solid rgba(99,102,241,0.18);border-radius:20px;padding:2.2rem 2.8rem;margin-bottom:1.75rem;position:relative;overflow:hidden}
.hero-badge{display:inline-flex;align-items:center;gap:6px;background:rgba(99,102,241,0.1);border:1px solid rgba(99,102,241,0.25);border-radius:20px;padding:4px 14px;font-size:0.72rem;font-weight:600;color:#a5b4fc;letter-spacing:0.5px;text-transform:uppercase;margin-bottom:1rem}
.hero-title{font-size:2.6rem;font-weight:900;line-height:1.05;margin:0;background:linear-gradient(135deg,#f8fafc 0%,#e2e8f0 40%,#a5b4fc 100%);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;letter-spacing:-0.8px}
.hero-subtitle{font-size:1rem;color:#475569;margin-top:0.45rem;font-weight:400;letter-spacing:0.2px}
.hero-meta{display:flex;align-items:center;gap:20px;margin-top:1.25rem;flex-wrap:wrap}
.hero-pill{display:inline-flex;align-items:center;gap:5px;font-size:0.75rem;color:#334155;letter-spacing:0.3px}
.hero-pill strong{color:#6366f1;font-weight:600}

/* Section header */
.sec-hd{font-size:0.68rem;font-weight:800;letter-spacing:2px;text-transform:uppercase;color:#2d3f5c;margin:0 0 0.9rem 0;display:block}

/* Score ring */
.score-ring{background:linear-gradient(145deg,#0d1627,#09101d);border:1px solid rgba(99,102,241,0.2);border-radius:18px;padding:1.6rem 1rem;text-align:center;box-shadow:0 8px 32px rgba(0,0,0,0.3),inset 0 1px 0 rgba(255,255,255,0.03);position:relative;overflow:hidden}
.score-num{font-size:4rem;font-weight:900;line-height:1;position:relative}
.score-denom{font-size:1.1rem;font-weight:400;color:#334155}
.score-lbl{font-size:0.65rem;font-weight:700;letter-spacing:2px;text-transform:uppercase;color:#2d3f5c;margin-top:0.3rem;position:relative}

/* Entity header */
.entity-hdr{background:linear-gradient(135deg,#0c1422,#090d1a);border:1px solid rgba(99,102,241,0.15);border-radius:16px;padding:1.4rem 1.8rem;margin-bottom:1.4rem;box-shadow:0 4px 24px rgba(0,0,0,0.2)}

/* Category cards */
.cat-card{background:linear-gradient(145deg,#0c1220,#09101d);border:1px solid rgba(99,102,241,0.12);border-radius:14px;padding:1.2rem 0.9rem;text-align:center;box-shadow:0 4px 20px rgba(0,0,0,0.2);transition:transform 0.15s,box-shadow 0.15s}
.cat-card:hover{transform:translateY(-2px);box-shadow:0 8px 32px rgba(0,0,0,0.3)}
.cat-num{font-size:2.1rem;font-weight:900;line-height:1}
.cat-lbl{font-size:0.65rem;font-weight:700;letter-spacing:1.2px;text-transform:uppercase;color:#334155;margin-top:4px}

/* Risk chip badge */
.risk-chip{display:inline-flex;align-items:center;padding:3px 11px;border-radius:20px;font-size:0.67rem;font-weight:800;letter-spacing:0.8px;text-transform:uppercase;border:1px solid}
.chip-CRITICAL{background:rgba(244,63,94,0.08);color:#f43f5e;border-color:rgba(244,63,94,0.3)}
.chip-HIGH{background:rgba(251,146,60,0.08);color:#fb923c;border-color:rgba(251,146,60,0.3)}
.chip-MEDIUM{background:rgba(251,191,36,0.08);color:#fbbf24;border-color:rgba(251,191,36,0.3)}
.chip-LOW{background:rgba(52,211,153,0.08);color:#34d399;border-color:rgba(52,211,153,0.3)}

/* Finding cards */
.find-card{border-radius:13px;padding:1rem 1.2rem;margin-bottom:10px;border-left:3px solid;box-shadow:0 3px 16px rgba(0,0,0,0.2);transition:transform 0.15s}
.find-card:hover{transform:translateX(3px)}
.find-CRITICAL{background:rgba(244,63,94,0.04);border-color:#f43f5e;border-top:1px solid rgba(244,63,94,0.12);border-right:1px solid rgba(244,63,94,0.08);border-bottom:1px solid rgba(244,63,94,0.08)}
.find-HIGH{background:rgba(251,146,60,0.04);border-color:#fb923c;border-top:1px solid rgba(251,146,60,0.12);border-right:1px solid rgba(251,146,60,0.08);border-bottom:1px solid rgba(251,146,60,0.08)}
.find-MEDIUM{background:rgba(251,191,36,0.04);border-color:#fbbf24;border-top:1px solid rgba(251,191,36,0.12);border-right:1px solid rgba(251,191,36,0.08);border-bottom:1px solid rgba(251,191,36,0.08)}
.find-LOW{background:rgba(52,211,153,0.04);border-color:#34d399;border-top:1px solid rgba(52,211,153,0.12);border-right:1px solid rgba(52,211,153,0.08);border-bottom:1px solid rgba(52,211,153,0.08)}
.find-title{font-weight:600;font-size:0.9rem;color:#e2e8f0;line-height:1.3}
.find-meta{font-size:0.72rem;color:#334155;margin-top:5px;letter-spacing:0.2px}
.find-desc{font-size:0.84rem;color:#64748b;margin-top:8px;line-height:1.6}

/* Mitigation items */
.mit-item{display:flex;gap:8px;padding:5px 0;font-size:0.82rem;color:#475569;line-height:1.5;border-bottom:1px solid rgba(99,102,241,0.06)}
.mit-item:last-child{border-bottom:none}
.mit-arrow{color:#6366f1;font-weight:700;flex-shrink:0;margin-top:1px}

/* Action cards */
.act-card{background:linear-gradient(135deg,#09101c,#070d17);border:1px solid rgba(99,102,241,0.13);border-radius:14px;padding:1.1rem 1.4rem;margin-bottom:10px;box-shadow:0 3px 16px rgba(0,0,0,0.18);transition:border-color 0.2s}
.act-card:hover{border-color:rgba(99,102,241,0.28)}
.act-num{font-size:0.67rem;font-weight:800;color:#6366f1;letter-spacing:1px;text-transform:uppercase;margin-bottom:3px}
.act-title{font-weight:700;font-size:0.9rem;color:#e2e8f0}
.act-meta{font-size:0.72rem;color:#334155;margin-top:4px}
.act-desc{font-size:0.84rem;color:#64748b;margin-top:6px;line-height:1.6}
.tf-chip{display:inline-block;padding:2px 10px;border-radius:5px;font-size:0.67rem;font-weight:700;border:1px solid;letter-spacing:0.3px}

/* Exec summary */
.exec-card{background:linear-gradient(135deg,#09101c,#070d17);border:1px solid rgba(99,102,241,0.18);border-radius:16px;padding:1.6rem 1.8rem;line-height:1.85;color:#94a3b8;font-size:0.9rem;box-shadow:0 8px 40px rgba(0,0,0,0.25),inset 0 1px 0 rgba(255,255,255,0.02)}

/* Sidebar components */
.sb-label{font-size:0.6rem;font-weight:800;letter-spacing:2px;text-transform:uppercase;color:#1e2d45!important;display:block;margin-bottom:0.6rem;padding-bottom:0.4rem;border-bottom:1px solid rgba(99,102,241,0.08)}
.sb-agent{display:flex;align-items:center;gap:8px;padding:5px 8px;border-radius:7px;margin-bottom:2px;font-size:0.78rem;color:#2d4060!important;cursor:default;transition:background 0.15s}
.sb-agent:hover{background:rgba(99,102,241,0.06);color:#475569!important}
.sb-dot{width:6px;height:6px;border-radius:50%;background:rgba(99,102,241,0.4);flex-shrink:0}
.byline-box{background:linear-gradient(135deg,rgba(99,102,241,0.07),rgba(139,92,246,0.04));border:1px solid rgba(99,102,241,0.12);border-radius:12px;padding:0.9rem 1rem;margin-top:1rem}

/* Footer */
.footer-bar{text-align:center;padding:2rem 0 0.5rem;margin-top:2.5rem;border-top:1px solid rgba(99,102,241,0.08)}
.footer-inner{font-size:0.75rem;color:#1a2540;letter-spacing:0.4px}
.footer-name{color:#6366f1!important;font-weight:700}
</style>
""", unsafe_allow_html=True)



# -- render_report (defined before any call site) ----------------------------
def render_report(report: dict) -> None:
    level        = (report.get("overall_level") or "MEDIUM").upper()
    score        = float(report.get("overall_score") or 0)
    entity       = report.get("entity_name") or "Unknown Entity"
    industry     = report.get("industry") or ""
    context_type = report.get("context_type") or ""
    session_id   = report.get("session_id") or ""
    score_color  = LEVEL_COLOR.get(level, "#6366f1")
    cat_reports  = report.get("category_reports") or []
    top_risks    = report.get("top_risks") or []
    action_plan  = report.get("action_plan") or []
    exec_summary = report.get("executive_summary") or report.get("risk_summary") or ""

    st.markdown("<hr>", unsafe_allow_html=True)

    # Entity header
    emoji = LEVEL_EMOJI.get(level, "")
    st.markdown(f"""
    <div class="entity-hdr">
      <div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:10px;">
        <div>
          <div style="font-size:1.5rem;font-weight:800;color:#f1f5f9;letter-spacing:-0.4px;">{entity}</div>
          <div style="font-size:0.78rem;color:#2d3f5c;margin-top:4px;">
            {industry.title()} &middot; {context_type.title()} &nbsp;|&nbsp;
            <code>{session_id}</code>
          </div>
        </div>
        <span class="risk-chip chip-{level}">{emoji} {level} RISK</span>
      </div>
    </div>""", unsafe_allow_html=True)

    # Score row
    c1, c2, c3, c4 = st.columns([1.1, 1, 1, 1])
    finding_count  = sum(len(c.get("findings") or []) for c in cat_reports)
    critical_count = sum(1 for c in cat_reports if (c.get("level") or "").upper() == "CRITICAL")
    with c1:
        st.markdown(f"""
        <div class="score-ring">
          <div class="score-num" style="color:{score_color};">{score:.0f}<span class="score-denom">/100</span></div>
          <div class="score-lbl">Overall Risk Score</div>
        </div>""", unsafe_allow_html=True)
    with c2:
        st.metric("Total Findings", finding_count)
    with c3:
        st.metric("Categories", len(cat_reports))
    with c4:
        st.metric("Critical Areas", critical_count)

    st.markdown("<br>", unsafe_allow_html=True)

    # Executive summary
    if exec_summary:
        st.markdown('<span class="sec-hd">Executive Summary</span>', unsafe_allow_html=True)
        st.markdown(f'<div class="exec-card">{exec_summary}</div>', unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)

    # Category breakdown
    if cat_reports:
        st.markdown('<span class="sec-hd">Category Breakdown</span>', unsafe_allow_html=True)
        cols = st.columns(max(len(cat_reports), 1))
        for i, cat in enumerate(cat_reports):
            cat_level = (cat.get("level") or "LOW").upper()
            cat_score = float(cat.get("score") or 0)
            cat_name  = cat.get("category") or "unknown"
            c_col = LEVEL_COLOR.get(cat_level, "#6366f1")
            with cols[i % len(cols)]:
                st.markdown(f"""
                <div class="cat-card" style="border-top:3px solid {c_col};">
                  <div class="cat-num" style="color:{c_col};">{cat_score:.0f}</div>
                  <div class="cat-lbl">{cat_name}</div>
                  <div style="margin-top:10px;"><span class="risk-chip chip-{cat_level}">{cat_level}</span></div>
                </div>""", unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)

    # Top risks
    if top_risks:
        st.markdown('<span class="sec-hd">Top Risk Findings</span>', unsafe_allow_html=True)
        for f in top_risks[:6]:
            sev   = (f.get("severity") or "MEDIUM").upper()
            title = f.get("title") or "Unnamed risk"
            desc  = f.get("description") or ""
            cat   = f.get("category") or ""
            lh    = f.get("likelihood") or "?"
            imp   = f.get("impact") or "?"
            sc    = float(f.get("score") or 0)
            st.markdown(f"""
            <div class="find-card find-{sev}">
              <div style="display:flex;align-items:flex-start;justify-content:space-between;gap:10px;flex-wrap:wrap;">
                <span class="find-title">{title}</span>
                <span class="risk-chip chip-{sev}">{sev}</span>
              </div>
              <div class="find-meta">{cat.title()} &nbsp;&middot;&nbsp; Score {sc:.0f} &nbsp;&middot;&nbsp; Likelihood {lh}/5 &nbsp;&middot;&nbsp; Impact {imp}/5</div>
              <div class="find-desc">{desc}</div>
            </div>""", unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)

    # Detailed findings by category
    if cat_reports:
        st.markdown('<span class="sec-hd">Detailed Findings by Category</span>', unsafe_allow_html=True)
        for cat in cat_reports:
            cat_level   = (cat.get("level") or "LOW").upper()
            cat_score   = float(cat.get("score") or 0)
            cat_name    = cat.get("category") or "unknown"
            cat_summary = cat.get("summary") or ""
            findings    = cat.get("findings") or []
            n = len(findings)
            label = f"{cat_name.title()} Risk  ·  {cat_score:.0f}/100  ·  {cat_level}  ·  {n} finding{'s' if n != 1 else ''}"
            with st.expander(label):
                if cat_summary:
                    st.markdown(f'<p style="color:#64748b;font-size:0.85rem;margin-bottom:12px;line-height:1.65;">{cat_summary}</p>', unsafe_allow_html=True)
                for f in findings:
                    sev   = (f.get("severity") or "MEDIUM").upper()
                    title = f.get("title") or "Unnamed risk"
                    desc  = f.get("description") or ""
                    mits  = f.get("mitigations") or []
                    evids = f.get("evidence") or []
                    st.markdown(f"""
                    <div class="find-card find-{sev}" style="margin-bottom:10px;">
                      <div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap;">
                        <span class="find-title">{title}</span>
                        <span class="risk-chip chip-{sev}">{sev}</span>
                      </div>
                      <div class="find-desc">{desc}</div>
                    </div>""", unsafe_allow_html=True)
                    if mits:
                        st.markdown('<p style="font-size:0.68rem;font-weight:800;letter-spacing:1.5px;color:#1e2d45;margin:10px 0 5px;text-transform:uppercase;">Mitigations</p>', unsafe_allow_html=True)
                        mit_html = "".join(f'<div class="mit-item"><span class="mit-arrow">&rarr;</span>{m}</div>' for m in mits)
                        st.markdown(f'<div style="padding:4px 0;">{mit_html}</div>', unsafe_allow_html=True)
                    if evids:
                        st.markdown('<p style="font-size:0.68rem;font-weight:800;letter-spacing:1.5px;color:#1e2d45;margin:10px 0 5px;text-transform:uppercase;">Evidence</p>', unsafe_allow_html=True)
                        for e in evids:
                            st.markdown(f'<p style="font-size:0.78rem;color:#2d3f5c;margin:2px 0;padding-left:12px;">&middot; {e}</p>', unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)

    # Action plan
    if action_plan:
        st.markdown('<span class="sec-hd">Action Plan</span>', unsafe_allow_html=True)
        for item in action_plan:
            priority  = item.get("priority") or ""
            title     = item.get("title") or ""
            desc      = item.get("description") or ""
            owner     = item.get("owner") or "Risk Owner"
            timeframe = item.get("timeframe") or ""
            category  = item.get("category") or ""
            t_color   = next((v for k, v in TIMEFRAME_COLOR.items() if k in timeframe), "#6366f1")
            st.markdown(f"""
            <div class="act-card">
              <div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:8px;">
                <div>
                  <div class="act-num">Action #{priority} &nbsp;&middot;&nbsp; {category.upper()}</div>
                  <div class="act-title">{title}</div>
                </div>
                <span class="tf-chip" style="color:{t_color};border-color:{t_color};background:rgba(0,0,0,0.2);">{timeframe}</span>
              </div>
              <div class="act-meta">Owner: {owner}</div>
              <div class="act-desc">{desc}</div>
            </div>""", unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)

    with st.expander("Raw Report JSON"):
        st.json(report)

    st.markdown("""
    <div class="footer-bar">
      <div class="footer-inner">
        Built by <span class="footer-name">Brahma Naidu</span>
        <span style="color:#1e2d45;margin:0 8px;">|</span>
        Multi-Agent Risk Intelligence Demo
        <span style="color:#1e2d45;margin:0 8px;">|</span>
        Powered by Anthropic Claude
      </div>
    </div>""", unsafe_allow_html=True)



# -- Sidebar ------------------------------------------------------------------
with st.sidebar:
    st.markdown("""
    <div class="sb-section">
      <span class="sb-label">AI Risk Assessor</span>
      <div style="font-size:0.75rem;color:#2d3f5c;line-height:1.6;margin-top:4px;">
        Agentic business risk intelligence powered by five specialized AI agents.
      </div>
    </div>""", unsafe_allow_html=True)

    st.markdown('<span class="sb-label" style="margin-top:1.5rem;display:block;">Sample Cases</span>', unsafe_allow_html=True)
    sample = st.selectbox("sample", ["-- select a demo case --"] + list(SAMPLES.keys()), label_visibility="collapsed")

    st.markdown('<span class="sb-label" style="margin-top:1.5rem;display:block;">Agent Pipeline</span>', unsafe_allow_html=True)
    for agent, icon in [
        ("Financial Risk Agent", "\U0001f4b0"),
        ("Compliance Agent",     "\u2696\ufe0f"),
        ("Operations Agent",     "\u2699\ufe0f"),
        ("Cyber / Data Agent",   "\U0001f510"),
        ("Exec Summary Agent",   "\U0001f4cb"),
    ]:
        st.markdown(
            f'<div class="sb-agent"><span class="sb-dot"></span>{icon} {agent}</div>',
            unsafe_allow_html=True
        )

    st.markdown("""
    <div class="byline-box">
      <div style="font-size:0.68rem;color:#2d3f5c;letter-spacing:0.5px;text-transform:uppercase;font-weight:700;">Built by</div>
      <div style="font-size:1rem;font-weight:800;color:#6366f1;margin-top:2px;">Brahma Naidu</div>
      <div style="font-size:0.7rem;color:#2d3f5c;margin-top:3px;">AI Risk Assessor &middot; v1.0 &middot; Anthropic Claude</div>
    </div>""", unsafe_allow_html=True)

# -- Hero ---------------------------------------------------------------------
st.markdown("""
<div class="hero-wrap">
  <div style="display:flex;align-items:flex-start;gap:1.5rem;flex-wrap:wrap;">
    <div style="font-size:3.2rem;line-height:1;filter:drop-shadow(0 0 20px rgba(99,102,241,0.5));">&#x1F6E1;&#xFE0F;</div>
    <div style="flex:1;min-width:240px;">
      <div class="hero-badge">&#x26A1; Multi-Agent Intelligence</div>
      <div class="hero-title">AI Risk Assessor</div>
      <div class="hero-subtitle">Agentic Business Risk Intelligence System</div>
      <div class="hero-meta">
        <span class="hero-pill">&#x1F916; <strong>5 Specialized Agents</strong></span>
        <span class="hero-pill" style="color:#1e2d45;">&middot;</span>
        <span class="hero-pill">&#x1F4CA; <strong>8 Risk Categories</strong></span>
        <span class="hero-pill" style="color:#1e2d45;">&middot;</span>
        <span class="hero-pill">&#x1F6E1; Built by <strong>Brahma Naidu</strong></span>
        <span class="hero-pill" style="color:#1e2d45;">&middot;</span>
        <span class="hero-pill">Powered by <strong>Anthropic Claude</strong></span>
      </div>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

# -- Tabs ---------------------------------------------------------------------
tab_assess, tab_history = st.tabs(["  \u26a1  New Assessment  ", "  \U0001f558  History  "])

CONTEXT_TYPES = ["startup", "vendor", "project", "product", "workflow", "enterprise"]
INDUSTRIES    = ["ai", "fintech", "technology", "healthcare", "ecommerce", "legal", "other"]
STAGES        = ["pre-seed", "seed", "series_a", "growth", "enterprise", "internal"]

def _safe_idx(lst, val, default=0):
    try: return lst.index(val)
    except (ValueError, TypeError): return default

# -- Assessment tab -----------------------------------------------------------
with tab_assess:
    prefill = SAMPLES.get(sample, {}) if sample != "-- select a demo case --" else {}

    with st.form("assess_form"):
        c1, c2 = st.columns(2)
        with c1:
            name = st.text_input("Entity Name", value=prefill.get("name", ""),
                placeholder="Company, product, vendor, or project")
            industry = st.selectbox("Industry", INDUSTRIES,
                index=_safe_idx(INDUSTRIES, prefill.get("industry", "ai")))
        with c2:
            context_type = st.selectbox("Assessment Type", CONTEXT_TYPES,
                index=_safe_idx(CONTEXT_TYPES, prefill.get("context_type", "startup")))
            stage = st.selectbox("Stage", STAGES,
                index=_safe_idx(STAGES, prefill.get("stage", "seed")))

        description = st.text_area("Description", value=prefill.get("description", ""), height=140,
            placeholder="Describe the business, product, vendor, or workflow in detail. More context = sharper analysis.")

        c3, c4, c5 = st.columns(3)
        with c3:
            handles_pii = st.checkbox("Handles PII / personal data", value=bool(prefill.get("handles_pii", False)))
        with c4:
            handles_payments = st.checkbox("Handles payments", value=bool(prefill.get("handles_payments", False)))
        with c5:
            team_size = st.number_input("Team size", min_value=1, max_value=100000,
                value=int(prefill.get("team_size", 10)))

        submitted = st.form_submit_button("\u26a1  Run Risk Assessment", type="primary", use_container_width=True)

    if submitted:
        if not (name or "").strip():
            st.error("Entity name is required.")
        elif not (description or "").strip():
            st.error("Description is required.")
        else:
            payload = {
                "name": name.strip(), "description": description.strip(),
                "context_type": context_type, "industry": industry,
                "additional_context": {
                    "team_size": int(team_size), "stage": stage,
                    "handles_pii": handles_pii, "handles_payments": handles_payments,
                    "primary_market": "US",
                },
            }
            with st.spinner("\U0001f916  Running multi-agent analysis — Financial \u00b7 Compliance \u00b7 Operations \u00b7 Cyber \u00b7 Executive..."):
                result, error_msg = None, None
                try:
                    resp = requests.post(f"{API_BASE}/assess", json=payload, timeout=240)
                    resp.raise_for_status()
                    result = resp.json()
                except requests.exceptions.ConnectionError:
                    error_msg = "Cannot connect to backend.\n\nStart it with:\n```\nuvicorn backend.main:app --port 8000\n```"
                except requests.exceptions.Timeout:
                    error_msg = "Request timed out (4 min). Try again."
                except requests.exceptions.HTTPError as e:
                    error_msg = f"Backend HTTP {e.response.status_code}: {e.response.text[:300]}"
                except ValueError as e:
                    error_msg = f"Could not parse JSON response: {e}"
                except Exception as e:
                    error_msg = f"Unexpected error: {e}"

            if error_msg:
                st.error(error_msg)
            elif not result:
                st.error("No response from backend.")
            else:
                status = result.get("status", "")
                rpt    = result.get("report")
                if status == "complete" and isinstance(rpt, dict):
                    st.success(f"\u2705  Assessment complete — {result.get('message', '')}")
                    render_report(rpt)
                elif status == "failed":
                    st.error(f"\u274c  Failed: {result.get('message', 'Unknown error')}")
                    with st.expander("Details"): st.json(result)
                elif isinstance(rpt, dict):
                    st.warning(f"Status: {status} — rendering available data.")
                    render_report(rpt)
                else:
                    st.error("Backend returned no report data.")
                    with st.expander("Raw response"): st.json(result)

# -- History tab --------------------------------------------------------------
with tab_history:
    if st.button("\u21bb  Refresh", type="secondary"):
        st.rerun()
    try:
        resp     = requests.get(f"{API_BASE}/history?limit=25", timeout=5)
        resp.raise_for_status()
        sessions = resp.json().get("sessions") or []
        if not sessions:
            st.markdown('<p style="color:#2d3f5c;text-align:center;padding:3rem;">No assessments yet.</p>', unsafe_allow_html=True)
        else:
            for s in sessions:
                level     = s.get("overall_level") or "N/A"
                score     = s.get("overall_score")
                score_str = f"{score:.0f}/100" if score is not None else "pending"
                status    = s.get("status", "")
                created   = (s.get("created_at") or "")[:16]
                entity    = s.get("entity_name", "Unknown")
                emoji     = LEVEL_EMOJI.get(level, "\u26aa")
                label     = f"{entity}   ·   {score_str}   ·   {emoji} {level}   ·   {status}   ·   {created}"
                with st.expander(label):
                    st.markdown(
                        f'<p style="font-size:0.8rem;color:#2d3f5c;">'
                        f'<code>{s.get("session_id","")}</code> &nbsp;&middot;&nbsp; '
                        f'{s.get("industry","?")} &nbsp;&middot;&nbsp; {s.get("context_type","?")}</p>',
                        unsafe_allow_html=True)
                    if status == "complete":
                        if st.button("Load report", key=f"ld_{s.get('session_id','')}"):
                            try:
                                r   = requests.get(f"{API_BASE}/report/{s['session_id']}", timeout=10).json()
                                rpt = r.get("report")
                                if isinstance(rpt, dict): render_report(rpt)
                                else: st.warning("Report data unavailable.")
                            except Exception as e:
                                st.error(f"Could not load: {e}")
    except requests.exceptions.ConnectionError:
        st.error("Cannot connect to backend. Run: `uvicorn backend.main:app --port 8000`")
    except Exception as e:
        st.error(f"Error: {e}")
