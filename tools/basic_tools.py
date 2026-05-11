# tools/basic_tools.py
import datetime, json


# =============================================================================
# PHẦN 1 — Python implementations (không thay đổi so với trước)
#
# Các hàm này là logic thực thi thuần Python.
# Chúng không biết gì về LLM hay API — chỉ nhận input, trả output.
# =============================================================================

# [CŨ] Hàm helper này parse string thô từ regex ("Action Input: ...")
# [MỚI] Sẽ không cần nữa sau khi refactor sang function calling:
#        API trả về block.input đã là dict typed, không phải string thô.
#        Giữ lại tạm thời vì react_agent.py hiện tại vẫn dùng text parsing.
def _parse_input(raw: str, key: str) -> str:
    try:
        parsed = json.loads(raw)
        if isinstance(parsed, dict):
            return parsed.get(key, raw)
    except (json.JSONDecodeError, TypeError):
        pass
    return raw


# [CŨ] Signature nhận action_input: str — vì text parsing truyền string thô từ regex
# [MỚI] Sau khi refactor: sẽ đổi thành get_current_time() không nhận tham số,
#        vì function calling gọi trực tiếp tools[name](**block.input) với input_schema rỗng.
def get_current_time(action_input: str = "") -> str:
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# [CŨ] Nhận expression dạng string thô, _parse_input tự extract key "expression"
# [MỚI] Sau khi refactor: signature đổi thành calculate(expression: str),
#        vì block.input đã là {"expression": "100 * 1.08"} — không cần _parse_input nữa.
def calculate(action_input: str) -> str:
    expression = _parse_input(action_input, "expression")
    try:
        expression = expression.replace("^", "**")
        allowed_chars = set("0123456789.+-*/() ")
        if not all(c in allowed_chars for c in expression):
            return "Error: Biểu thức chứa ký tự không hợp lệ. Chỉ cho phép số và +, -, *, **, /(), ()."
        result = eval(expression, {"__builtins__": None}, {})
        if isinstance(result, float):
            result = round(result, 4)
        return f"Kết quả: {result}"
    except ZeroDivisionError:
        return "Error: Lỗi chia cho 0."
    except Exception as e:
        return f"Error: Không thể tính toán biểu thức. Chi tiết: {e}"


# [CŨ] Nhận action_input: str rồi json.loads() thủ công bên trong
# [MỚI] Sau khi refactor: signature đổi thành compute_annuity(pmt, rate, target),
#        vì block.input = {"pmt": 100, "rate": 8, "target": 10000} — API đã parse + validate.
#        Không cần try/except json.loads và KeyError nữa — schema "required" đảm bảo đủ key.
def compute_annuity(action_input: str) -> str:
    try:
        params = json.loads(action_input)
        pmt = float(params["pmt"])
        rate = float(params["rate"]) / 100
        target = float(params["target"])
    except (json.JSONDecodeError, KeyError, ValueError) as e:
        return f"Error: Input phải là JSON với 3 key: pmt, rate, target. Chi tiết: {e}"

    rows = []
    total = 0
    for year in range(1, 101):
        total = round((total + pmt) * (1 + rate), 2)
        rows.append(f"  Năm {year:>3}: {total:>12,.2f} triệu VND")
        if total >= target:
            return (
                f"Cần {year} năm để tích lũy đủ {target:,.0f} triệu VND.\n"
                f"Số tiền đạt được: {total:,.2f} triệu VND\n"
                f"Tổng tiền gốc đã gửi: {pmt * year:,.0f} triệu VND\n"
                f"Lãi tích lũy: {total - pmt * year:,.2f} triệu VND\n\n"
                f"Chi tiết từng năm:\n" + "\n".join(rows)
            )

    return f"Không đạt mục tiêu {target:,.0f} triệu sau 100 năm với pmt={pmt} triệu, rate={rate*100}%/năm."


# =============================================================================
# PHẦN 2 — Tool schemas theo chuẩn Anthropic tool use (MỚI HOÀN TOÀN)
#
# [CŨ] Tool description nằm trong docstring của hàm Python.
#      _build_tool_list() đọc docstring → inject vào system prompt dạng plain text.
#      LLM đọc text rồi tự đoán tên key, type, required — không có gì ràng buộc.
#
# [MỚI] Tool description + input_schema định nghĩa tường minh dạng dict.
#      Truyền vào API qua tham số tools=TOOL_SCHEMAS.
#      API tự giải thích schema cho model — model biết chính xác key nào, type nào, bắt buộc không.
#      Model bị ràng buộc trả về đúng format → không thể sai key, không thể hallucinate observation.
#
# Cấu trúc mỗi schema:
#   name        — tên tool, model dùng tên này trong tool_use block
#   description — giải thích ngắn để model biết khi nào dùng tool này
#   input_schema — JSON Schema (draft-07): type, properties, required
# =============================================================================

