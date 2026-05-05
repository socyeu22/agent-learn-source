# Ngày 14 — Factory Pattern cho Agent Strategies

## 1. Vấn đề khái niệm này giải quyết

Bạn đã có `run_react_agent()` và `run_with_reflexion()`. Mỗi nơi cần gọi agent (CLI, API endpoint, test) đều phải tự viết `if/else` để chọn hàm nào. Khi thêm strategy mới, bạn phải sửa tất cả các nơi đó — quên sửa 1 chỗ là bug. Cần một cơ chế để thêm strategy mà không sửa logic điều phối.

## 2. Định nghĩa

1. **Factory Pattern**: một hàm/module nhận tên strategy (string) làm input, trả về agent function tương ứng — tách biệt việc "chọn strategy" ra khỏi việc "chạy strategy".
2. **Strategy Selection Principle**: nguyên tắc luôn bắt đầu với strategy đơn giản nhất (ReAct), chỉ nâng cấp lên strategy phức tạp hơn khi có bằng chứng cụ thể rằng strategy đơn giản không đủ.

## 3. Hiểu sâu hơn

Factory đơn giản có thể dùng `if/elif` bên trong, nhưng khi số lượng strategies tăng (Day 11 đã liệt kê 4 strategies), cách tốt hơn là dùng **registry dictionary** — giống cách đã làm với tool registry ở Day 9. Mỗi strategy được đăng ký vào dict, factory chỉ cần lookup:

```python
STRATEGY_REGISTRY = {
    "react":      run_react_agent,
    "reflexion":  run_with_reflexion,
}
```

Khi thêm strategy mới (ví dụ `plan_execute`), chỉ cần 2 thay đổi trong `agent_factory.py`: 1 dòng import + 1 dòng registry entry. Toàn bộ `create_agent()`, `list_strategies()`, error handling không cần sửa gì.

`functools.partial` được dùng để "đóng gói" tham số `tools` vào strategy function, tạo ra callable đơn giản `agent_fn(task)` thay vì `strategy_fn(task, tools)`. Ưu điểm so với `lambda`: `partial` giữ metadata của function gốc (`__name__`, `__doc__`), hỗ trợ introspection qua `.func` và `.keywords` — rất hữu ích cho unit test.

Error handling khi strategy không hợp lệ phải raise error với message rõ ràng, bao gồm cả danh sách strategy hợp lệ. Không được âm thầm fallback về default — fallback im lặng tạo bug rất khó trace vì agent chạy "bình thường" nhưng dùng sai strategy.

## 4. Hậu quả nếu bỏ qua hoặc dùng sai

**Không dùng Factory Pattern:** Mỗi lần thêm strategy mới, phải sửa code ở mọi nơi gọi agent — CLI, API endpoint, test file. Quên sửa 1 chỗ = bug. Với 5 nơi gọi agent và 4 strategies, bạn đang quản lý 20 nhánh `if/else` rải rác khắp codebase.

**Không tuân thủ Selection Principle:** Mặc định dùng Reflexion cho mọi task → user hỏi "mấy giờ rồi?" phải đợi 3 lần LLM call, tốn gấp 3x token, latency tăng 3x mà chất lượng không cải thiện — vì task này không có không gian cải thiện.

## 5. Vị trí trong bức tranh lớn

Factory Pattern là sự áp dụng cùng tư duy **dynamic dispatch qua registry** đã học ở Day 9 (tool registry: `tools[action](action_input)` thay vì `if/else`), nhưng ở tầng cao hơn — tầng strategy thay vì tầng tool. Chuỗi kết nối: Day 9 tool registry → Day 14 strategy registry → cùng pattern, khác tầng trừu tượng.

Selection Principle kết nối trực tiếp với bài học Day 13: Reflexion không phải lúc nào cũng cần. Ba yếu tố quyết định: có không gian cải thiện không, có tiêu chí đánh giá rõ ràng không, và task có cho phép latency cao không.

## 6. Câu hỏi để tự kiểm tra

**Lý thuyết:** Factory Pattern giải quyết vấn đề gì mà `if/else` trực tiếp không giải quyết được — đặc biệt khi code gọi agent nằm ở nhiều nơi khác nhau?

**Tình huống:** Bạn cần thêm strategy `tree_of_thought` vào hệ thống. Liệt kê chính xác các bước cần làm và số dòng thay đổi trong `agent_factory.py`. Có cần sửa `create_agent()` không?

## 7. Câu hỏi còn chưa rõ

Ý tưởng dùng meta-agent (LLM tự chọn strategy) đã được thảo luận nhưng chưa implement — trade-off giữa tự động hóa và chi phí thêm 1 LLM call. Đây có thể là chủ đề quay lại khi hệ thống có nhiều strategies hơn và task đa dạng hơn.
