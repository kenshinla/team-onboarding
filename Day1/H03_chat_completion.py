from azure.ai.projects import AIProjectClient
from azure.identity import AzureCliCredential

ENDPOINT = "https://proj-hol-t-resource.services.ai.azure.com/api/projects/proj-hol-t"
MODEL = "gpt-6-astra"

project_client = AIProjectClient(
    endpoint=ENDPOINT,
    credential=AzureCliCredential())
openai_client = project_client.get_openai_client()

response = openai_client.chat.completions.create(
    model=MODEL,
    messages=[{"role": "user", "content": "나의 이름은 홍길동이야. 나이는 20살이야."}
    ]
)
print("[응답1]")
print(response.choices[0].message.content)

response = openai_client.chat.completions.create(
    model=MODEL,
    messages=[{"role": "user", "content": "나의 이름은??"}
    ]
)
print("[응답2]")
print(response.choices[0].message.content)