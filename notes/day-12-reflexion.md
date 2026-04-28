# Ngày 12 — Implement Reflexion

## 1. Vấn đề khái niệm này giải quyết

Khi build AI Agent, agent luôn tự tin rằng câu trả lời đầu tiên của mình đã đủ tốt — kể cả khi nó nông, thiếu ý, hoặc chung chung. Không có cơ chế nào để agent tự nhận ra "câu trả lời này chưa đủ chất lượng" trước khi trả về cho user, dẫn tới user phải prompt lại nhiều lần hoặc nhận output kém chất lượng.

## 2. Định nghĩa

**Reflexion** = sau khi agent sinh ra câu trả lời, gọi LLM thêm một lần nữa để tự chấm điểm câu trả lời theo tiêu chí cụ thể; nếu điểm thấp, agent viết lại với feedback đính kèm — lặp đến khi đạt ngưỡng hoặc hết `max_retries`.

## 3. Hiểu sâu hơn

**Cơ chế 4 bước:** (1) ReAct sinh answer lần đầu, (2) gọi LLM lần hai để self-critique theo rubric nhiều chiều (completeness, accuracy, clarity), (3) nếu mọi chiều ≥ ngưỡng → break, (4) nếu không → nối feedback vào task → chạy lại ReAct → quay lại bước 2.

**Rubric phải tách nhiều chiều, không gộp 1 điểm tổng:** Nếu chỉ chấm 1 số duy nhất, LLM có bias chọn 3-4 (giống học sinh tự chấm bài), và điểm cao ở chiều này có thể "bù" cho chiều yếu khi tính trung bình. Khi tách 3 chiều và check `all(score >= threshold)`, không chiều nào có thể bù cho chiều khác — buộc phải sửa đúng chỗ yếu.

**Hai stopping condition độc lập, bắt buộc cả hai:** (a) tất cả điểm đạt ngưỡng → câu trả lời đủ tốt; (b) hết `max_retries` → tránh infinite loop. Thiếu một trong hai → hoặc dừng quá sớm, hoặc loop tốn token vô hạn.

**Verbal feedback vs gradient updates:** Reflexion dùng feedback bằng chữ inject vào prompt — không cần dataset, không cần GPU training, học ngay trong session. Đánh đổi: feedback không persist qua session khác (session mới thì agent lại mắc lỗi cũ), không thay đổi khả năng nền tảng của model, và bị giới hạn bởi context window. Production thường kết hợp: dùng Reflexion thu thập failure cases → fine-tune sau.

**Self-critique có cost ẩn:** Worst case với `max_retries=2` = 3× ReAct + 2× critique = 5 lần gọi LLM. Latency có thể lên 5-10 giây — không phù hợp cho real-time UX (chat support cần <3 giây).

**Các cơ chế thay thế Reflexion khi latency critical:** Khi không thể chờ critique runtime, đảm bảo chất lượng phải dịch chuyển sang **input và prompt**, không phải output. Năm cơ chế chính: (1) **Prompt engineering mạnh** — few-shot examples + strict output format, rẻ nhất, đủ cho 80% use case; (2) **Offline evaluation** — log response rồi critique batch ban đêm, user không chờ nhưng vẫn theo dõi được chất lượng; (3) **RAG** — cải thiện input bằng cách tìm tài liệu liên quan trước khi trả lời, có ground truth thật thay vì tự critique (Tuần 6-9); (4) **Escalation logic** — câu hỏi khó hoặc agent không confident → chuyển cho con người (Tuần 13); (5) **Streaming response** — không giảm tổng thời gian nhưng UX cảm giác nhanh hơn vì user thấy chữ xuất hiện dần. **Nguyên tắc tổng quát:** latency-critical → chất lượng đảm bảo ở INPUT (prompt, RAG); latency-tolerant → có thể dùng OUTPUT critique (Reflexion).

**Self-critique có thể sai:** Critique cũng là LLM, không phải oracle. Nếu answer đầu vào bị cụt hoặc context kém, critique chấm sai → retry vô ích. Phải có `try/except` quanh `json.loads()` và fallback hành vi khi critique crash.

## 4. Hậu quả nếu bỏ qua hoặc dùng sai

**Nếu không dùng Reflexion khi cần:** Agent trả lời nông, user phải prompt lại 3-4 lần — ví dụ hỏi "phân tích ưu nhược điểm X" → agent trả 2 dòng mỗi mục, không ai dùng được trong báo cáo thực tế.

**Nếu dùng rubric 1 chiều:** Câu trả lời sai sự thật nhưng viết mượt được chấm 3.5/5 → pass ngưỡng → output sai vẫn ra production. Đây chính là "average out trap".

