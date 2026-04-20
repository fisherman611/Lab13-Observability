# Day 13 Observability Lab Final Report

## 1. Team Metadata
- [GROUP_NAME]: 
- [REPO_URL]: 
- [MEMBERS]:
  - Member A: [Name] | Role: Logging & PII
  - Member B: [Name] | Role: Tracing & Enrichment
  - Member C: [Name] | Role: SLO & Alerts
  - Member D: [Name] | Role: Load Test & Dashboard
  - Member E: [Name] | Role: Demo & Report

---

## 2. Group Performance (Auto-Verified)
- [VALIDATE_LOGS_FINAL_SCORE]: 100/100
- [TOTAL_TRACES_COUNT]: 27
- [PII_LEAKS_FOUND]: 0

---

## 3. Technical Evidence (Group)

### 3.1 Logging & Tracing
- [EVIDENCE_CORRELATION_ID_SCREENSHOT]: [Path to image]
- [EVIDENCE_PII_REDACTION_SCREENSHOT]: [Path to image]
- [EVIDENCE_TRACE_WATERFALL_SCREENSHOT]: [Path to image]
- [TRACE_WATERFALL_EXPLANATION]: Waterfall trace cho thấy rõ sự phân tách giữa bước RAG và LLM. Khi bước RAG bị chậm, thanh ngang của `retrieve` kéo dài rõ rệt, giúp cô lập vấn đề hiệu năng ngay lập tức.

### 3.2 Dashboard & SLOs
- [DASHBOARD_6_PANELS_SCREENSHOT]: [Path to image]
- [SLO_TABLE]:
| SLI | Target | Window | Current Value |
|---|---:|---|---:|
| Latency P95 | < 3000ms | 28d | 11535ms |
| Error Rate | < 2% | 28d | 0.00% |
| Cost Budget | < $2.5/day | 1d | $0.000742 |
| Quality Proxy | > 0.5 | 1h | 0.810 |
| PII Redaction | 100% | 28d | 100% |

### 3.3 Alerts & Runbook
- [ALERT_RULES_SCREENSHOT]: [Path to image]
- [SAMPLE_RUNBOOK_LINK]: [docs/alerts.md#L11-L14]

---

## 4. Incident Response (Group)
- [SCENARIO_NAME]: rag_slow
- [SYMPTOMS_OBSERVED]: Độ trễ P99 vọt lên trên 20 giây đối với một số yêu cầu QA sau khi bật incident.
- [ROOT_CAUSE_PROVED_BY]: Trace `req-b76c30ec` cho thấy bước RAG bị chậm ~6s so với yêu cầu chuẩn `req-4827503b`.
- [FIX_ACTION]: Vô hiệu hóa kịch bản `rag_slow` từ Dashboard.
- [PREVENTIVE_MEASURE]: Thiết lập cảnh báo (Alert) P95 > 5s và cơ chế Fallback retrieval.

---

## 5. Individual Contributions & Evidence

### Member A
- [TASKS_COMPLETED]: 
- [EVIDENCE_LINK]: 

### Member B
- [TASKS_COMPLETED]: 
- [EVIDENCE_LINK]: 

### Member C
- [TASKS_COMPLETED]: 
- [EVIDENCE_LINK]: 

### Member D
- [TASKS_COMPLETED]: 
- [EVIDENCE_LINK]: 

### Member E
- [TASKS_COMPLETED]: 
- [EVIDENCE_LINK]: 

---

## 6. Bonus Items (Optional)
- [BONUS_COST_OPTIMIZATION]: Đã tối ưu Token usage bằng cách rút gọn prompt và sử dụng model Llama 3.1 8B.
- [BONUS_AUDIT_LOGS]: Hệ thống ghi nhận mọi thay đổi trạng thái incident vào file logs với level WARNING.
- [BONUS_CUSTOM_METRIC]: Quality Heuristic Score - Bộ chỉ số chấm điểm AI tự động (0-1), giúp quan sát độ chính xác của phản hồi trực quan trên Dashboard.
