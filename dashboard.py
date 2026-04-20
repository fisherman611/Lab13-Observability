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
HEALTH_URL       = os.getenv("HEALTH_URL", CHAT_URL.replace("/chat", "/health"))

SLO_P95_MS  = 500
SLO_ERR_PCT = 5.0
SLO_QUALITY = 0.5
HISTORY_RETENTION_SEC = 24 * 60 * 60
TREND_WINDOWS = {"15m": 15 * 60, "30m": 30 * 60, "1h": 60 * 60, "3h": 3 * 60 * 60}

if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = []
if "thumb_feedback" not in st.session_state:
    st.session_state.thumb_feedback = []
if "regenerate_count" not in st.session_state:
    st.session_state.regenerate_count = 0
if "last_chat_input" not in st.session_state:
    st.session_state.last_chat_input = ""
if "session_id" not in st.session_state:
    st.session_state.session_id = f"s-dashboard-{int(time.time())}"
if "metrics_history" not in st.session_state:
    st.session_state.metrics_history = []

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
        "nav", ["📊 Overview", "🤖 Chatbot", "📜 Logs"],
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


# ─── Helpers ───────────────────────────────────────────────────────────────────
def fetch() -> dict:
    try:
        r = requests.get(API_URL, timeout=3)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        st.error(f"❌ Cannot reach `{API_URL}` — {e}")
        st.stop()


def fetch_health() -> dict:
    try:
        r = requests.get(HEALTH_URL, timeout=3)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        return {"ok": False, "error": str(e), "tracing_enabled": False, "incidents": {}}


def send_chat(payload: dict) -> dict:
    r = requests.post(CHAT_URL, json=payload, timeout=30)
    r.raise_for_status()
    return r.json()


def badge(ok: bool, warn: bool = False) -> str:
    if ok:   return "<span class='badge badge-ok'>● OK</span>"
    if warn: return "<span class='badge badge-warn'>● WARN</span>"
    return          "<span class='badge badge-crit'>● CRIT</span>"


def section(icon: str, title: str, status_html: str = "") -> None:
    st.markdown(
        f"<div class='section-title'>{icon} {title}&nbsp;&nbsp;{status_html}</div>",
        unsafe_allow_html=True,
    )


def append_metrics_history(data: dict) -> None:
    now = pd.Timestamp.now(tz="UTC")
    lat = data.get("latency", {})
    errs = data.get("errors", {})
    cost = data.get("cost", {})
    tok = data.get("tokens", {})
    qual = data.get("quality", {})

    point = {
        "ts": now.isoformat(),
        "latency_p95": float(lat.get("p95", 0)),
        "error_rate_pct": float(errs.get("error_rate_pct", 0)),
        "quality_proxy": float(qual.get("proxy_score_avg", 0)),
        "cost_total_usd": float(cost.get("total_usd", 0)),
        "tokens_in_total": int(tok.get("in_total", 0)),
        "tokens_out_total": int(tok.get("out_total", 0)),
        "traffic": int(data.get("traffic", 0)),
        "total_errors": int(errs.get("total_errors", 0)),
    }

    history = st.session_state.metrics_history
    if history:
        last = history[-1]
        last_ts = pd.to_datetime(last.get("ts"), utc=True, errors="coerce")
        if pd.notna(last_ts):
            same_snapshot = all(
                last.get(key) == point[key]
                for key in (
                    "latency_p95",
                    "error_rate_pct",
                    "quality_proxy",
                    "cost_total_usd",
                    "tokens_in_total",
                    "tokens_out_total",
                    "traffic",
                    "total_errors",
                )
            )
            if same_snapshot and (now - last_ts).total_seconds() < 2:
                return

    history.append(point)
    cutoff = now - pd.Timedelta(seconds=HISTORY_RETENTION_SEC)
    st.session_state.metrics_history = [
        h for h in history if pd.to_datetime(h.get("ts"), utc=True, errors="coerce") >= cutoff
    ]


def metrics_history_df(window_seconds: int) -> pd.DataFrame:
    history = st.session_state.metrics_history
    if not history:
        return pd.DataFrame()

    df = pd.DataFrame(history)
    if "ts" not in df.columns:
        return pd.DataFrame()

    df["ts"] = pd.to_datetime(df["ts"], utc=True, errors="coerce")
    df = df.dropna(subset=["ts"]).sort_values("ts")
    if df.empty:
        return df

    cutoff = pd.Timestamp.now(tz="UTC") - pd.Timedelta(seconds=window_seconds)
    return df[df["ts"] >= cutoff]


