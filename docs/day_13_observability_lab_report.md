# Day 13 Observability Lab Report

## 1. Team Metadata
- **GROUP_NAME**: C401-B6
- **REPO_URL**: https://github.com/fisherman611/Lab13-Observability
- **MEMBERS**:
  - Lương Hữu Thành | Role: Logging & PII
  - Vũ Như Đức | Role: Tracing & Enrichment
  - Nguyễn Tiến Thắng | Role: SLO & Alerts
  - Hoàng Văn Bắc | Role: Load Test & Dashboard
  - Trần Anh Tú | Role: Demo & Report
  - Nguyễn Như Giáp | Role: UI Integration
  - Vũ Phúc Thành | Role: LLM Test Data

---

## 2. Group Performance (Auto-Verified)
- **VALIDATE_LOGS_FINAL_SCORE**: 100/100
- **TOTAL_TRACES_COUNT**: 17
- **PII_LEAKS_FOUND**: 0

---

## 3. Technical Evidence (Group)

### 3.1 Logging & Tracing
- [EVIDENCE_CORRELATION_ID_SCREENSHOT](screenshots/EVIDENCE_CORRELATION_ID_SCREENSHOT.jpg)
- [EVIDENCE_PII_REDACTION_SCREENSHOT](screenshots/EVIDENCE_PII_REDACTION_SCREENSHOT.jpg)
- [EVIDENCE_TRACE_WATERFALL_SCREENSHOT](screenshots/EVIDENCE_TRACE_WATERFALL_SCREENSHOT.jpg)
- **TRACE_WATERFALL_EXPLANATION**: Trace được gắn ở LabAgent.run() bằng @observe(), sau đó cập nhật trace/observation qua langfuse_context.update_current_trace() và update_current_observation() (metadata gồm doc_count, query_preview, usage input/output tokens). Span đáng chú ý là nhánh RAG khi incident rag_slow bật sẽ tạo trễ 2.5s trong app/rag.py.

### 3.2 Dashboard & SLOs
- [DASHBOARD_6_PANELS_SCREENSHOT](screenshots/DASHBOARD_6_PANELS_SCREENSHOT.jpg)

**SLO_TABLE**:

| SLI | Target | Window | Current Value |
| --- | ---: | --- | ---: |
| Latency P95 | < 3000ms | 28d | 11535ms |
| Error Rate | < 2% | 28d | 0.00% |
| Cost Budget | < $2.5/day | 1d | $0.000742 |
| Quality Proxy | > 0.5 | 1h | 0.810 |
| PII Redaction | 100% | 28d | 100% |

### 3.3 Alerts & Runbook
- [ALERT_RULES_SCREENSHOT](screenshots/ALERT_RULES_SCREENSHOT.png)
- **SAMPLE_RUNBOOK_LINK**: [High latency runbook](alerts.md#1-high-latency-p95)

---

## 4. Incident Response (Group)
- **SCENARIO_NAME**: rag_slow
- **SYMPTOMS_OBSERVED**: Latency P95 tăng mạnh; request /chat phản hồi chậm rõ rệt; dashboard hiển thị tail latency vượt ngưỡng.
- **ROOT_CAUSE_PROVED_BY**: Cờ incident rag_slow được bật và hàm retrieve() trong app/rag.py gọi time.sleep(2.5), gây tăng latency theo mỗi request.
- **FIX_ACTION**: Disable incident qua endpoint /incidents/rag_slow/disable; tối ưu luồng retrieval/tool call để tránh chặn đồng bộ.
- **PREVENTIVE_MEASURE**: Giữ alert latency P95, dùng trace để tách bottleneck RAG/LLM, thêm kiểm soát timeout cho tool call.

---

## 5. Individual Contributions & Evidence

### Lương Hữu Thành
- [TASKS_COMPLETED]: Triển khai dashboard Streamlit, mở rộng UI dashboard và bổ sung hiển thị metric thực thi.
- **EVIDENCE_LINK**:
  - https://github.com/fisherman611/Lab13-Observability/commit/2e7477aee1d5a0031e0a2e0a9a67d23bf8898240
  - https://github.com/fisherman611/Lab13-Observability/commit/6d78492a9bc2123ac36c7aee0716902bcf5da76f

### Vũ Như Đức
- [TASKS_COMPLETED]: Enrich log context trong API; cập nhật module LLM/RAG và luồng test full LLM flow.
- **EVIDENCE_LINK**:
  - https://github.com/fisherman611/Lab13-Observability/commit/05c914ba73b86735eafdf0a8edc6f843d1aef103
  - https://github.com/fisherman611/Lab13-Observability/commit/f6610cb94639faeb97e02842f408ffd1cad87995

### Nguyễn Tiến Thắng
- [TASKS_COMPLETED]: Sửa middleware để chuẩn hóa correlation ID/context propagation.
- **EVIDENCE_LINK**: https://github.com/fisherman611/Lab13-Observability/commit/7c138e0b941f9fc2938f3654290a8ab5005ec4b9

### Hoàng Văn Bắc
- [TASKS_COMPLETED]: Bổ sung tracing và incident flow; cập nhật phần liên quan middleware/tracing.
- **EVIDENCE_LINK**: https://github.com/fisherman611/Lab13-Observability/commit/1c25858a13d4e04b9b4fb458d15102b7ecf52638

### Trần Anh Tú
- [TASKS_COMPLETED]: Nâng cấp PII scrubbing trong logging pipeline và cập nhật regex nhận diện dữ liệu nhạy cảm.
- **EVIDENCE_LINK**:
  - https://github.com/fisherman611/Lab13-Observability/commit/2f53497e93f7093039d62c0f14f0740f578c5ad2
  - https://github.com/fisherman611/Lab13-Observability/commit/3a9b6ceb907682ca63b158c68faf69c335d7979d

### Nguyễn Như Giáp
- [TASKS_COMPLETED]: Cải tiến UI dashboard và hoàn thiện tích hợp cuối cho lab.
- **EVIDENCE_LINK**:
  - https://github.com/fisherman611/Lab13-Observability/commit/b33609c9b65c62de92a6c32d103370ae360cc975
  - https://github.com/fisherman611/Lab13-Observability/commit/a6a35d3e67dc7fe80c6603446bb8a0eaa274fb14

### Vũ Phúc Thành
- [TASKS_COMPLETED]: Bổ sung bộ test query cho LLM (data/llm_test_queries.jsonl) phục vụ kiểm thử end-to-end.
- **EVIDENCE_LINK**: https://github.com/fisherman611/Lab13-Observability/commit/16ecfc4d782670a88c765f1725ae285a40a492e9

---

## 6. Bonus Items (Optional)
- **BONUS_COST_OPTIMIZATION**: Có cơ chế theo dõi chi phí qua cost.total_usd, cost.avg_usd ở app/metrics.py và hiển thị trên dashboard (dashboard.py), nhưng chưa có số liệu before/after được commit.
- **BONUS_AUDIT_LOGS**: Chưa có triển khai audit log tách riêng trong phiên bản hiện tại.
- **BONUS_CUSTOM_METRIC**: Có custom metric quality.proxy_score_avg, qps_estimate, breakdown error theo loại trong app/metrics.py.

