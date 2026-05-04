# tools/basic_tools.py
import datetime, json

def _parse_input(raw: str, key: str) -> str:
    """Parse action_input: JSON object → lấy key, string thuần → dùng thẳng."""
    try:
        parsed = json.loads(raw)
        if isinstance(parsed, dict):
            return parsed.get(key, raw)
    except (json.JSONDecodeError, TypeError):
        pass
    return raw

def get_current_time(action_input: str = "") -> str:
    """Trả về thời gian hiện tại."""
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def calculate(action_input: str) -> str:
    """Tính toán biểu thức toán học. Hỗ trợ +, -, *, /, ** (hoặc ^) và ()."""
    expression = _parse_input(action_input, "expression")
    try:
        expression = expression.replace("^", "**")
        allowed_chars = set("0123456789.+-*/() ")
        if not all(c in allowed_chars for c in expression):
            return "Error: Biểu thức chứa ký tự không hợp lệ. Chỉ cho phép số và +, -, *, **, /(), ()."
        result = eval(expression, {"__builtins__": None}, {})
        # Round để tránh floating point noise (vd: 333.97119999999995)
        if isinstance(result, float):
            result = round(result, 4)
        return f"Kết quả: {result}"
    except ZeroDivisionError:
        return "Error: Lỗi chia cho 0."
    except Exception as e:
        return f"Error: Không thể tính toán biểu thức. Chi tiết: {e}"


def compute_annuity(action_input: str) -> str:
    """
    Tính tích lũy tiết kiệm với lãi gộp theo từng năm.
    Input JSON: pmt (triệu VND/năm), rate (% lãi suất/năm), target (triệu VND mục tiêu).
    Giả định: gửi tiền đầu năm, lãi tính cả năm đó (annuity due).
    """
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
            summary = (
                f"Cần {year} năm để tích lũy đủ {target:,.0f} triệu VND.\n"
                f"Số tiền đạt được: {total:,.2f} triệu VND\n"
                f"Tổng tiền gốc đã gửi: {pmt * year:,.0f} triệu VND\n"
                f"Lãi tích lũy: {total - pmt * year:,.2f} triệu VND\n\n"
                f"Chi tiết từng năm:\n" + "\n".join(rows)
            )
            return summary

    return f"Không đạt mục tiêu {target:,.0f} triệu sau 100 năm với pmt={pmt} triệu, rate={rate*100}%/năm."


# Tool registry
TOOLS = {
    "get_current_time": get_current_time,
    "calculate": calculate,
    "compute_annuity": compute_annuity,
}