# ═══════════════════════════════════════════════════════════════════════════════
#  PAGE: Overview
# ═══════════════════════════════════════════════════════════════════════════════
def page_overview():
    data = fetch()
    append_metrics_history(data)

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
            st.dataframe(preview_df, use_container_width=True, hide_index=True)

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
                st.dataframe(pd.DataFrame(results), use_container_width=True, hide_index=True)

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

    st.markdown("---")
    section("📈", "TRENDS")
    range_col, note_col = st.columns([1, 3])
    with range_col:
        selected_window = st.select_slider(
            "Time window",
            options=list(TREND_WINDOWS.keys()),
            value="1h",
            key="overview_trend_window",
        )
    with note_col:
        st.caption("Default range is 1 hour. SLO reference lines are overlaid on latency, error rate, and quality charts.")

    trend_df = metrics_history_df(TREND_WINDOWS[selected_window])
    if len(trend_df) < 2:
        st.info("Need at least 2 snapshots to draw trends. Keep Live Mode on for a few refresh cycles.")
    else:
        trend_df = trend_df.set_index("ts")
        t1, t2, t3 = st.columns(3, gap="medium")

        with t1:
            st.caption("Latency P95 (ms)")
            latency_chart = trend_df[["latency_p95"]].copy()
            latency_chart["SLO"] = SLO_P95_MS
            st.line_chart(latency_chart, color=["#2563eb", "#ef4444"])

        with t2:
            st.caption("Error Rate (%)")
            error_chart = trend_df[["error_rate_pct"]].copy()
            error_chart["SLO"] = SLO_ERR_PCT
            st.line_chart(error_chart, color=["#ef4444", "#f59e0b"])

        with t3:
            st.caption("Quality Proxy (0-1)")
            quality_chart = trend_df[["quality_proxy"]].copy()
            quality_chart["SLO"] = SLO_QUALITY
            st.line_chart(quality_chart, color=["#22c55e", "#f59e0b"])

        t4, t5 = st.columns(2, gap="medium")
        with t4:
            st.caption("Cost Over Time (cumulative USD)")
            st.line_chart(trend_df[["cost_total_usd"]], color="#10b981")
        with t5:
            st.caption("Tokens Over Time (cumulative)")
            st.line_chart(trend_df[["tokens_in_total", "tokens_out_total"]], color=["#6366f1", "#f97316"])

    # Langfuse shortcut
    if LANGFUSE_ENABLED:
        st.markdown("---")
        st.caption(f"🔗 Detailed traces → [Langfuse Cloud]({LANGFUSE_HOST})")


