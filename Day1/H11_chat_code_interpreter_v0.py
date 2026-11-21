from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import WebSearchTool
from azure.identity import AzureCliCredential

ENDPOINT="https://proj-hol-t-resource.services.ai.azure.com/api/projects/proj-hol-t"
MODEL = "gpt-6-astra"

QUESTION = {
    "오늘/내일 서울 날씨 알려줘"
}

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

QUESTION = (
    "다음은 월별 카페 방문객 수 입니다.:"
    "[120, 150, 135, 210, 180, 100]."
    "Python을 사용해서 총합, 평균, 최대값과 최대값이 나온 월을 계산하고",
    "월별 방문객 수 막대 그래프도 만들어 주세요. 계산 과정과 결과를 설명해 주세요."
)

response = openai_client.responses.create(
    model=MODEL, tools=[{ "type" : "code_interpreter", "container": {"type" : "auto"},}],
    instructions=("최신 날씨 정보는 구글에서 항상 검색해서 답변해 주세요.")
),
input=QUESTION,

print("[Code Interpreter 대화]")
print("[Web Search ON]")
print(without_web_search.output_text)


