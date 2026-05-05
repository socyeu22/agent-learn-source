# Ngày 15 — Review Tuần 3 + Commit

## 1. Vấn đề khái niệm này giải quyết

Sau khi đã học 4 strategies riêng lẻ (Day 11) và implement Reflexion (Day 12–13) + Factory Pattern (Day 14), câu hỏi quan trọng nhất chưa được trả lời: **với một task cụ thể, chọn strategy nào?** Biết implement không đủ — biết **khi nào dùng cái nào** mới tạo ra giá trị thực tế.

## 2. Tổng hợp 4 Strategies

| Strategy | Cơ chế (1 câu) | Tốt cho | Tránh khi | Chi phí token |
|---|---|---|---|---|
| **ReAct** | Xen kẽ Thought → Action → Observation, phản hồi ngay với kết quả từ môi trường | Task ngắn, cần tool, môi trường thay đổi liên tục | Task nhiều bước dài, dễ context drift sau 10+ iterations | 1x baseline |
| **Plan-and-Execute** | Tách biệt giai đoạn lập kế hoạch toàn cục và thực thi tuần tự | Task có cấu trúc rõ, các bước phụ thuộc nhau theo thứ tự cố định | Môi trường động, thông tin thay đổi giữa chừng | 1 planning call + N execution calls |
| **Tree of Thought** | Khám phá nhiều nhánh suy luận song song, chọn nhánh triển vọng nhất | Bài toán sáng tạo, nhiều lời giải tiềm năng | Token budget hạn chế, cần real-time response | Rất cao — tăng theo số nhánh × chiều sâu |
| **Reflexion** | Sau mỗi attempt, LLM tự chấm điểm theo rubric → inject feedback → chạy lại | Task có tiêu chí đánh giá rõ, chất lượng quan trọng hơn tốc độ | Task factual (1 đáp án đúng), real-time chat | 3–28x tùy số retry |

## 3. Framework chọn Strategy

Hỏi 3 câu theo thứ tự, dừng ở câu đầu tiên cho kết quả "Có":

1. Task đơn giản, 1–3 bước? → **ReAct**
2. Cần chất lượng cao, có tiêu chí đánh giá rõ, user chờ được? → **Reflexion**
3. Nhiều bước cố định, biết trước cấu trúc? → **Plan-and-Execute**
4. Cần khám phá nhiều hướng, bài toán sáng tạo? → **Tree of Thought**

> **Nguyên tắc Selection Principle:** Luôn bắt đầu với strategy đơn giản nhất (ReAct). Chỉ nâng cấp khi có bằng chứng cụ thể (A/B test, token cost, output quality) rằng ReAct không đủ.

## 4. Hiểu sâu hơn

**"Strategy phức tạp hơn = kết quả tốt hơn" là sai.** Ví dụ cụ thể:
- Tree of Thought cho task "mấy giờ rồi?" → 5 nhánh song song đều ra cùng 1 kết quả, tốn 5x token, không cải thiện gì
- Reflexion cho task factual → LLM tự chấm 5/5 ngay lần đầu, retry không thêm giá trị
- Plan-and-Execute trong môi trường động → kế hoạch lỗi thời ngay sau bước 1

**Khi nào nâng cấp strategy trong code?** Cách đơn giản nhất: dựa vào metadata của task (độ phức tạp, loại task) hoặc kết quả lần chạy đầu (nếu ReAct kém, retry bằng Reflexion). Adaptive strategy selection là chủ đề nâng cao sẽ quay lại sau.

## 5. Vị trí trong bức tranh lớn

Tuần 3 hoàn thành chuỗi: Day 6 (ReAct concept) → Day 7–9 (ReAct implementation) → Day 10 (debug + log) → Day 11 (4 strategies overview) → Day 12–13 (Reflexion implement + test) → Day 14 (Factory Pattern) → Day 15 (framework chọn strategy).

Từ Tuần 4 trở đi chuyển sang **Tool Use** — từ việc dùng tools đơn giản sang thiết kế tool interface cho production: tool definition schema, input validation, error contract.

## 6. Code đã viết tuần 3

- `agents/react_agent.py` — thêm `self_critique()`, `run_with_reflexion()`, `_build_tool_list()`, `tracker` parameter, `return_trace=True`
- `agents/agent_factory.py` — `STRATEGY_REGISTRY`, `create_agent()` dùng `functools.partial`, `list_strategies()`, ValueError rõ ràng
- `scripts/compare_reflexion.py` — A/B test script
- `tools/basic_tools.py` — thêm `compute_annuity`, fix `calculate`
- `prompts/react_system.txt` — `{tool_list}` placeholder thay hardcode
- `notes/` — planning-strategies, reflexion, reflexion-when-to-use, factory-pattern, reflexion-comparison

## 7. Tech debt có ý thức (chưa cần refactor ngay)

1. **`partial` vs closure trong `create_agent()`**: `partial` có nguy cơ argument collision nhưng hỗ trợ introspection (`.func`, `.keywords`) tốt cho testing. Trade-off chấp nhận được ở scale hiện tại.
2. **Best-so-far pattern trong Reflexion**: hiện trả về answer cuối, không phải answer tốt nhất. Sẽ refactor khi học evaluation ở Phase 3.
3. **Hallucinated observations trong trace**: LLM tự viết "Observation" giả lẫn với observation thật trong report. Cần tách khi render — chưa ảnh hưởng logic, chỉ ảnh hưởng readability.

## 8. Câu hỏi đã kiểm tra

- **Lý thuyết:** Mô tả luồng thực thi Reflexion (chạy → chấm điểm theo rubric → feedback → inject → retry)
- **Tình huống:** Chọn strategy cho "viết email xin lỗi" → Reflexion (có rubric, có không gian cải thiện, latency OK), nhưng bắt đầu bằng ReAct trước theo Selection Principle
- **Bẫy:** "ToT luôn tốt hơn ReAct" → Sai, "luôn" là bẫy, nhiều hướng chỉ có giá trị khi các hướng thực sự khác nhau
- **Tình huống:** Đồng nghiệp thêm `elif` thay vì registry entry → bypass pattern, `list_strategies()` bị lệch source of truth