# ═══════════════════════════════════════════════════════════════════════════════
#  PAGE: Chatbot
# ═══════════════════════════════════════════════════════════════════════════════
def page_chatbot():
    st.markdown("## 🤖 Chatbot Pickleball (LLM + RAG)")
    st.caption("Hỏi đáp trực tiếp và theo dõi chỉ số observability theo thời gian thực.")

    health = fetch_health()
    data = fetch()

    lat = data.get("latency", {})
    errs = data.get("errors", {})
    cost = data.get("cost", {})
    tok = data.get("tokens", {})
    qual = data.get("quality", {})

    info_left, info_right = st.columns([2, 1])
    with info_left:
        st.markdown("### Thông tin chatbot")
        st.write(
            {
                "chat_url": CHAT_URL,
                "session_id": st.session_state.session_id,
                "mục_đích": "Tư vấn mua bán pickleball, tra giá và chính sách",
            }
        )
    with info_right:
        st.markdown("### Trạng thái")
        if health.get("ok"):
            st.success("API đang hoạt động")
        else:
            st.error(f"Không truy cập được /health: {health.get('error', 'unknown error')}")
        st.write(
            {
                "tracing_enabled": health.get("tracing_enabled", False),
                "incidents": health.get("incidents", {}),
            }
        )

    # 6 nhóm chỉ số chính
    st.markdown("### Chỉ số Observability")
    c1, c2, c3 = st.columns(3)
    c1.metric("Latency P50", f"{lat.get('p50', 0):.0f} ms")
    c2.metric("Latency P95", f"{lat.get('p95', 0):.0f} ms")
    c3.metric("Latency P99", f"{lat.get('p99', 0):.0f} ms")

    c4, c5 = st.columns(2)
    c4.metric("Traffic (requests)", f"{data.get('traffic', 0):,}")
    c5.metric("QPS", f"{data.get('qps_estimate', 0):.2f}")

    c6, c7 = st.columns(2)
    c6.metric("Error rate", f"{errs.get('error_rate_pct', 0):.2f}%")
    c7.metric("Total errors", f"{errs.get('total_errors', 0)}")
    if errs.get("breakdown"):
        st.caption("Error breakdown")
        st.json(errs.get("breakdown", {}))

    c8, c9 = st.columns(2)
    c8.metric("Cost total", f"${cost.get('total_usd', 0):.4f}")
    c9.metric("Cost avg/request", f"${cost.get('avg_usd', 0):.5f}")

    c10, c11 = st.columns(2)
    c10.metric("Tokens in", f"{tok.get('in_total', 0):,}")
    c11.metric("Tokens out", f"{tok.get('out_total', 0):,}")

    thumbs_up = sum(1 for x in st.session_state.thumb_feedback if x == "up")
    thumbs_down = sum(1 for x in st.session_state.thumb_feedback if x == "down")
    total_fb = thumbs_up + thumbs_down
    helpful_rate = (thumbs_up / total_fb * 100) if total_fb else 0.0
    c12, c13, c14 = st.columns(3)
    c12.metric("Quality proxy", f"{qual.get('proxy_score_avg', 0):.3f}")
    c13.metric("Thumbs up rate", f"{helpful_rate:.1f}%")
    c14.metric("Regenerate count", st.session_state.regenerate_count)

    st.markdown("---")
    st.markdown("### Hỏi đáp trực tiếp")

    for msg in st.session_state.chat_messages:
        role = msg.get("role", "assistant")
        content = msg.get("content", "")
        with st.chat_message(role):
            st.markdown(content)
            if role == "assistant" and "meta" in msg:
                meta = msg["meta"]
                st.caption(
                    f"latency={meta.get('latency_ms', 0)}ms | "
                    f"tokens_in={meta.get('tokens_in', 0)} | "
                    f"tokens_out={meta.get('tokens_out', 0)} | "
                    f"cost=${meta.get('cost_usd', 0)} | "
                    f"quality={meta.get('quality_score', 0)}"
                )

    chat_input = st.chat_input("Nhập câu hỏi về giá, sản phẩm, bảo hành, đổi trả...")
    if chat_input:
        st.session_state.last_chat_input = chat_input
        st.session_state.chat_messages.append({"role": "user", "content": chat_input})
        try:
            payload = {
                "user_id": "u_dashboard",
                "session_id": st.session_state.session_id,
                "feature": "qa",
                "message": chat_input,
            }
            answer = send_chat(payload)
            st.session_state.chat_messages.append(
                {
                    "role": "assistant",
                    "content": answer.get("answer", "Không có phản hồi."),
                    "meta": {
                        "latency_ms": answer.get("latency_ms", 0),
                        "tokens_in": answer.get("tokens_in", 0),
                        "tokens_out": answer.get("tokens_out", 0),
                        "cost_usd": answer.get("cost_usd", 0.0),
                        "quality_score": answer.get("quality_score", 0.0),
                    },
                }
            )
            st.rerun()
        except Exception as e:
            st.error(f"Gọi chatbot thất bại: {e}")

    fb_col1, fb_col2, fb_col3 = st.columns([1, 1, 2])
    if fb_col1.button("👍 Hữu ích"):
        st.session_state.thumb_feedback.append("up")
        st.success("Đã ghi nhận đánh giá tích cực")
    if fb_col2.button("👎 Chưa tốt"):
        st.session_state.thumb_feedback.append("down")
        st.warning("Đã ghi nhận đánh giá cần cải thiện")
    if fb_col3.button("🔁 Regenerate câu trả lời gần nhất"):
        if not st.session_state.last_chat_input:
            st.info("Chưa có câu hỏi gần nhất để tạo lại.")
        else:
            st.session_state.regenerate_count += 1
            try:
                payload = {
                    "user_id": "u_dashboard",
                    "session_id": st.session_state.session_id,
                    "feature": "qa",
                    "message": st.session_state.last_chat_input,
                }
                answer = send_chat(payload)
                st.session_state.chat_messages.append(
                    {
                        "role": "assistant",
                        "content": answer.get("answer", "Không có phản hồi."),
                        "meta": {
                            "latency_ms": answer.get("latency_ms", 0),
                            "tokens_in": answer.get("tokens_in", 0),
                            "tokens_out": answer.get("tokens_out", 0),
                            "cost_usd": answer.get("cost_usd", 0.0),
                            "quality_score": answer.get("quality_score", 0.0),
                        },
                    }
                )
                st.rerun()
            except Exception as e:
                st.error(f"Regenerate thất bại: {e}")


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
        use_container_width=True,
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
elif page == "🤖 Chatbot":
    page_chatbot()
else:
    page_logs()

# ─── Auto-refresh ──────────────────────────────────────────────────────────────
if auto_refresh:
    time.sleep(refresh_rate)
    st.rerun()
