# Ngày 13 — Test Reflexion + So Sánh

## 1. Vấn đề khái niệm này giải quyết

Sau khi implement Reflexion ở Ngày 12, câu hỏi quan trọng hơn không phải "cách implement" mà là "khi nào nên dùng". Bật Reflexion mặc định cho mọi task → chi phí API tăng 3–28x, latency tăng, và với task đơn giản, output có thể **tệ hơn** (answer bị rút gọn không cần thiết, hoặc retry vô nghĩa).

## 2. Định nghĩa

**Reflexion selection problem:** quyết định khi nào nên áp dụng Reflexion dựa trên đặc điểm của task — thay vì áp dụng mặc định cho mọi truy vấn.

## 3. Hiểu sâu hơn

### 4 điều kiện cần thiết để Reflexion hiệu quả (rút ra từ 6 lần A/B test)

**Điều kiện 1 — Có không gian cải thiện:**
Task phải có nhiều đáp án có thể cải thiện qua feedback. Task factual (tra giờ, tra đơn hàng, tra chính sách) chỉ có 1 đáp án đúng → Reflexion lãng phí. Minh họa: `simple_factual` tốn 3.2–4.8x token mà answer không tốt hơn.

**Điều kiện 2 — Latency không phải ưu tiên hàng đầu:**
Reflexion thêm 4–100+ giây. Chatbot real-time (cần <3s) không phù hợp. Báo cáo phân tích, tư vấn mua hàng (user chờ được) → chấp nhận được.

**Điều kiện 3 — Infrastructure layer phải đúng trước:**
Tool phải tính đúng, system prompt phải mô tả tool chính xác. Minh họa: `compute_annuity` tính sai → 97 năm → Reflexion retry → gọi lại cùng tool → vẫn 97 năm → tốn 28.5x token mà output vẫn sai. Reflexion chỉ sửa content-level, không sửa infra-level.

**Điều kiện 4 — Critique phải có đủ context:**
Nếu critique chỉ thấy `(answer, task)` mà không biết answer đến từ tool, nó sẽ đánh giá sai → trigger retry vô nghĩa. Fix: inject trace log (tool calls + observations) vào prompt critique. Minh họa: cùng answer "10:50:33", không có trace → accuracy=1 ("AI bịa giờ"), có trace → accuracy=5 ("agent gọi get_current_time").

### Quy tắc tổng quát (rule of thumb)

Dùng Reflexion khi đáp ứng ít nhất 3/4 điều kiện. Thiếu điều kiện 3 hoặc 4 → Reflexion chắc chắn thất bại, không cần thử.

### Framework phân loại task cho e-commerce agent

| Loại câu hỏi | Reflexion? | Lý do |
|---|---|---|
| Tra đơn hàng | ❌ Tắt | 1 đáp án đúng, cần nhanh, tool tra DB là đủ |
| So sánh sản phẩm | ✅ Bật | Có không gian cải thiện, high-value query, user chờ được |
| Chính sách đổi trả | ❌ Tắt | Factual từ knowledge base, bắt buộc đúng, Reflexion có thể bịa thêm |

## 4. Hậu quả nếu bỏ qua hoặc dùng sai

**Bật Reflexion mặc định:** chi phí tăng 3–28x, latency tăng, task đơn giản có thể output tệ hơn (answer bị rút gọn không cần thiết).

**Tắt Reflexion hoàn toàn:** task analytical mất cơ hội cải thiện. Ví dụ: agent so sánh sản phẩm chỉ nêu 2 điểm thay vì 5 → user không đủ thông tin quyết định → mất doanh thu.

**Không đo lường trước khi quyết định:** tin trực giác "task này có vẻ cần Reflexion" → không có data → không giải thích được cho team tại sao tốn token.

**Reflexion không sửa lỗi tính toán:** lỗi tính toán nằm ở tool layer. Reflexion chỉ cho LLM cơ hội thử approach khác, không sửa phép tính.

## 5. Vị trí trong bức tranh lớn

Ngày 12 học "cách implement Reflexion", Ngày 13 học "khi nào dùng Reflexion" → đây là bước chuyển từ **implementation skill** sang **engineering judgment**. Ngày 14 sẽ nâng thêm một tầng: viết factory pattern tự động chọn strategy phù hợp.

Nguyên tắc cốt lõi: **"Infrastructure phải đúng trước khi thêm intelligence layer. Loop chỉ khuếch đại tín hiệu đã có — input hỏng thì loop tốn token mà không cải thiện."** Áp dụng cho mọi pattern agent sau này: RAG, multi-agent, evaluation.

Pattern "đo trước khi quyết định" (A/B test) sẽ trở lại mạnh mẽ ở Phase 3 (Ngày 87+, Evaluation) — khi đó bạn sẽ build evaluation pipeline chuyên nghiệp thay vì script thủ công.

## 6. Câu hỏi để tự kiểm tra

**Lý thuyết:** Liệt kê 4 điều kiện cần thiết để Reflexion hiệu quả. Cho ví dụ cụ thể khi mỗi điều kiện bị vi phạm.

**Tình huống:** Agent viết email marketing cho sản phẩm mới. Email cần: tiêu đề hấp dẫn, mô tả sản phẩm chính xác (lấy từ database), CTA rõ ràng, tone phù hợp brand. Bạn có nên dùng Reflexion? Rubric critique sẽ có những chiều nào?

**Bẫy:** "Reflexion tốn nhiều token nhưng luôn cải thiện chất lượng, vậy chỉ cần tăng budget API là được." — Tìm 2 lỗi logic trong nhận định này.

## 7. Câu hỏi còn chưa rõ / Cần tìm hiểu thêm

- **Adaptive Reflexion:** Thay vì bật/tắt cứng, cho agent tự quyết định "có cần self-critique không?" dựa trên confidence score. Đây là hướng mở rộng nâng cao — sẽ gặp ở Phase 2+ khi học về agent với nhiều strategy.

- **Statistical significance:** 6 lần chạy cho thấy LLM output không deterministic (cùng task cho kết quả khác nhau: 28, 29, 31, 32, 97 năm). Trong production, cần chạy N lần và tính trung bình/variance. Evaluation methodology sẽ học kỹ ở Ngày 87+.

- **Annuity due vs Ordinary annuity:** Tool `compute_annuity` dùng annuity due (gửi đầu năm), công thức thủ công `(1.08^n-1)/0.08` là ordinary annuity (gửi cuối năm). Hai cách cho kết quả khác nhau (28 vs 29 năm). Cần document rõ assumption trong tool description.

- **Critique prompt engineering:** Dòng `"nếu dữ liệu đến từ tool call thì coi là chính xác"` trong prompt critique giải quyết self-evaluation bias cho tool-based answers. Nhưng nếu tool trả data sai (ví dụ API trả giá cũ), prompt này sẽ che giấu lỗi. Trade-off cần cân nhắc theo use case.

## Artifacts đã tạo/sửa

- `scripts/compare_reflexion.py` — A/B test script với TokenTracker
- `tools/basic_tools.py` — thêm `compute_annuity`, fix `calculate` hỗ trợ `**`
- `agents/react_agent.py` — thêm `tracker` parameter, fix regex Final Answer, tăng critique `max_tokens`, thêm `trace` parameter cho `self_critique`
- `notes/reflexion-comparison.md` — bảng so sánh 6 lần chạy

## Nguồn tham khảo

- Anthropic "Building Effective Agents" — section "When (and when not) to use agents"
- Dữ liệu thực nghiệm từ 6 lần A/B test trên 3 task types
