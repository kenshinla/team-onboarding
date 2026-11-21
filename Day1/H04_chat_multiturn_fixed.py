from azure.ai.projects import AIProjectClient
from azure.identity import AzureCliCredential

ENDPOINT = "https://proj-hol-t-resource.services.ai.azure.com/api/projects/proj-hol-t"
MODEL = "gpt-6-astra"

project_client = AIProjectClient(
    endpoint=ENDPOINT,
    credential=AzureCliCredential())
openai_client = project_client.get_openai_client()

chat_history = [
    {"role": "user", "content": "아침에 간단하게 먹기 좋은 메뉴를 하나 추천해 주세요."},
]

first_response = openai_client.chat.completions.create(
    model=MODEL,
    messages=chat_history,
)

first_answer = first_response.choices[0].message.content or ""
print("\n[첫 번째 응답]\n" + first_answer)


chat_history.append(
    {"role": "user", "content": "그 메뉴를 만들 때 필요한 재료를 알려 주세요."}
)
second_response = openai_client.chat.completions.create(
    model=MODEL,
    messages=chat_history,
)
second_answer = second_response.choices[0].message.content or ""
print("\n[두 번째 응답]\n" + second_answer)
chat_history.append({"role": "assistant", "content": second_answer})

chat_history.append(
    {
        "role": "user",
        "content": "처음 요리하는 사람도 따라 할 수 있게 조리 순서를 설명해 주세요.",
    }
)
third_response = openai_client.chat.completions.create(
    model=MODEL,
    messages=chat_history,
)
third_answer = third_response.choices[0].message.content or ""
print("\n[세 번째 응답]\n" + third_answer)

