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
    """Tính toán biểu thức toán học cơ bản (+, -, *, /)."""
    expression = _parse_input(action_input, "expression")
    try:
        allowed_chars = set("0123456789.+-*/() ")
        if not all(c in allowed_chars for c in expression):
            return "Error: Biểu thức chứa ký tự không hợp lệ. Chỉ cho phép số và +, -, *, /, ()."
        result = eval(expression, {"__builtins__": None}, {})
        return str(result)
    except ZeroDivisionError:
        return "Error: Lỗi chia cho 0."
    except Exception as e:
        return f"Error: Không thể tính toán biểu thức. Chi tiết: {e}"

# Tool registry
TOOLS = {
    "get_current_time": get_current_time,
    "calculate": calculate,
}