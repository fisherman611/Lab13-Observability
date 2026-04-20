"""
AI Observability Dashboard — Monitoring Style
Nguồn dữ liệu: GET /metrics (app/metrics.py)
Log: data/logs.jsonl
Tracing: Langfuse Cloud
"""
from __future__ import annotations

import json
import os
import time

import pandas as pd
import requests
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

# ─── Config ────────────────────────────────────────────────────────────────────
API_URL          = os.getenv("API_URL",  "http://localhost:8000/metrics")
CHAT_URL         = os.getenv("CHAT_URL", "http://localhost:8000/chat")
LOG_FILE         = os.getenv("LOG_PATH", "data/logs.jsonl")
LANGFUSE_HOST    = os.getenv("LANGFUSE_HOST", "https://us.cloud.langfuse.com")
LANGFUSE_ENABLED = bool(os.getenv("LANGFUSE_PUBLIC_KEY", ""))

SLO_P95_MS  = 500
SLO_ERR_PCT = 5.0
SLO_QUALITY = 0.5

# ─── Page setup ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AI Observability",
    layout="wide",
    page_icon="📡",
    initial_sidebar_state="expanded",
)

# ─── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;600&display=swap');

/* ═══ Base ═══ */
*, *::before, *::after { box-sizing: border-box; }
html, body {
    font-family: 'Inter', system-ui, sans-serif;
    background: #f0f2f5;
    color: #1c1e26;
}
[data-testid="stAppViewContainer"]    { background: #f0f2f5; }
[data-testid="stMain"]                { background: #f0f2f5; }
[data-testid="stMainBlockContainer"]  { background: #f0f2f5; padding-top: 1.2rem !important; }

/* ═══ Sidebar — dark Grafana style ═══ */
[data-testid="stSidebar"] {
    background: #1b1e2b !important;
    border-right: 1px solid #2c2f40;
    min-width: 220px !important;
}
[data-testid="stSidebar"] * {
    color: #b8bec9 !important;
    font-size: 0.85rem;
}
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3 { color: #e2e5ef !important; }
[data-testid="stSidebar"] .stRadio label  { color: #b8bec9 !important; }
[data-testid="stSidebar"] .stSlider label { color: #b8bec9 !important; }
[data-testid="stSidebar"] hr { border-color: #2c2f40 !important; }

/* ═══ Metric cards ═══ */
[data-testid="stMetric"] {
    background: #ffffff;
    border: 1px solid #e4e6f0;
    border-top: 3px solid #4a90d9;
    border-radius: 6px;
    padding: 14px 18px !important;
    box-shadow: 0 1px 3px rgba(0,0,0,0.06);
    transition: box-shadow .2s;
}
[data-testid="stMetric"]:hover {
    box-shadow: 0 4px 12px rgba(0,0,0,0.10);
}
[data-testid="stMetricLabel"] p {
    font-size: 0.68rem !important;
    font-weight: 600 !important;
    text-transform: uppercase;
    letter-spacing: .07em;
    color: #6b7280 !important;
    margin-bottom: 2px;
}
[data-testid="stMetricValue"] {
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 1.55rem !important;
    font-weight: 600 !important;
    color: #111827 !important;
    line-height: 1.2 !important;
}
[data-testid="stMetricDelta"] {
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.75rem !important;
}

/* ═══ Section title ═══ */
.section-title {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 0.7rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: .1em;
    color: #374151;
    padding: 6px 0 10px 0;
    border-bottom: 1px solid #e4e6f0;
    margin-bottom: 12px;
}

/* ═══ Status badges ═══ */
.badge {
    display: inline-block;
    border-radius: 4px;
    padding: 2px 10px;
    font-size: .7rem;
    font-weight: 700;
    letter-spacing: .04em;
    text-transform: uppercase;
    vertical-align: middle;
}
.badge-ok   { background:#dcfce7; color:#15803d; border:1px solid #bbf7d0; }
.badge-warn { background:#fef9c3; color:#a16207; border:1px solid #fde68a; }
.badge-crit { background:#fee2e2; color:#b91c1c; border:1px solid #fca5a5; }

/* ═══ Status bar top ═══ */
.status-bar {
    display: flex;
    align-items: center;
    gap: 20px;
    background: #1b1e2b;
    border-radius: 6px;
    padding: 8px 18px;
    margin-bottom: 18px;
    font-size: 0.75rem;
    color: #9ca3af;
}
.status-bar .dot { width:8px; height:8px; border-radius:50%; display:inline-block; margin-right:5px; }
.dot-green  { background:#22c55e; box-shadow:0 0 6px #22c55e88; }
.dot-yellow { background:#eab308; }
.dot-red    { background:#ef4444; box-shadow:0 0 6px #ef444488; }
.status-bar strong { color: #e2e5ef; }

/* ═══ Panel card wrapper ═══ */
.panel-card {
    background: #ffffff;
    border: 1px solid #e4e6f0;
    border-radius: 6px;
    padding: 16px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    margin-bottom: 8px;
}

/* ═══ Expander ═══ */
[data-testid="stExpander"] {
    background: #ffffff !important;
    border: 1px solid #e4e6f0 !important;
    border-radius: 6px !important;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04) !important;
}

/* ═══ Buttons ═══ */
[data-testid="stBaseButton-primary"] {
    background: #2563eb !important;
    border-radius: 5px !important;
    border: none !important;
    color: #fff !important;
    font-weight: 600 !important;
    font-size: 0.8rem !important;
}
[data-testid="stBaseButton-secondary"] {
    background: #ffffff !important;
    border: 1px solid #d1d5db !important;
    border-radius: 5px !important;
    color: #374151 !important;
    font-size: 0.8rem !important;
}

/* ═══ Text input ═══ */
[data-testid="stTextInput"] input {
    background: #f9fafb;
    border: 1px solid #d1d5db;
    border-radius: 5px;
    font-size: 0.85rem;
    color: #111827;
    padding: 8px 12px;
}

/* ═══ Divider ═══ */
hr { border-color: #e4e6f0 !important; margin: 1rem 0 !important; }

/* ═══ Links ═══ */
a { color: #2563eb !important; text-decoration: none; }
a:hover { text-decoration: underline; }

/* ═══ Caption / caption text ═══ */
[data-testid="stCaptionContainer"] p {
    color: #6b7280 !important;
    font-size: 0.75rem !important;
}

/* ═══ Chart ═══ */
[data-testid="stArrowVegaLiteChart"] { border-radius: 6px; overflow: hidden; }
</style>
""", unsafe_allow_html=True)


# ─── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 📡 AI Observability")
    st.markdown("---")
    page = st.radio(
        "nav", ["📊 Overview", "📜 Logs"],
        label_visibility="collapsed"
    )
    st.markdown("---")
    st.markdown("**SETTINGS**")
    auto_refresh = st.toggle("Live Mode", value=True)
    refresh_rate = st.select_slider("Interval", [5, 10, 15, 30, 60], value=10)
    st.caption(f"Refreshing every {refresh_rate}s")
    st.markdown("---")
    st.markdown("**SLO TARGETS**")
    st.caption(f"P95 Latency ≤ {SLO_P95_MS} ms")
    st.caption(f"Error Rate  ≤ {SLO_ERR_PCT}%")
    st.caption(f"Quality     ≥ {SLO_QUALITY}")
    st.markdown("---")
    st.markdown("**INTEGRATIONS**")
    if LANGFUSE_ENABLED:
        st.markdown(f"[🔗 Open Langfuse]({LANGFUSE_HOST})")
        st.markdown("<span class='badge badge-ok'>Tracing ON</span>", unsafe_allow_html=True)
    else:
        st.markdown("<span class='badge badge-warn'>Tracing OFF</span>", unsafe_allow_html=True)
    st.markdown(f"[🔗 API Endpoint]({API_URL})")

    st.markdown("---")
    st.markdown("**🧪 INCIDENT INJECTION**")
    try:
        base = API_URL.replace("/metrics", "")
        status_res = requests.get(f"{base}/incidents/status", timeout=2)
        if status_res.ok:
            incidents_data = status_res.json()
            for name, config in incidents_data.items():
                is_on = config.get("enabled", False)
                if st.toggle(f"Inject {name}", value=is_on, key=f"tg_{name}") != is_on:
                    toggle_incident(name, not is_on)
                if is_on:
                    st.caption(f"⚠️ {config.get('description', '')}")
    except:
        st.caption("Cannot load incidents status")


# ─── Helpers ───────────────────────────────────────────────────────────────────
def fetch() -> dict:
    try:
        r = requests.get(API_URL, timeout=3)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        st.error(f"❌ Cannot reach `{API_URL}` — {e}")
        st.stop()


def badge(ok: bool, warn: bool = False) -> str:
    if ok:   return "<span class='badge badge-ok'>● OK</span>"
    if warn: return "<span class='badge badge-warn'>● WARN</span>"
    return          "<span class='badge badge-crit'>● CRIT</span>"


def section(icon: str, title: str, status_html: str = "") -> None:
    st.markdown(
        f"<div class='section-title'>{icon} {title}&nbsp;&nbsp;{status_html}</div>",
        unsafe_allow_html=True,
    )

def toggle_incident(name: str, enable: bool):
    base = API_URL.replace("/metrics", "")
    endpoint = f"{base}/incidents/{name}/{'enable' if enable else 'disable'}"
    try:
        r = requests.post(endpoint, timeout=3)
        if r.ok:
            st.toast(f"✅ Incident {name} {'Enabled' if enable else 'Disabled'}")
            time.sleep(0.5)
            st.rerun()
    except Exception as e:
        st.error(f"Failed to toggle {name}: {e}")


# ═══════════════════════════════════════════════════════════════════════════════
#  PAGE: Overview
# ═══════════════════════════════════════════════════════════════════════════════
def page_overview():
    data = fetch()

    lat   = data.get("latency", {})
    errs  = data.get("errors",  {})
    cost  = data.get("cost",    {})
    tok   = data.get("tokens",  {})
    qual  = data.get("quality", {})

    p95      = lat.get("p95", 0)
    err_pct  = errs.get("error_rate_pct", 0)
    score    = qual.get("proxy_score_avg", 0.0)
    traffic  = data.get("traffic", 0)
    qps      = data.get("qps_estimate", 0.0)

    ok_lat  = p95     <= SLO_P95_MS
    ok_err  = err_pct <= SLO_ERR_PCT
    ok_qual = score   >= SLO_QUALITY
    system_ok = ok_lat and ok_err and ok_qual

    # ─── Top status bar ────────────────────────────────────────────────────────
    sys_dot   = "dot-green" if system_ok else "dot-red"
    sys_label = "All systems operational" if system_ok else "Degraded — check panels below"
    lat_dot   = "dot-green" if ok_lat else "dot-red"
    err_dot   = "dot-green" if ok_err else "dot-red"
    q_dot     = "dot-green" if ok_qual else ("dot-yellow" if score >= 0.3 else "dot-red")

    st.markdown(f"""
    <div class="status-bar">
        <span><span class="dot {sys_dot}"></span><strong>System</strong>&nbsp;{sys_label}</span>
        <span style="margin-left:auto;display:flex;gap:18px">
            <span><span class="dot {lat_dot}"></span>Latency</span>
            <span><span class="dot {err_dot}"></span>Errors</span>
            <span><span class="dot {q_dot}"></span>Quality</span>
            <span style="color:#6b7280">⏱ {time.strftime('%H:%M:%S')}</span>
        </span>
    </div>
    """, unsafe_allow_html=True)

    # ─── Batch runner ──────────────────────────────────────────────────────────
    SAMPLE_FILE = "data/sample_queries.jsonl"
    with st.expander("⚡ Run Sample Queries", expanded=False):
        if not os.path.exists(SAMPLE_FILE):
            st.warning(f"File `{SAMPLE_FILE}` not found.")
        else:
            queries = []
            with open(SAMPLE_FILE, "r", encoding="utf-8") as f:
                for l in f:
                    if l.strip():
                        queries.append(json.loads(l))

            st.caption(f"Loaded **{len(queries)}** queries from `{SAMPLE_FILE}`")

            # Preview table
            preview_df = pd.DataFrame(queries)[["user_id", "feature", "message"]]
            preview_df["message"] = preview_df["message"].str[:60] + "…"
            st.dataframe(preview_df, width="stretch", hide_index=True)

            col_btn, col_status = st.columns([2, 5])
            if col_btn.button("▶ Send All Queries", type="primary"):
                progress = st.progress(0, text="Sending…")
                results  = []
                for i, q in enumerate(queries):
                    try:
                        res = requests.post(CHAT_URL, json=q, timeout=20)
                        if res.ok:
                            d = res.json()
                            results.append({
                                "user_id":    q.get("user_id"),
                                "feature":    q.get("feature"),
                                "status":     "✅ OK",
                                "latency_ms": d.get("latency_ms", "?"),
                                "tokens_in":  d.get("tokens_in", 0),
                                "tokens_out": d.get("tokens_out", 0),
                                "cost_usd":   d.get("cost_usd", 0),
                            })
                        else:
                            results.append({"user_id": q.get("user_id"), "feature": q.get("feature"),
                                            "status": f"❌ HTTP {res.status_code}", "latency_ms": "-"})
                    except Exception as ex:
                        results.append({"user_id": q.get("user_id"), "feature": q.get("feature"),
                                        "status": f"❌ {ex}", "latency_ms": "-"})
                    progress.progress((i + 1) / len(queries), text=f"Done {i+1}/{len(queries)}")

                progress.empty()
                st.success(f"Finished {len(results)} requests — metrics updated, refresh to see changes.")
                st.dataframe(pd.DataFrame(results), width="stretch", hide_index=True)

    # ─── Row 1: 3 panels ───────────────────────────────────────────────────────
    col1, col2, col3 = st.columns(3, gap="medium")

    with col1:
        section("⏱", "LATENCY", badge(ok_lat, p95 <= SLO_P95_MS * 1.5))
        la, lb, lc = st.columns(3)
        la.metric("P50",  f"{lat.get('p50', 0):.0f} ms")
        lb.metric("P95",  f"{p95:.0f} ms")
        lc.metric("P99",  f"{lat.get('p99', 0):.0f} ms")
        lb.caption(f"SLO ≤ {SLO_P95_MS} ms")

    with col2:
        section("🌐", "TRAFFIC")
        ta, tb = st.columns(2)
        ta.metric("Requests", f"{traffic:,}")
        tb.metric("QPS", f"{qps:.2f}")

    with col3:
        section("🔥", "ERRORS", badge(ok_err, err_pct <= SLO_ERR_PCT * 2))
        ea, eb = st.columns(2)
        ea.metric("Count",     errs.get("total_errors", 0))
        eb.metric("Rate",      f"{err_pct:.2f}%")
        eb.caption(f"SLO ≤ {SLO_ERR_PCT}%")
        bkd = errs.get("breakdown", {})
        if bkd:
            for k, v in bkd.items():
                st.caption(f"▸ `{k}` — {v}")

    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

    # ─── Row 2: 3 panels ───────────────────────────────────────────────────────
    col4, col5, col6 = st.columns(3, gap="medium")

    with col4:
        section("💸", "COST (USD)")
        ca, cb = st.columns(2)
        ca.metric("Total",   f"${cost.get('total_usd', 0):.4f}")
        cb.metric("Avg/req", f"${cost.get('avg_usd', 0):.5f}")

    with col5:
        section("📦", "TOKENS")
        ta2, tb2 = st.columns(2)
        ta2.metric("Input",  f"{tok.get('in_total',  0):,}")
        tb2.metric("Output", f"{tok.get('out_total', 0):,}")

    with col6:
        section("⭐", "QUALITY", badge(ok_qual, score >= 0.3))
        st.metric("Avg Score", f"{score:.3f}")
        bar = max(0.0, min(1.0, score))
        clr = "#22c55e" if bar >= SLO_QUALITY else "#eab308" if bar >= 0.3 else "#ef4444"
        st.markdown(f"""
        <div style="background:#f3f4f6;border-radius:4px;height:8px;margin-top:4px">
          <div style="background:{clr};width:{int(bar*100)}%;height:8px;border-radius:4px;transition:width .4s"></div>
        </div>
        <div style="font-family:'JetBrains Mono',mono;font-size:.7rem;color:#6b7280;margin-top:4px">{int(bar*100)}% · SLO ≥ {int(SLO_QUALITY*100)}%</div>
        """, unsafe_allow_html=True)

    # Langfuse shortcut
    if LANGFUSE_ENABLED:
        st.markdown("---")
        st.caption(f"🔗 Detailed traces → [Langfuse Cloud]({LANGFUSE_HOST})")


# ═══════════════════════════════════════════════════════════════════════════════
#  PAGE: Logs
# ═══════════════════════════════════════════════════════════════════════════════
def page_logs():
    st.markdown("## 📜 Log Explorer")
    st.caption(f"Source: `{LOG_FILE}`")

    ctrl1, ctrl2, ctrl3 = st.columns([2, 2, 1])
    max_rows     = ctrl1.slider("Show last N rows", 20, 500, 100, 20, label_visibility="collapsed")
    selected_lvl = ctrl2.selectbox("Level filter", ["all", "info", "warning", "error", "critical"], label_visibility="collapsed")
    if ctrl3.button("↻ Refresh", type="secondary"):
        st.rerun()

    if not os.path.exists(LOG_FILE):
        st.info(f"No log file at `{LOG_FILE}` yet — send a request from the Overview page.")
        return

    try:
        lines = []
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            for l in f:
                if l.strip():
                    lines.append(json.loads(l))
    except Exception as e:
        st.error(f"Error reading log: {e}")
        return

    if not lines:
        st.info("No log entries yet.")
        return

    lines.reverse()
    df = pd.DataFrame(lines[:max_rows])

    if selected_lvl != "all" and "level" in df.columns:
        df = df[df["level"] == selected_lvl]

    priority = ["ts", "level", "event", "latency_ms", "tokens_in", "tokens_out", "cost_usd", "error_type", "service"]
    cols = [c for c in priority if c in df.columns] + [c for c in df.columns if c not in priority]
    df = df[cols]

    st.dataframe(
        df,
        width="stretch",
        hide_index=True,
        column_config={
            "ts":         st.column_config.TextColumn("Timestamp"),
            "level":      st.column_config.TextColumn("Level",      width="small"),
            "latency_ms": st.column_config.NumberColumn("Latency",  format="%d ms"),
            "cost_usd":   st.column_config.NumberColumn("Cost",     format="$%.5f"),
            "tokens_in":  st.column_config.NumberColumn("Tok In",   format="%d"),
            "tokens_out": st.column_config.NumberColumn("Tok Out",  format="%d"),
        }
    )

    # Latency chart
    if "latency_ms" in df.columns:
        valid = df.dropna(subset=["latency_ms"]).copy()
        if not valid.empty:
            st.markdown("---")
            st.markdown("**Latency Trend**")
            if "ts" in valid.columns:
                valid["ts"] = pd.to_datetime(valid["ts"], errors="coerce")
                valid = valid.sort_values("ts").set_index("ts")
            st.line_chart(valid["latency_ms"], color="#2563eb")

    if LANGFUSE_ENABLED:
        st.markdown("---")
        st.caption(f"🔗 Full trace details on [Langfuse Cloud]({LANGFUSE_HOST})")


# ─── Router ────────────────────────────────────────────────────────────────────
if page == "📊 Overview":
    page_overview()
else:
    page_logs()

# ─── Auto-refresh ──────────────────────────────────────────────────────────────
if auto_refresh:
    time.sleep(refresh_rate)
    st.rerun()
