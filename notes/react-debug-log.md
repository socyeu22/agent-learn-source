# ReAct Agent Debug Log

## Test Case 1
**Input:** "Bây giờ là mấy giờ?"
**Iterations:** 2
**Outcome:** ✅ Thành công

### Iteration 1
- Thought: Tôi cần biết thời gian hiện tại, hãy dùng tool get_current_time
- Action: get_current_time
- Action Input: ""
- Observation: 2026-04-14 10:32:17

### Iteration 2
- Thought: Đã có kết quả, có thể trả lời ngay
- Final Answer: Bây giờ là 10:32:17, ngày 14/04/2026

**Nhận xét:** Agent xử lý đúng — task yêu cầu real-time data nên bắt buộc phải qua tool. Nếu LLM bỏ qua `get_current_time` và trả Final Answer thẳng thì kết quả sẽ bị hallucinate (giờ sai).

---

## Test Case 2
**Input:** "Tính 15% của 2500000"
**Iterations:** 2
**Outcome:** ✅ Thành công

### Iteration 1
- Thought: Cần tính 15% của 2,500,000 — dùng tool calculate
- Action: calculate
- Action Input: `2500000 * 0.15`
- Observation: 375000.0

### Iteration 2
- Thought: Đã có kết quả chính xác từ tool
- Final Answer: 15% của 2,500,000 VND là 375,000 VND

**Nhận xét:** LLM có thể tự tính được bài này, nhưng nếu để LLM tự trả lời thẳng thì dễ hallucinate với số lẻ phức tạp hơn. Việc bắt qua tool `calculate` đảm bảo kết quả chính xác 100%.

---

## Test Case 3
**Input:** "Nếu tôi tiết kiệm 500,000 VND/tháng từ hôm nay, sau 2 năm tôi có bao nhiêu?"
**Iterations:** 3
**Outcome:** ✅ Thành công

### Iteration 1
- Thought: Cần tính số tháng trong 2 năm rồi nhân với số tiền tiết kiệm mỗi tháng
- Action: calculate
- Action Input: `500000 * 24`
- Observation: 12000000

### Iteration 2
- Thought: Đã có kết quả, 2 năm = 24 tháng, tổng = 12,000,000 VND
- Final Answer: Sau 2 năm tiết kiệm 500,000 VND/tháng, bạn sẽ có **12,000,000 VND**

**Nhận xét:** Task nhiều bước nhất trong 3 case — agent cần tự suy luận "2 năm = 24 tháng" trước khi gọi tool. Đây là bài test tốt cho phần Thought của ReAct loop.

---

## Bugs Tìm Ra & Đã Fix

### Bug 1 — Double Final Answer
**Triệu chứng:** Final Answer bị in ra 2 lần — một lần trong iteration print của agent, một lần nữa ở `test_react.py`.

**Root cause:** `test_react.py` gọi `print(f"Final Answer: {result}")` sau khi `run_react_agent` return, trong khi bên trong agent đã in llm_output (chứa `Final Answer:`) ở mỗi iteration.

**Fix:** Bỏ dòng `print(f"Final Answer: {result}")` trong `test_react.py` — agent đã in đủ thông tin trong vòng lặp.

---

### Bug 2 — LLM bỏ qua tool, trả Final Answer thẳng
**Triệu chứng:** Với một số task đơn giản, LLM tự tin trả lời mà không gọi tool nào — dẫn đến nguy cơ hallucination.

**Root cause:** Code check `"Final Answer:" in llm_output` trước khi `parse_action()` — nếu LLM trả về cả Action lẫn Final Answer trong cùng 1 response, agent dừng luôn mà không thực thi tool.

**Fix:** Đổi thứ tự — `parse_action()` chạy trước, chỉ accept Final Answer khi không có Action nào:

```python
# Trước
if "Final Answer:" in llm_output:
    return ...
action, action_input = parse_action(llm_output)

# Sau
action, action_input = parse_action(llm_output)
if not action and "Final Answer:" in llm_output:
    return ...
```

---

### Bonus — Regex Final Answer chỉ bắt 1 dòng
**Triệu chứng:** Câu trả lời nhiều dòng bị cắt cụt, chỉ lấy được dòng đầu tiên.

**Root cause:** `re.search(r"Final Answer:\s*(.+)")` — `.+` không match `\n` nên dừng ở cuối dòng đầu.

**Fix qua 2 bước:**
1. Thêm `re.DOTALL` → bắt được nhiều dòng nhưng lấy luôn cả text thừa phía sau
2. Dùng `re.MULTILINE` + `(.+(?:\n.+)*)` → bắt các dòng liên tiếp, dừng ở dòng trống

```python
# Cuối cùng
re.search(r"Final Answer:\s*(.+(?:\n.+)*)", llm_output, re.MULTILINE)
```
