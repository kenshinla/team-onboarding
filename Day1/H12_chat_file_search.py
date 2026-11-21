from azure.ai.projects import AIProjectClient
from azure.identity import AzureCliCredential

ENDPOINT="https://proj-hol-t-resource.services.ai.azure.com/api/projects/proj-hol-t"
MODEL = "gpt-6-astra"

VECTOR_STORE_ID = "vs_DDlb7fBybfiruN8aQdKlQThh"

QUESTION = (
    "샘플 상품 안내서를 참고하여 AirClean Mini와 CoolBreeze Pro 의"
    "소비전력과 권장 공간을 비교해 주세요."
)

project_client = AIProjectClient(
    endpoint=ENDPOINT,
    credential=AzureCliCredential(),
)
openai_client = project_client.get_openai_client()

file_search_tool = {
    "type" : "file_search",
    "vector_store_ids" : [VECTOR_STORE_ID],
}
response = openai_client.responses.create(
    model=MODEL,
    tools=[file_search_tool],
    input=QUESTION,
)
print("[File Search 응답]")
print(response.output_text)

