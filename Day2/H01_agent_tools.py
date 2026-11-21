import os
from pathlib import Path

from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import AgentDetails, CodeInterpreterTool, PromptAgentDefinition
from azure.identity import AzureCliCredential
from dotenv import load_dotenv


HOL_ROOT = Path(__file__).resolve().parents[0]
AGENT_NAME = "day2-h01-tools-agent"


def create_or_get_agent(
    project_client: AIProjectClient,
    agent_name: str,
    model: str,
) -> AgentDetails:
    """이름으로 Agent를 찾고, 없으면 Code Interpreter Tool을 등록해 생성한다."""

    if project_client is None or not agent_name or not model:
        raise RuntimeError("project_client, agent_name, model을 확인하세요.")

    # 먼저 프로젝트의 Agent 목록에서 같은 이름을 검색한다.
    # 같은 이름의 Agent가 있으면 새로 만들지 않고 기존 Agent를 재사용한다.
    for existing_agent in project_client.agents.list():
        if existing_agent.name == agent_name:
            agent = project_client.agents.get(agent_name=agent_name)
            print(f"기존 Agent 재사용: {agent.name}")
            return {
                "name": agent.name,
                "version": agent.versions.latest.version,
                "type": "agent_reference",
            }

    # Agent가 없을 때만 Tool이 포함된 새 Agent를 만든다.
    agentversion = project_client.agents.create_version(
        agent_name=agent_name,
        definition=PromptAgentDefinition(
            model=model,
            # instructions=(
            #     "당신은 계산과 간단한 데이터 분석을 도와주는 AI Agent입니다. "
            #     "필요한 경우 Code Interpreter Tool을 사용하고, "
            #     "계산 과정을 이해하기 쉬운 문장으로 설명하세요."
            # ),
            instructions=(
                    "당신은 계산과 간단한 데이터 분석을 도와주는 AI Agent입니다. "
                    "모든 계산 요청에 답하기 전에 반드시 Code Interpreter Tool을 호출해 "
                    "Python으로 계산하세요. 도구 실행 없이 계산 결과를 답하지 말고, "
                    "실행 결과를 이해하기 쉬운 문장으로 설명하세요."
            ),

            
            tools=[
                # Code Interpreter를 Agent의 Tool 목록에 등록한다.
                # container를 생략하면 서비스가 기본 설정(auto)을 사용한다.
                CodeInterpreterTool(),
            ],# {"type": "code_interpreter",}

        ),
    )
    agent_reference = {
        "name": agentversion.name,
        "version": agentversion.version,
        "type": "agent_reference",
    }
    
    print(f"새 Agent 생성: {agentversion.name}")
    return agent_reference


def main() -> None:
    """Tool이 등록된 Agent를 만들고 간단한 계산 질문을 보낸다."""

    # .env는 hol_l02_v3 폴더에 둔다.
    load_dotenv(HOL_ROOT / ".env")
    endpoint = os.environ["FOUNDRY_PROJECT_ENDPOINT"]
    model = os.environ["FOUNDRY_MODEL_DEPLOYMENT"]

    credential = AzureCliCredential()
    project_client = AIProjectClient(endpoint=endpoint, credential=credential)
    openai_client = project_client.get_openai_client()

    try:
        agent_reference = create_or_get_agent(project_client,AGENT_NAME,model)
        conversation = openai_client.conversations.create()
        response = openai_client.responses.create(
            conversation=conversation.id,
            input=(
                "다음 숫자의 평균과 가장 큰 값을 계산해 주세요: "
                "12, 25, 31, 42, 50"
            ),
            extra_body={"agent_reference": agent_reference},
        )

        print("\n[Agent 응답]")
        print(response.output_text)
    finally:
        openai_client.close()
        project_client.close()
        credential.close()


if __name__ == "__main__":
    main()