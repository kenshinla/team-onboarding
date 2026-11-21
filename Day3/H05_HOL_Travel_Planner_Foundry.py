"""H04 MAF Sequential Workflow."""

# TODO: 기존 hol12_multi_agent.py의 SequentialBuilder를 재사용한다.
# VERIFY: 설치된 MAF 버전의 API 호환성을 먼저 확인한다.

import asyncio, os
from pathlib import Path

from agent_framework import AgentResponseUpdate
from agent_framework.foundry import FoundryAgent
from agent_framework.orchestrations import SequentialBuilder
from azure.ai.projects.aio import AIProjectClient
from azure.identity.aio import AzureCliCredential
from dotenv import load_dotenv

# 실습 의도:
# 고객, 요금, 네트워크 전문가 Agent를 순서대로 실행한다.
# 앞 Agent의 결과가 다음 Agent로 전달되는 Sequential Workflow를 확인한다.
HOL_ROOT = Path(__file__).resolve().parents[0]


async def create_workflow(project_client, credential):
    """Foundry UI에서 만든 Agent를 연결해 Sequential Workflow를 반환한다."""

    agent_names = (
        "travel-planner-user11",
        "budget-planner-user11",
        "travel-reviewer-user11",
        "travel-report-writer-user11",
    )
    agent_versions = {}
    async for agent in project_client.agents.list():
        if agent.name in agent_names:
            agent_versions[agent.name] = agent.versions.latest.version

    missing_agents = [
        agent_name for agent_name in agent_names if agent_name not in agent_versions
    ]
    if missing_agents:
        raise RuntimeError(
            "Foundry 프로젝트에서 Agent를 찾을 수 없습니다: "
            + ", ".join(missing_agents)
            + ". Foundry UI의 Agent 이름과 FOUNDRY_PROJECT_ENDPOINT를 확인하세요."
        )

    travel_planner = FoundryAgent(
        project_endpoint=os.environ["FOUNDRY_PROJECT_ENDPOINT"],
        agent_name=agent_names[0],
        agent_version=agent_versions[agent_names[0]],
        credential=credential,
    )

    budget_planner = FoundryAgent(
        project_endpoint=os.environ["FOUNDRY_PROJECT_ENDPOINT"],
        agent_name=agent_names[1],
        agent_version=agent_versions[agent_names[1]],
        credential=credential,
    )

    travel_reviewer = FoundryAgent(
        project_endpoint=os.environ["FOUNDRY_PROJECT_ENDPOINT"],
        agent_name=agent_names[2],
        agent_version=agent_versions[agent_names[2]],
        credential=credential,
    )

    travel_report_writer = FoundryAgent(
        project_endpoint=os.environ["FOUNDRY_PROJECT_ENDPOINT"],
        agent_name=agent_names[3],
        agent_version=agent_versions[agent_names[3]],
        credential=credential,
    )

    workflow = SequentialBuilder(
        participants=[travel_planner, budget_planner, travel_reviewer, travel_report_writer],
        # intermediate_output_from=[agent_customer, agent_billing, agent_network],
    ).build()

    return workflow


async def main() -> None:
    load_dotenv(HOL_ROOT / ".env")

    destination = input("여행 목적지 (기본: 일본 오사카): ").strip() or "일본 오사카"
    budget = input("2인 총예산 원 (기본: 2000000): ").strip() or "2000000"
    
    case = f"""
           [여행 요청]
            목적지: {destination}
            출발지: 인천
            여행 기간: 3박 4일
            인원: 성인 2명
            총예산: {budget}원 (2명 합계)
            여행 스타일: 관광 60%, 맛집 40%
            숙박: 3성급 이상 호텔
            이동: 대중교통 우선
            선호: 여유 있는 일정

            여행 일정을 수립하고 경비를 계산한 후 여행 지침을 검토하고 최종 여행 계획서를 작성하세요.
            """

    async with AzureCliCredential() as credential:
        async with AIProjectClient(
            endpoint=os.environ["FOUNDRY_PROJECT_ENDPOINT"],
            credential=credential,
        ) as project_client:
            workflow = await create_workflow(project_client, credential)

            print("\n[여행 Sequential Workflow 실행]")
            current_agent = None
            response_parts = []

            async for event in workflow.run(case, stream=True):
                if isinstance(event.data, AgentResponseUpdate):
                    update = event.data
                    if (
                        current_agent is not None
                        and update.author_name != current_agent
                    ):
                        print(f"[{current_agent}]\n{''.join(response_parts)}\n")
                        response_parts = []

                    current_agent = update.author_name
                    response_parts.append(update.text)

            if current_agent is not None and response_parts:
                print(f"[{current_agent}]\n{''.join(response_parts)}")


if __name__ == "__main__":
    asyncio.run(main())