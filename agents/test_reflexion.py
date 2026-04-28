from agents.react_agent import run_with_reflexion
from tools.basic_tools import TOOLS

task = "Giải phương trình 10/x = 8"

print(f"\n{'='*50}")
print(f"Task: {task}")
result = run_with_reflexion(task, TOOLS)
print(f"\n[Kết quả cuối]: {result}")
