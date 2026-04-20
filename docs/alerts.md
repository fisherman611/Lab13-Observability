# Alert Rules and Runbooks (Observability Lab)

## 1. High Latency P95 (Hệ thống phản hồi chậm)
- **Severity**: P2 (Nghiêm trọng - Cần xử lý sớm)
- **Trigger**: `latency_p95_ms > 5000` (Phản hồi chậm hơn 5 giây cho 95% yêu cầu).
- **Impact**: Người dùng cảm thấy ứng dụng bị treo, gây trải nghiệm tệ.
- **First Checks**:
  1. Kiểm tra **Langfuse Trace Waterfall**: Xem bước `retrieve` hay `NVIDIA LLM Call` bị dài bất thường.
  2. Truy cập Dashboard và kiểm tra xem incident `rag_slow` có đang bị bật nhầm không?
  3. Kiểm tra mạng (network) tới NVIDIA NIM API.
- **Mitigation**:
  - Nếu do `rag_slow` incident: Tắt ngay trên Dashboard.
  - Nếu do LLM chậm: Chuyển sang model nhỏ hơn (như Llama 3.1 8B thay vì 70B).
  - Áp dụng `time.sleep` ngắn hơn hoặc tối ưu hóa keyword search trong `rag.py`.

## 2. API Error Spike (Lỗi hệ thống tăng vọt)
- **Severity**: P1 (Khẩn cấp - Phải xử lý ngay)
- **Trigger**: `error_rate_pct > 5` (Hơn 5% request bị lỗi 500).
- **Impact**: Người dùng hoàn toàn không nhận được câu trả lời.
- **First Checks**:
  1. Xem Log tại `data/logs.jsonl` tìm từ khóa `request_failed` và `error_type`.
  2. Kiểm tra `tool_fail` incident trong file `data/injections.json`.
  3. Xác nhận API Key (NVIDIA hoặc Langfuse) có bị hết hạn hay 401 Unauthorized không.
- **Mitigation**:
  - Tắt incident `tool_fail` nếu đang bật.
  - Cập nhật lại API Key mới vào file `.env`.
  - Triển khai cơ chế Retry với model dự phòng.

## 3. PII Leak Detected (Rò rỉ dữ liệu nhạy cảm)
- **Severity**: P1 (Khẩn cấp - Rủi ro bảo mật cao)
- **Trigger**: `pii_leak_count > 0` trong logs quan sát.
- **Impact**: Lộ thông tin cá nhân (SĐT, Email) người dùng vào hệ thống Logs/Trace.
- **First Checks**:
  1. Kiểm tra log sự kiện `pii_leak` được bật trong file cấu hình.
  2. So sánh `message_preview` giữa input gốc và log cuối cùng.
- **Mitigation**:
  - Tắt incident `pii_leak` ngay lập tức.
  - Cập nhật lại Regex tìm kiếm PII trong `app/pii.py`.
  - Thực hiện xóa (purge) các bản logs cũ bị lộ dữ liệu nhạy cảm.

## 4. Cost Budget Spike (Chi phí tăng đột biến)
- **Severity**: P2 (Nghiêm trọng - Rủi ro tài chính)
- **Trigger**: `hourly_cost_usd > 2x_baseline` (Chi phí tăng gấp đôi bình thường).
- **First Checks**:
  1. Kiểm tra tỉ lệ Token `tokens_out/tokens_in` trên Langfuse Dashboard.
  2. Xác nhận xem incident `cost_spike` có đang được bật làm tăng ảo số lượng token không.
- **Mitigation**:
  - Giảm `max_tokens` trong cấu hình gọi LLM.
  - Sử dụng Model giá rẻ hơn cho các tác vụ đơn giản.
  - Tắt incident `cost_spike` trên Dashboard.
