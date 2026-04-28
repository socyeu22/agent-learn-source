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

def run_react_agent(task: str, tools: dict, max_iterations: int = 10) -> str:
    system = open("prompts/react_system.txt").read()
    messages = [{"role": "user", "content": f"Task: {task}"}]

    for i in range(max_iterations):
        # Gọi Claude API với system prompt ReAct và toàn bộ lịch sử messages
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=2048,
            system=system,
            messages=messages,
        )
        # Lấy nội dung text từ response đầu tiên
        llm_output = response.content[0].text

        print(f"\n--- Iteration {i + 1} ---\n{llm_output}")

        # Dùng parse_action để trích xuất tên tool và input từ output của LLM
        # Check Action TRƯỚC — nếu có cả Action lẫn Final Answer thì ưu tiên thực thi tool
        action, action_input = parse_action(llm_output)

        # Chỉ accept Final Answer khi không có Action nào để thực thi
        if not action and "Final Answer:" in llm_output:
            final = re.search(r"Final Answer:\s*(.+(?:\n.+)*)", llm_output, re.MULTILINE)
            return final.group(1).strip() if final else llm_output

        # Nếu không parse được action, inject lỗi như một Observation để LLM tự sửa format
        # (thay vì dừng cứng — LLM đôi khi viết text thừa hoặc xuống dòng giữa Action/Action Input)
        if not action:
            observation = "Error: không parse được Action từ output của bạn. Hãy viết đúng format:\nAction: tên_tool\nAction Input: input"
            messages.append({"role": "assistant", "content": llm_output})
            messages.append({"role": "user", "content": f"Observation: {observation}"})
            continue  # tiếp tục loop thay vì dừng

        action = to_snake_case(action)
        
        # Tra cứu tool trong dict; nếu không tồn tại thì trả về thông báo lỗi làm observation
        if action not in tools:
            observation = f"Error: tool '{action}' không tồn tại. Các tool có sẵn: {list(tools.keys())}"
        else:
            # Thực thi tool với action_input và lấy kết quả làm observation
            # Bắt exception để agent không crash — inject lỗi như Observation cho LLM tự xử lý
            try:
                observation = tools[action](action_input)
            except Exception as e:
                observation = f"Error: tool '{action}' gặp lỗi khi thực thi: {e}"

        print(f"Observation: {observation}")

        # Append output của LLM vào messages với role "assistant"
        messages.append({"role": "assistant", "content": llm_output})
        # Append observation vào messages với role "user" để LLM đọc ở bước tiếp theo
        messages.append({"role": "user", "content": f"Observation: {observation}"})

    return "Đã đạt max_iterations"


def self_critique(answer: str, task: str) -> dict:
    """
    Chấm điểm câu trả lời theo 3 tiêu chí: completeness, accuracy, clarity.
    Trả về dict có 4 keys: completeness, accuracy, clarity, feedback.
    """
    prompt = f"""Bạn là chuyên gia đánh giá câu trả lời của AI.

Task gốc: {task}

Câu trả lời cần chấm:
{answer}

Hãy chấm điểm theo rubric sau (1 = tệ, 5 = xuất sắc):
- completeness: câu trả lời có đầy đủ thông tin không?
- accuracy: thông tin có chính xác không?
- clarity: trình bày có rõ ràng, dễ hiểu không?

Trả về JSON (không có markdown):
{{"completeness": <số>, "accuracy": <số>, "clarity": <số>, "feedback": "<nhận xét>"}}"""

    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=256,
        messages=[{"role": "user", "content": prompt}],
    )
    text = response.content[0].text.strip()
    if text.startswith("```"):
        text = re.sub(r"```(?:json)?\n?", "", text).strip().rstrip("`").strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {"completeness": 1, "accuracy": 1, "clarity": 1, "feedback": f"Không parse được JSON từ critique. Raw: {text[:200]}"}


def run_with_reflexion(task: str, tools: dict, max_retries: int = 2, threshold: float = 4.0) -> str:
    """
    Chạy ReAct agent, sau đó tự critique.
    Nếu điểm thấp → chạy lại với feedback. Tối đa max_retries lần.
    """
    answer = run_react_agent(task, tools)

    for i in range(max_retries):
        critique = self_critique(answer, task)
        scores = {k: critique[k] for k in ("completeness", "accuracy", "clarity")}
        print(f"\n[Reflexion #{i+1}] Điểm: {scores} | Feedback: {critique['feedback']}")

        if all(v >= threshold for v in scores.values()):
            print("[Reflexion] Câu trả lời đạt yêu cầu, dừng lại.")
            break

        enriched_task = f"{task}\n\n[Phản hồi từ lần trước]: {critique['feedback']}"
        answer = run_react_agent(enriched_task, tools)

    return answer