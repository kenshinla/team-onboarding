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
HOL_ROOT = Path(__file__).resolve().parents[1]


async def create_workflow(project_client, credential):
    """Foundry UI에서 만든 Agent를 연결해 Sequential Workflow를 반환한다."""

    agent_names = (
        # 고객 ID로 고객 상품과 서비스 상태를 찾아 핵심 사실을 정리하세요.
        "hol-day3-h04-customer-user11",
        # 고객 ID로 청구 정보를 찾아 요금 증가 내역과 근거를 정리하세요.
        "hol-day3-h04-billing-user11",
        # 고객 지역의 장애 정보를 찾아 속도 저하와의 관련성을 정리하세요.
        "hol-l02-data-incidents-user11",
        # 앞선 결과를 종합하고 확인된 사실과 미확인 내용을 구분해 답변하세요.
        "hol-day3-h04-main-user11",
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

    agent_customer = FoundryAgent(
        project_endpoint=os.environ["FOUNDRY_PROJECT_ENDPOINT"],
        agent_name=agent_names[0],
        agent_version=agent_versions[agent_names[0]],
        credential=credential,
    )

    agent_billing = FoundryAgent(
        project_endpoint=os.environ["FOUNDRY_PROJECT_ENDPOINT"],
        agent_name=agent_names[1],
        agent_version=agent_versions[agent_names[1]],
        credential=credential,
    )

    agent_network = FoundryAgent(
        project_endpoint=os.environ["FOUNDRY_PROJECT_ENDPOINT"],
        agent_name=agent_names[2],
        agent_version=agent_versions[agent_names[2]],
        credential=credential,
    )

    agent_main = FoundryAgent(
        project_endpoint=os.environ["FOUNDRY_PROJECT_ENDPOINT"],
        agent_name=agent_names[3],
        agent_version=agent_versions[agent_names[3]],
        credential=credential,
    )

    workflow = SequentialBuilder(
        participants=[agent_customer, agent_billing, agent_network, agent_main],
        # intermediate_output_from=[agent_customer, agent_billing, agent_network],
    ).build()

    return workflow


async def main() -> None:
    load_dotenv(HOL_ROOT / ".env")
    customer_id = input("고객 ID를 입력하세요 (KT-C001): ").strip().upper()
    case = f"""
            고객 ID: {customer_id}
            이 고객의 인터넷 속도 저하와 요금 증가 원인을 조사하세요.
            각 Agent에 설정된 File Search를 사용해 필요한 정보를 직접 찾으세요.
            검색으로 확인되지 않은 내용은 추측하지 마세요.
            """

    async with AzureCliCredential() as credential:
        async with AIProjectClient(
            endpoint=os.environ["FOUNDRY_PROJECT_ENDPOINT"],
            credential=credential,
        ) as project_client:
            workflow = await create_workflow(project_client, credential)

            print("\n[Sequential Workflow 실행]")
            current_agent = None
            response_parts = []

            async for event in workflow.run(case, stream=True):
                if isinstance(event.data, AgentgResponseUpdate):
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