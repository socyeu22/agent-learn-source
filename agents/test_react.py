# test_react.py — chạy agent với 3 câu hỏi
from agents.react_agent import run_react_agent
from tools.basic_tools import TOOLS

questions = [
    "Bây giờ là mấy giờ?",
    "Tính 15% của 2500000",
    "Từ ngày 1/1/2026 đến hôm nay là bao nhiêu ngày?",
]

for q in questions:
    print(f"\n{'='*50}")
    print(f"Task: {q}")
    result = run_react_agent(q, TOOLS)
    print(f"Final Answer: {result}")