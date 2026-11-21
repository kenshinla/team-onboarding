from azure.ai.projects import AIProjectClient
from azure.identity import AzureCliCredential

ENDPOINT = "https://proj-hol-t-resource.services.ai.azure.com/api/projects/proj-hol-t"
MODEL = "grok-4.7-user01"

project_client = AIProjectClient(
    endpoint=ENDPOINT,
    credential=AzureCliCredential())
openai_client = project_client.get_openai_client()

chat_history = []

print("질문을 입력하세요. 종료하려면 quit을 입력합니다.")

while True:
    user_message = input("사용자> ").strip()
    if user_message.lower() == "quit":
        break
    if not user_message:
        continue

    chat_history.append({"role": "user", "content": user_message})
    response = openai_client.chat.completions.create(
        model=MODEL,
        messages=chat_history,
    )
    answer = response.choices[0].message.content or ""
    print(f"Agent> {answer}")
    chat_history.append({"role": "assistant", "content": answer})

    