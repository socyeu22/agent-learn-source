import anthropic
import os
from dotenv import load_dotenv
load_dotenv()

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
SYSTEM = "Bạn là trợ lý AI. Trả lời ngắn gọn, rõ ràng bằng tiếng Việt."
history = []

# Tracking tích lũy cả session
total_in = 0
total_out = 0

def chat_with_cost(user_message: str):
    global total_in, total_out

    history.append({"role": "user", "content": user_message})

    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1024,
        system=SYSTEM,
        messages=history  # truyền gì vào đây? -> history đã có đúng format 
    )

    reply = response.content[0].text
    history.append({"role": "assistant", "content": reply})

    # Lấy token usage
    usage = response.usage
    total_in += usage.input_tokens
    total_out += usage.output_tokens

    # Tính cost — giá claude-3-5-sonnet: $3/1M input, $15/1M output
    cost = (total_in * 1 / 1_000_000) + (total_out * 5 / 1_000_000)

    print(f"Assistant: {reply}")
    print(f"[Tokens: {usage.input_tokens}in / {usage.output_tokens}out | Session cost: ${cost:.4f}]")

if __name__ == "__main__":
    print("Chat Agent với Cost Tracking (gõ 'exit' để thoát)")
    while True:
        q = input("\nYou: ")
        if q.lower() == "exit": break
        chat_with_cost(q)