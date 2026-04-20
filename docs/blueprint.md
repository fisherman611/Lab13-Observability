# Day 13 Observability Lab Report

> **Instruction**: Fill in all sections below. This report is designed to be parsed by an automated grading assistant. Ensure all tags (e.g., `[GROUP_NAME]`) are preserved.

## 1. Team Metadata
- [GROUP_NAME]: Lab13-Observability-Team
- [REPO_URL]: https://github.com/fisherman611/Lab13-Observability
- [MEMBERS]:
  - Member A: Lương Hữu Thành | Role: Logging & PII
  - Member B: Vũ Như Đức | Role: Tracing & Enrichment
  - Member C: Nguyễn Tiến Thắng | Role: SLO & Alerts
  - Member D: Hoàng Văn Bắc | Role: Load Test & Dashboard
  - Member E: Trần Anh Tú | Role: Demo & Report
  - Member F: Nguyễn Như Giáp | Role: UI Integration
  - Member G: Vũ Phúc Thành | Role: LLM Test Data

---

## 2. Group Performance (Auto-Verified)
- [VALIDATE_LOGS_FINAL_SCORE]: N/A (không có `data/logs.jsonl` trong repo để chạy `scripts/validate_logs.py`)
- [TOTAL_TRACES_COUNT]: N/A (không có ảnh/chứng cứ trace được commit)
- [PII_LEAKS_FOUND]: N/A (chưa có tập log runtime để kiểm chứng tự động)

---

## 3. Technical Evidence (Group)

### 3.1 Logging & Tracing
- [EVIDENCE_CORRELATION_ID_SCREENSHOT]: N/A (chưa đính kèm screenshot)
- [EVIDENCE_PII_REDACTION_SCREENSHOT]: N/A (chưa đính kèm screenshot)
- [EVIDENCE_TRACE_WATERFALL_SCREENSHOT]: N/A (chưa đính kèm screenshot)
- [TRACE_WATERFALL_EXPLANATION]: Theo code, trace được gắn ở `LabAgent.run()` bằng `@observe()`, sau đó cập nhật trace/observation qua `langfuse_context.update_current_trace()` và `update_current_observation()` (metadata gồm `doc_count`, `query_preview`, usage input/output tokens). Span đáng chú ý là nhánh RAG khi incident `rag_slow` bật sẽ tạo trễ 2.5s trong `app/rag.py`.

### 3.2 Dashboard & SLOs
- [DASHBOARD_6_PANELS_SCREENSHOT]: N/A (chưa đính kèm screenshot)
- [SLO_TABLE]:
| SLI | Target | Window | Current Value |
|---|---:|---|---:|
| Latency P95 | < 3000ms | 28d | N/A |
| Error Rate | < 2% | 28d | N/A |
| Cost Budget | < $2.5/day | 1d | N/A |

### 3.3 Alerts & Runbook
- [ALERT_RULES_SCREENSHOT]: N/A (chưa đính kèm screenshot)
- [SAMPLE_RUNBOOK_LINK]: [docs/alerts.md#1-high-latency-p95]

---

## 4. Incident Response (Group)
- [SCENARIO_NAME]: rag_slow
- [SYMPTOMS_OBSERVED]: Latency P95 tăng mạnh; request `/chat` phản hồi chậm rõ rệt; dashboard hiển thị tail latency vượt ngưỡng.
- [ROOT_CAUSE_PROVED_BY]: Cờ incident `rag_slow` được bật và hàm `retrieve()` trong `app/rag.py` gọi `time.sleep(2.5)`, gây tăng latency theo mỗi request.
- [FIX_ACTION]: Disable incident qua endpoint `/incidents/rag_slow/disable`; tối ưu luồng retrieval/tool call để tránh chặn đồng bộ.
- [PREVENTIVE_MEASURE]: Giữ alert latency P95, dùng trace để tách bottleneck RAG/LLM, thêm kiểm soát timeout cho tool call.

---

## 5. Individual Contributions & Evidence

### Lương Hữu Thành
- [TASKS_COMPLETED]: Triển khai dashboard Streamlit, mở rộng UI dashboard và bổ sung hiển thị metric thực thi.
- [EVIDENCE_LINK]: https://github.com/fisherman611/Lab13-Observability/commit/2e7477a ; https://github.com/fisherman611/Lab13-Observability/commit/6d78492

### Vũ Như Đức
- [TASKS_COMPLETED]: Enrich log context trong API; cập nhật module LLM/RAG và luồng test full LLM flow.
- [EVIDENCE_LINK]: https://github.com/fisherman611/Lab13-Observability/commit/05c914b ; https://github.com/fisherman611/Lab13-Observability/commit/f6610cb

### Nguyễn Tiến Thắng
- [TASKS_COMPLETED]: Sửa middleware để chuẩn hóa correlation ID/context propagation.
- [EVIDENCE_LINK]: https://github.com/fisherman611/Lab13-Observability/commit/7c138e0

### Hoàng Văn Bắc
- [TASKS_COMPLETED]: Bổ sung tracing và incident flow; cập nhật phần liên quan middleware/tracing.
- [EVIDENCE_LINK]: https://github.com/fisherman611/Lab13-Observability/commit/1c25858

### Trần Anh Tú
- [TASKS_COMPLETED]: Nâng cấp PII scrubbing trong logging pipeline và cập nhật regex nhận diện dữ liệu nhạy cảm.
- [EVIDENCE_LINK]: https://github.com/fisherman611/Lab13-Observability/commit/2f53497 ; https://github.com/fisherman611/Lab13-Observability/commit/3a9b6ce

### Nguyễn Như Giáp
- [TASKS_COMPLETED]: Cải tiến UI dashboard và hoàn thiện tích hợp cuối cho lab.
- [EVIDENCE_LINK]: https://github.com/fisherman611/Lab13-Observability/commit/b33609c ; https://github.com/fisherman611/Lab13-Observability/commit/a6a35d3

### Vũ Phúc Thành
- [TASKS_COMPLETED]: Bổ sung bộ test query cho LLM (`data/llm_test_queries.jsonl`) phục vụ kiểm thử end-to-end.
- [EVIDENCE_LINK]: https://github.com/fisherman611/Lab13-Observability/commit/16ecfc4

---

## 6. Bonus Items (Optional)
- [BONUS_COST_OPTIMIZATION]: Có cơ chế theo dõi chi phí qua `cost.total_usd`, `cost.avg_usd` ở `app/metrics.py` và hiển thị trên dashboard (`dashboard.py`), nhưng chưa có số liệu before/after được commit.
- [BONUS_AUDIT_LOGS]: Chưa có triển khai audit log tách riêng trong phiên bản hiện tại.
- [BONUS_CUSTOM_METRIC]: Có custom metric `quality.proxy_score_avg`, `qps_estimate`, breakdown error theo loại trong `app/metrics.py`.
