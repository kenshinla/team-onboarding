import os
from pathlib import Path

from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import AgentDetails, PromptAgentDefinition, WebSearchTool
from azure.identity import AzureCliCredential


HOL_ROOT = Path(__file__).resolve().parents[0]
AGENT_NAME = "hol-common-t"
ROUTINE_NAME = "day1-h14-daily-ai-news-USER11"

# NEWS_PROMPT는 Routine이 Agent에 전달하는 입력 메시지이다.
NEWS_PROMPT = """
오늘의 최신 AI 관련 뉴스를 검색해서 정리해 주세요.

다음 형식으로 최대 5건을 작성하세요.
1. 뉴스 제목
2. 출처와 발행일
3. 핵심 내용 2~3문장
4. 개발자에게 중요한 이유

확인할 수 없는 내용은 추측하지 말고, 검색 결과가 없으면
검색 결과가 없다고 알려 주세요.
"""

def main() -> None:

    endpoint = "https://proj-hol-t-resource.services.ai.azure.com/api/projects/proj-hol-t"

    credential = AzureCliCredential()
    project_client = AIProjectClient(endpoint=endpoint, credential=credential)

    agent = project_client.agents.get(agent_name=AGENT_NAME)
    routine = project_client.beta.routines.create_or_update(
            routine_name=ROUTINE_NAME,
            description="매일 최신 AI 뉴스를 검색하고 요약한다.",
            enabled=True,
            triggers={
                "daily-ai-news": {
                    "type": "schedule",
                    "cron_expression": "10 17 * * *",
                    "time_zone": "Asia/Seoul",
                }
            },
            action={
                "type": "invoke_agent_responses_api",
                "agent_name": agent.name,
                "input": NEWS_PROMPT,
            },
        )

    print(f"Agent 준비 완료: {agent.name}")
    print(f"Routine 생성 완료: {routine.name}")
    print(f"Routine 활성화 상태: {routine.enabled}")
        
if __name__ == "__main__":
    main()
    