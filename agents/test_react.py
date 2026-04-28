# test_react.py — chạy agent với 3 câu hỏi
from agents.react_agent import run_react_agent
from tools.basic_tools import TOOLS

questions = [
    "Nếu tôi tiết kiệm 500,000 VND/tháng từ hôm nay, sau 2 năm tôi có bao nhiêu?",
]

# Test ReAct
for q in questions:
    print(f"\n{'='*50}")
    print(f"Task: {q}")
    run_react_agent(q, TOOLS)
