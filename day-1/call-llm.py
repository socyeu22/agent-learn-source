import os
from dotenv import load_dotenv
import anthropic

load_dotenv()
client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

def call_llm(messages):
    try:
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=1024,
            messages=messages
        )
        return response.content[0].text
    except anthropic.AuthenticationError as e:
        print(f"[Lỗi xác thực] API key không hợp lệ: {e}")
    except anthropic.RateLimitError as e:
        print(f"[Lỗi rate limit] Vượt quá giới hạn request: {e}")
    except anthropic.APIConnectionError as e:
        print(f"[Lỗi kết nối] Không thể kết nối tới API: {e}")
    except anthropic.APIStatusError as e:
        print(f"[Lỗi API {e.status_code}] {e.message}")
    return None


def get_last_n_messages(history, n):
    return history[-n:] if len(history) > n else history


conversation_history = []
N = 10  # số tin nhắn gần nhất gửi cho LLM

while True:
    msg = input("Bạn: ")
    if msg.lower() == "quit":
        break
    else:
        # Thêm tin nhắn của người dùng vào lịch sử
        conversation_history.append({"role": "user", "content": msg})

        # Gửi N tin nhắn gần nhất cho model
        res = call_llm(get_last_n_messages(conversation_history, N))
        if res is None:
            conversation_history.pop()  # bỏ tin nhắn vừa thêm nếu gọi LLM thất bại
            continue
        print(f"Claude: {res}\n")

        # Lưu câu trả lời của model vào lịch sử
        conversation_history.append({"role": "assistant", "content": res})