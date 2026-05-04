import anthropic, json, os, re
from dotenv import load_dotenv
load_dotenv()

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

def to_snake_case(name):
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()

def parse_action(text: str) -> tuple[str, str]:
    
    action_match = re.search(r"Action:\s*(.+)", text)
    action_input_match = re.search(r"Action Input:\s*(.+)", text)
    if not action_match or not action_input_match:
        return ("", "")
    return (action_match.group(1).strip(), action_input_match.group(1).strip())

def _build_tool_list(tools: dict) -> str:
    lines = []
    for i, name in enumerate(tools, 1):
        fn = tools[name]
        doc_lines = (fn.__doc__ or "").strip().splitlines() if fn.__doc__ else []
        doc_lines = [l.strip() for l in doc_lines if l.strip()]
        if doc_lines:
            lines.append(f"{i}. {name} — {doc_lines[0]}")
            for extra in doc_lines[1:]:
                lines.append(f"   {extra}")
        else:
            lines.append(f"{i}. {name}")
    return "\n".join(lines)


def run_react_agent(task: str, tools: dict, max_iterations: int = 10, tracker=None, return_trace: bool = False):
    system = open("prompts/react_system.txt").read().replace("{tool_list}", _build_tool_list(tools))
    messages = [{"role": "user", "content": f"Task: {task}"}]
    trace = []

    for i in range(max_iterations):
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=2048,
            system=system,
            messages=messages,
        )
        if tracker:
            tracker.add(response.usage)
        llm_output = response.content[0].text

        print(f"\n--- Iteration {i + 1} ---\n{llm_output}")

        # Check Action TRƯỚC — nếu có cả Action lẫn Final Answer thì ưu tiên thực thi tool
        action, action_input = parse_action(llm_output)

        # Chỉ accept Final Answer khi không có Action nào để thực thi
        if not action and "Final Answer:" in llm_output:
            final = re.search(r"Final Answer:\s*(.+)", llm_output, re.DOTALL)
            answer = final.group(1).strip() if final else llm_output
            trace.append({"iteration": i + 1, "llm_output": llm_output, "action": "", "action_input": "", "observation": ""})
            if return_trace:
                return {"answer": answer, "trace": trace}
            return answer

        # Nếu không parse được action, inject lỗi như một Observation để LLM tự sửa format
        if not action:
            observation = "Error: không parse được Action từ output của bạn. Hãy viết đúng format:\nAction: tên_tool\nAction Input: input"
            trace.append({"iteration": i + 1, "llm_output": llm_output, "action": "", "action_input": "", "observation": observation})
            messages.append({"role": "assistant", "content": llm_output})
            messages.append({"role": "user", "content": f"Observation: {observation}"})
            continue

        action = to_snake_case(action)

        if action not in tools:
            observation = f"Error: tool '{action}' không tồn tại. Các tool có sẵn: {list(tools.keys())}"
        else:
            try:
                observation = tools[action](action_input)
            except Exception as e:
                observation = f"Error: tool '{action}' gặp lỗi khi thực thi: {e}"

        print(f"Observation: {observation}")
        trace.append({"iteration": i + 1, "llm_output": llm_output, "action": action, "action_input": action_input, "observation": observation})

        messages.append({"role": "assistant", "content": llm_output})
        messages.append({"role": "user", "content": f"Observation: {observation}"})

    if return_trace:
        return {"answer": "Đã đạt max_iterations", "trace": trace}
    return "Đã đạt max_iterations"


def self_critique(answer: str, task: str, trace: list = None, tracker=None) -> dict:
    """
    Chấm điểm câu trả lời theo 3 tiêu chí: completeness, accuracy, clarity.
    Trả về dict có 4 keys: completeness, accuracy, clarity, feedback.
    """
    tool_context = ""
    if trace:
        tool_calls = [s for s in trace if s.get("action")]
        if tool_calls:
            lines = ["Agent đã gọi các tool sau (kết quả là dữ liệu thật, không phải do AI tự bịa):"]
            for s in tool_calls:
                lines.append(f"- {s['action']}({s['action_input']}) → {str(s['observation'])[:200]}")
            tool_context = "\n" + "\n".join(lines) + "\n"

    prompt = f"""Bạn là chuyên gia đánh giá câu trả lời của AI agent có khả năng gọi tool.

Task gốc: {task}
{tool_context}
Câu trả lời cần chấm:
{answer}

Hãy chấm điểm theo rubric sau (1 = tệ, 5 = xuất sắc):
- completeness: câu trả lời có đầy đủ thông tin không?
- accuracy: thông tin có chính xác không? (nếu dữ liệu đến từ tool call ở trên thì coi là chính xác)
- clarity: trình bày có rõ ràng, dễ hiểu không?

Trả về JSON (không có markdown):
{{"completeness": <số>, "accuracy": <số>, "clarity": <số>, "feedback": "<nhận xét>"}}"""

    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )
    if tracker:
        tracker.add(response.usage)
    text = response.content[0].text.strip()
    if text.startswith("```"):
        text = re.sub(r"```(?:json)?\n?", "", text).strip().rstrip("`").strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {"completeness": 1, "accuracy": 1, "clarity": 1, "feedback": f"Không parse được JSON từ critique. Raw: {text[:200]}"}


def run_with_reflexion(task: str, tools: dict, max_retries: int = 2, threshold: float = 4.0, tracker=None, return_history: bool = False):
    """
    Chạy ReAct agent, sau đó tự critique.
    Nếu điểm thấp → chạy lại với feedback. Tối đa max_retries lần.
    return_history=True → trả về dict {"final_answer": str, "history": [...]}
    """
    history = []
    result = run_react_agent(task, tools, tracker=tracker, return_trace=True)
    answer, trace = result["answer"], result["trace"]

    for i in range(max_retries):
        critique = self_critique(answer, task, trace=trace, tracker=tracker)
        scores = {k: critique[k] for k in ("completeness", "accuracy", "clarity")}
        passed = all(v >= threshold for v in scores.values())
        print(f"\n[Reflexion #{i+1}] Điểm: {scores} | Feedback: {critique['feedback']}")

        history.append({
            "attempt": i + 1,
            "answer": answer,
            "trace": trace,
            "scores": scores,
            "feedback": critique["feedback"],
            "passed": passed,
        })

        if passed:
            print("[Reflexion] Câu trả lời đạt yêu cầu, dừng lại.")
            break

        enriched_task = f"{task}\n\n[Phản hồi từ lần trước]: {critique['feedback']}"
        result = run_react_agent(enriched_task, tools, tracker=tracker, return_trace=True)
        answer, trace = result["answer"], result["trace"]

    if return_history:
        return {"final_answer": answer, "history": history}
    return answer