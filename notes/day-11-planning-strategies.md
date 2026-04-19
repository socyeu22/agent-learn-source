# Planning Strategies for AI Agents

## Bảng so sánh

| Strategy | Cơ chế (1 câu) | Dùng khi | Tránh khi |
|---|---|---|---|
| **ReAct** | Xen kẽ lập luận (Thought) và hành động (Action) trong một chuỗi duy nhất, phản hồi ngay với kết quả từ môi trường. | Task ngắn, cần phản hồi nhanh, môi trường thay đổi liên tục. | Task dài nhiều bước, cần kế hoạch tổng thể trước khi hành động. |
| **Plan-and-Execute** | Tách biệt giai đoạn lập kế hoạch toàn cục và giai đoạn thực thi từng bước theo kế hoạch đó. | Task phức tạp, có cấu trúc rõ ràng, các bước phụ thuộc nhau theo thứ tự. | Môi trường động, thông tin thay đổi giữa chừng khiến kế hoạch ban đầu lỗi thời. |
| **Tree of Thought** | Khám phá nhiều hướng suy luận song song dạng cây, đánh giá và chọn nhánh triển vọng nhất. | Bài toán đòi hỏi sáng tạo, có nhiều lời giải tiềm năng, cần tìm phương án tối ưu. | Task cần phản hồi thời gian thực, hoặc khi chi phí tính toán bị giới hạn chặt. |
| **Reflexion** | Agent tự phản ánh bằng ngôn ngữ sau mỗi lần thất bại, lưu bài học vào bộ nhớ dài hạn để cải thiện trial tiếp theo. | Task cho phép thử nhiều lần, cần học từ lỗi, không muốn fine-tune lại model. | Task chỉ có một lần thực thi duy nhất, hoặc khi tốc độ phản hồi là ưu tiên hàng đầu. |

---

## Use Cases thực tế

### ReAct

**Tình huống:** Người dùng hỏi *"Giá iPhone 16 Pro hiện tại là bao nhiêu?"* — agent cần tìm kiếm web, đọc kết quả, rồi trả lời ngay.

**Tại sao phù hợp:** Task chỉ cần vài bước, thông tin lấy từ môi trường (kết quả tìm kiếm) quyết định ngay bước tiếp theo, không cần kế hoạch phức tạp từ trước.

---

### Plan-and-Execute

**Tình huống:** Agent được giao nhiệm vụ *"Nghiên cứu 5 đối thủ cạnh tranh, tổng hợp điểm mạnh/yếu của từng công ty và viết báo cáo."*

**Tại sao phù hợp:** Có thể lập kế hoạch rõ ràng từ đầu (tìm kiếm công ty 1 → tóm tắt → tìm kiếm công ty 2 → ... → tổng hợp báo cáo), các bước độc lập và có thứ tự logic, không cần phản hồi liên tục từ môi trường.

---

### Tree of Thought

**Tình huống:** Agent cần giải bài toán *"Lên lịch trình du lịch 5 ngày tại Nhật Bản tối ưu nhất với ngân sách 30 triệu."*

**Tại sao phù hợp:** Có vô số cách sắp xếp hành trình, cần khám phá nhiều phương án (ưu tiên Tokyo trước? hay Kyoto?), đánh giá từng nhánh theo tiêu chí chi phí + trải nghiệm, rồi chọn lịch trình tốt nhất.

---

### Reflexion

**Tình huống:** Agent được yêu cầu *viết một hàm Python kiểm tra số nguyên tố*, chạy test cases, sửa lỗi cho đến khi tất cả pass.

**Tại sao phù hợp:** Có thể thử nhiều lần, có tín hiệu đánh giá rõ ràng (pass/fail test), agent cần nhớ lỗi cũ (ví dụ: *"lần trước quên xử lý số 1 và số 2"*) để không lặp lại ở lần viết tiếp theo.

---

## Ghi chú cá nhân

- **Điều tôi thấy thú vị nhất:** Reflexion chứng minh rằng LLM có thể "học" mà không cần cập nhật trọng số — chỉ cần ngôn ngữ làm phương tiện phản ánh, bộ nhớ trở thành công cụ thay thế gradient descent. Đây là ý tưởng rất gần với cách con người thực sự học từ thất bại.

- **Điều tôi còn chưa chắc:** Trong thực tế, khi nào nên kết hợp các chiến lược với nhau (ví dụ: Plan-and-Execute + Reflexion), và làm thế nào để đánh giá chiến lược nào phù hợp khi bài toán có đặc điểm của nhiều loại cùng một lúc?