**Nếu critique không nhận `task` gốc làm input:** Critique chỉ thấy answer rời ngữ cảnh → không thể đo completeness chính xác. Ví dụ: task yêu cầu "liệt kê 5 framework", answer đưa 3 framework — critique không biết yêu cầu là 5 → chấm 4/5 thay vì 2/5. Critique luôn cần cả `task` lẫn `answer` để có ground truth so sánh.

**Nếu thiếu `max_retries`:** Khi rubric quá khắt khe, agent loop vô hạn — bill API tăng, request bị treo.

**Nếu dùng Reflexion sai context (latency-critical):** Chat support cần response <3 giây nhưng Reflexion ngốn 5-10 giây → UX hỏng → khách hàng bỏ.

**Bài học từ output thực chạy hôm nay:** Khi answer bị cắt do `max_tokens` thấp, retry 3 lần với feedback **không cải thiện** — vì vấn đề ở tầng infrastructure, không phải tầng nội dung. Reflexion chỉ sửa được lỗi content-level, không sửa được lỗi infra-level. Tốn 5× token mà output vẫn cụt.

## 5. Vị trí trong bức tranh lớn

Reflexion là pattern **xây trên nền ReAct** (Ngày 8-9): `run_with_reflexion()` gọi `run_react_agent()` bên trong, bọc thêm vòng lặp critique bên ngoài. Đây cũng là lần đầu tiên thấy LLM đóng **2 vai trong cùng 1 agent**: vai executor (trả lời) và vai evaluator (chấm điểm) — khái niệm này sẽ mở rộng ở Tuần 12 (Orchestrator-Worker).

Cùng nguyên tắc "code là safety net độc lập với prompt" từ Ngày 9: `max_retries` là safety net ở code, rubric là safety net ở prompt — hai lớp độc lập.

Nguyên tắc cốt lõi rút ra: **infrastructure phải đúng trước khi thêm intelligence layer**. Loop chỉ khuếch đại tín hiệu đã có — input hỏng thì loop tốn token mà không cải thiện.

**Checklist 4 câu khi review code Agent dùng nhiều LLM call** (rút ra từ Câu 3 Knowledge Check, áp dụng cho Reflexion và mọi pattern Agent sau này): (1) **Stopping condition** có đủ không? — `max_retries`, `max_iterations`, early-exit; (2) **Parsing output LLM** có defensive không? — `try/except`, fallback khi JSON crash, strip markdown fence; (3) **Context truyền cho LLM** có đủ không? — task gốc, history, feedback, không thiếu input để LLM đánh giá đúng; (4) **Rubric đánh giá** có cụ thể & nhiều chiều không? — không gộp 1 điểm tổng, không dùng tiêu chí mơ hồ "tốt/xấu". Áp dụng checklist này khi tự review code của mình ở các ngày sau.

## 6. Câu hỏi để tự kiểm tra

**Lý thuyết:** Tại sao rubric self-critique phải tách nhiều chiều và check `all(score >= threshold)` thay vì check điểm trung bình ≥ threshold? Cho 1 ví dụ cụ thể về điểm số mà cách check khác nhau cho 2 kết quả khác nhau.

**Tình huống:** Bạn đang build AI Agent viết báo cáo phân tích tài chính, mỗi báo cáo ~3000 từ, không yêu cầu real-time (user chờ vài phút được). Agent thường viết thiếu phần "rủi ro" trong báo cáo. Bạn có nên dùng Reflexion không? Nếu có, rubric của bạn sẽ có những chiều nào? Nếu không, bạn dùng cơ chế gì thay thế?

## 7. Câu hỏi còn chưa rõ

- **Early-exit khi Reflexion đang stuck:** Nếu sau 2 lần retry điểm số không cải thiện (hoặc giảm — hiện tượng regression), có nên break sớm thay vì đợi `max_retries`? Sẽ thử ở Ngày 13 khi đo cost.

- **Best-so-far pattern:** Khi retry có thể làm chất lượng tệ đi (sửa chỗ này hỏng chỗ khác), nên lưu lại answer tốt nhất từng đạt được và trả về answer đó thay vì answer cuối. Code hôm nay chưa có pattern này — sẽ refactor sau.

- **Constitutional AI:** Biến thể nâng cao của Reflexion dùng "constitution" (danh sách nguyên tắc) thay vì critique tự do — sẽ học ở **Ngày 95-98** (Phase 3, Safety).

- **Episodic Memory:** Cách lưu lại bài học từ Reflexion qua nhiều session để agent không mắc cùng lỗi lần sau — sẽ học ở **Ngày 64-65** (Phase 2, Memory).

- **Offline evaluation, RAG, Human-in-the-loop, Streaming:** Các cơ chế đảm bảo chất lượng thay thế Reflexion khi latency critical — sẽ học rải rác từ Tuần 6 đến Tuần 19.