TOOL_SCHEMAS = [
    {
        "name": "get_current_time",
        "description": (
            # Câu 1 — làm gì, format output
            "Trả về ngày giờ hiện tại dạng YYYY-MM-DD HH:MM:SS. "
            # Câu 2 — khi nào nên gọi
            "Dùng khi user hỏi về thời gian thực, ngày hiện tại, hoặc cần mốc thời gian để tính toán. "
            # Câu 3 — khi nào không gọi (ranh giới với kiến thức nền của LLM)
            "Không dùng khi user hỏi về múi giờ các nước khác hoặc lịch sử ngày tháng — những câu đó LLM tự trả lời được."
        ),
        # input_schema rỗng — tool không nhận tham số nào
        "input_schema": {
            "type": "object",
            "properties": {}
        },
    },
    {
        "name": "calculate",
        "description": (
            # Câu 1 — làm gì, operator nào được hỗ trợ
            "Tính toán biểu thức toán học một bước, hỗ trợ +, -, *, /, ** (lũy thừa), ^ (lũy thừa), và (). "
            # Câu 2 — khi nào nên gọi; "luôn dùng" ngăn LLM tự tính trong đầu với số lớn/lũy thừa
            "Dùng cho phép tính đơn lẻ cần độ chính xác cao. Luôn dùng tool này thay vì tự tính trong đầu. "
            # Câu 3 — ranh giới với compute_annuity, đây là lỗi thực tế đã gặp ở day-13
            "Không dùng để tính lãi gộp nhiều năm hoặc tích lũy tiết kiệm — dùng compute_annuity thay thế."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                # [CŨ] LLM tự đoán key tên gì — đã từng dùng "expr", "formula", "expression"
                # [MỚI] Schema khai báo tường minh key là "expression", type string
                "expression": {
                    "type": "string",
                    "description": "Biểu thức toán học cần tính, ví dụ: '100 * 1.08 ** 5'",
                }
            },
            "required": ["expression"]
        },
    },
    {
        "name": "compute_annuity",
        "description": (
            # Câu 1 — làm gì, output gồm những gì
            "Tính tích lũy tiết kiệm với lãi gộp theo mô hình annuity due (gửi đầu năm). "
            "Trả về số năm cần thiết, tổng tiền đạt được, lãi tích lũy, và bảng chi tiết từng năm. "
            # Câu 2 — khi nào nên gọi
            "Dùng khi user muốn biết mất bao nhiêu năm để đạt mục tiêu tài chính với khoản gửi và lãi suất cố định. "
            # Câu 3 — ranh giới với calculate
            "Không dùng cho phép tính đơn lẻ — dùng calculate thay thế."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                # [CŨ] LLM đã từng dùng "annual_payment", "annual_rate", "years" → sai key → tool crash
                # [MỚI] Schema enforce đúng key, đúng type, đúng unit
                "pmt": {
                    "type": "number",
                    "description": "Số tiền gửi hàng năm, đơn vị triệu VND",
                },
                "rate": {
                    "type": "number",
                    "description": "Lãi suất %/năm, ví dụ: 8 cho 8%/năm",
                },
                "target": {
                    "type": "number",
                    "description": "Mục tiêu tích lũy, đơn vị triệu VND, ví dụ: 10000 cho 10 tỉ",
                },
            },
            # [CŨ] Thiếu key → json.loads KeyError → tool trả error string → LLM retry mù
            # [MỚI] API validate "required" trước khi gọi hàm — không bao giờ thiếu key
            "required": ["pmt", "rate", "target"]
        },
    },
]


# =============================================================================
# PHẦN 3 — Execution registry (giữ nguyên để react_agent.py hiện tại không vỡ)
#
# [CŨ] react_agent.py dùng: tools[action](action_input) — action là string từ regex
# [MỚI] Sau khi refactor react_agent.py sang function calling:
#        tools[block.name](**block.input) — name từ tool_use block, input là dict typed
#        TOOLS dict vẫn giữ cùng cấu trúc, chỉ cách gọi thay đổi ở react_agent.py
# =============================================================================

TOOLS = {
    "get_current_time": get_current_time,
    "calculate":        calculate,
    "compute_annuity":  compute_annuity,
}
