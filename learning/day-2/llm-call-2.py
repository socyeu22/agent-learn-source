import os
import anthropic
from dotenv import load_dotenv

load_dotenv()
client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

def ask(msg) -> str:
    res = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1024,
        messages=msg
    )
    return res.content[0].text

conversation_history = []

while True:
    msg = input("Bạn: ")
    if msg.lower() == "quit" :
        break
    
    conversation_history.append({"role" : "user", "content" : msg})
    res = ask(conversation_history)

    print(f"llm: {res}\n")

    conversation_history.append({"role" : "assistant", "content" : res})


