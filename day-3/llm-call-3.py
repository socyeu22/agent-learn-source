import anthropic, os
from dotenv import load_dotenv
load_dotenv()

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

# TODO 1: Định nghĩa system prompt — bạn muốn agent này là ai?
SYSTEM = "Bạn là một chuyên gia tư vấn tâm lý"

# TODO 2: Khởi tạo conversation history
history = []
N = 10

def get_last_n_messages(history, n):
    return history[-n:] if len(history) > n else history

def chat_stream(user_message: str):
    # TODO 3: Thêm user_message vào history đúng format
    history.append({"role": "user", "content": user_message})
    print("Assistant: ", end="", flush=True)
    full_reply = ""
    
    n_last_mesages = get_last_n_messages(history, N)
    # TODO 4: Gọi API với streaming, truyền system và history
    with client.messages.stream(
        model="claude-haiku-4-5-20251001", # Đổi sang model Haiku để đảm bảo hoạt động
        max_tokens=1024,
        system=SYSTEM,
        messages=n_last_mesages
        # ...
    ) as stream:
        for text in stream.text_stream:
            print(text, end="", flush=True)
            full_reply += text
    print()
    # TODO 5: Thêm reply của assistant vào history
    history.append({"role": "assistant", "content": full_reply})

if __name__ == "__main__":
    print("Chat Agent (gõ 'exit' để thoát)")
    while True:
        q = input("\nYou: ")
        if q.lower() == "exit":
            break
        chat_stream(q)