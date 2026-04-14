# ReAct Loop

## Sơ đồ
[Thought] → [Action] → [Observation]
                              ↓
                    Đủ thông tin? 
                    ├── Có → [Final Answer]
                    └── Không → [Thought] (loop lại)
                              ↓
                    max_iterations reached? → [Force Stop]

## Giải thích từng bước
- **Thought:**
Suy nghĩ để lập kế hoạch phải hành động gì
- **Action:**
Hành động dựa trên suy nghĩ bước trước
- **Observation:**
Quan sát kết quả trả về có đáp ứng yêu cầu, nếu không đáp ững thì tiếp tục suy nghĩ - Thought
- **Stopping condition:**
Điều kiện dừng nếu agent lặp nhiều lần nhưng không cải thiện kết quả trả về

## Ví dụ cụ thể
[1 ví dụ bạn tự nghĩ ra — không dùng ví dụ của mình]

- Ví dụ về agent viết bài đăng blog tin tức mới trong thể thao
- Agent có 1 tool là web search
- **Thought:**
Cần tìm những tin mới nhất trong 24h qua trong lĩnh vực thể thao, key word là hot new sport
- **Action:**
Tìm kiếm trên web với tool web search từ khoá "hot new sport"
- **Observation:**
Quan sát kết quả trả về là "Lịch thi đấu WC 2022", đây là 2026 nhưng kết quả tìm kiếm trả về 2022 thì không đúng, cần thay đổi từ khoá với kèm thời gian hiện tại là ngày 30/3/2026
- **Stopping condition:**
Vòng lặp tối đa 5 lần nếu không cải thiện kết quả, hoặc Agent tự đánh giá được kết quả đủ tốt và trả về final answer