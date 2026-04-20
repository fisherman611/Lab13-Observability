import time
import requests
import streamlit as st
import pandas as pd
import os
import json

# Cấu hình giao diện Streamlit
st.set_page_config(
    page_title="API Observability", 
    layout="wide", 
    page_icon="🤖",
    initial_sidebar_state="expanded"
)

# Sidebar Navigation
st.sidebar.title("🧭 Điều hướng")
page = st.sidebar.radio("Chọn trang:", ["Dashboard Metrics", "Logs Explorer"])

# Settings
st.sidebar.markdown("---")
st.sidebar.header("⚙️ Cài đặt")
auto_refresh = st.sidebar.checkbox("Bật Auto-Refresh", value=True)
refresh_rate = st.sidebar.slider("Tốc độ lấy mẫu (giây)", 2, 60, 5)

API_URL = "http://localhost:8000/metrics"
CHAT_URL = "http://localhost:8000/chat"
LOG_FILE = "data/logs.jsonl"

def show_dashboard():
    st.title("🚀 AI API Metrics Dashboard")
    st.markdown("Giám sát Real-time các chỉ số: Phản hồi, Lưu lượng, Lỗi, Chi phí, Tokens và Chất lượng.")

    try:
        response = requests.get(API_URL, timeout=2)
        data = response.json()
        print(f"[{time.strftime('%H:%M:%S')}] GET /metrics -> OK")
    except Exception as e:
        st.error(f"❌ Không thể kết nối tới server tại {API_URL}")
        print(f"[{time.strftime('%H:%M:%S')}] GET /metrics -> ERROR: {e}")
        st.stop()

    # Module Gửi Traffic giả lập
    with st.expander("🧪 Test Hệ Thống (Gửi Request)", expanded=True):
        col_input, col_status = st.columns([3, 1])
        with col_input:
            user_msg = st.text_input("Nhập tin nhắn (nhấn Enter)", placeholder="Ví dụ: Hello API!", key="input_test")
            
        if user_msg:
            with st.spinner("Đang gửi request..."):
                try:
                    res = requests.post(CHAT_URL, json={
                        "user_id": "test_user", "session_id": "session_1", "feature": "chat", "message": user_msg
                    }, timeout=10)
                    if res.status_code == 200:
                        latency = res.json().get('latency_ms', 0)
                        st.success(f"✅ Thành công! ({latency}ms)")
                        print(f"[{time.strftime('%H:%M:%S')}] POST /chat -> SUCCESS! {latency}ms")
                    else:
                        st.error(f"❌ Lỗi {res.status_code}")
                except Exception as e:
                    st.error("❌ Kết nối thất bại")

    st.caption(f"Cập nhật lần cuối: {time.strftime('%H:%M:%S')}")

    # Layout Metrics
    r1_col1, r1_col2, r1_col3 = st.columns(3)
    
    with r1_col1:
        st.subheader("⏱️ 1. Latency")
        lat = data.get("latency", {})
        l1, l2, l3 = st.columns(3)
        l1.metric("P50", f"{lat.get('p50', 0):.0f}ms")
        l2.metric("P95", f"{lat.get('p95', 0):.0f}ms")
        l3.metric("P99", f"{lat.get('p99', 0):.0f}ms")

    with r1_col2:
        st.subheader("🌐 2. Traffic")
        t1, t2 = st.columns(2)
        t1.metric("Tổng Reqs", data.get("traffic", 0))
        t2.metric("Est. QPS", f"{data.get('qps_estimate', 0):.2f}")

    with r1_col3:
        st.subheader("🔥 3. Errors")
        errs = data.get("errors", {})
        e1, e2 = st.columns(2)
        e1.metric("Tổng Lỗi", errs.get("total_errors", 0))
        e2.metric("Tỉ lệ", f"{errs.get('error_rate_pct', 0):.2f}%")

    st.markdown("---")
    r2_col1, r2_col2, r2_col3 = st.columns(3)

    with r2_col1:
        st.subheader("💸 4. Cost")
        cost = data.get("cost", {})
        st.metric("Tổng Chi Phí", f"${cost.get('total_usd', 0):.4f}")

    with r2_col2:
        st.subheader("📦 5. Tokens")
        tok = data.get("tokens", {})
        tk1, tk2 = st.columns(2)
        tk1.metric("Input", f"{tok.get('in_total', 0):,}")
        tk2.metric("Output", f"{tok.get('out_total', 0):,}")

    with r2_col3:
        st.subheader("⭐ 6. Quality")
        score = data.get("quality", {}).get("proxy_score_avg", 0)
        st.metric("Avg Score", f"{score:.2f}")
        st.progress(score if 0 <= score <= 1 else 0)

def show_logs():
    st.title("📜 Logs Explorer")
    st.markdown("Xem lịch sử request và log hệ thống từ `data/logs.jsonl`.")

    if not os.path.exists(LOG_FILE):
        st.warning(f"File log `{LOG_FILE}` chưa tồn tại. Hãy gửi 1 request để tạo log.")
        return

    # Nút refresh logs thủ công
    if st.button("🔄 Làm mới Logs"):
        st.rerun()

    try:
        logs = []
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    logs.append(json.loads(line))
        
        # Đảo ngược để thấy log mới nhất trên cùng
        logs.reverse()
        
        if not logs:
            st.info("Chưa có log nào được ghi lại.")
            return

        df = pd.DataFrame(logs)
        
        # Sắp xếp lại các cột quan trọng lên đầu nếu có
        important_cols = ['ts', 'level', 'event', 'latency_ms', 'cost_usd', 'tokens_in', 'tokens_out', 'error_type']
        cols = [c for c in important_cols if c in df.columns] + [c for c in df.columns if c not in important_cols]
        df = df[cols]

        st.dataframe(df, use_container_width=True)

        # Biểu đồ đơn giản về Latency trong logs
        if 'latency_ms' in df.columns:
            st.subheader("📈 Latency Trend (từ Logs)")
            chart_data = df.dropna(subset=['latency_ms']).head(50)
            st.line_chart(chart_data.set_index('ts')['latency_ms'])

    except Exception as e:
        st.error(f"Lỗi khi đọc file log: {e}")

# Main Logic
if page == "Dashboard Metrics":
    show_dashboard()
else:
    show_logs()

# Auto Refresh logic
if auto_refresh:
    time.sleep(refresh_rate)
    st.rerun()
