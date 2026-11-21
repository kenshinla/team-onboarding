from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import WebSearchTool
from azure.identity import AzureCliCredential

ENDPOINT="https://proj-hol-t-resource.services.ai.azure.com/api/projects/proj-hol-t"
MODEL = "gpt-6-astra"

QUESTION = (
    "오늘/내일 서울 날씨 알려줘"
)

project_client = AIProjectClient(endpoint=ENDPOINT,credential=AzureCliCredential())
openai_client = project_client.get_openai_client()
without_web_search = openai_client.responses.create(
    model=MODEL,
    input=QUESTION,
)
print("=" * 80)
print("[Web Search OFF]")
print(without_web_search.output_text)

web_search_tool = WebSearchTool(external_web_access=True)
with_web_search = openai_client.responses.create(
    model=MODEL,
    input=QUESTION, instructions="최신 날씨 정보는 구글에서 항상 검색해서 답변해 주세요.",
    tools=[
        {"type" : "web_search"}],
)

print("=" * 80)
print("[Web Search ON]")
print(without_web_search.output_text)


