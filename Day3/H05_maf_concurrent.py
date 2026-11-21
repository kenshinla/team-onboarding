"""H05 MAF Concurrent Workflow."""

import asyncio
import os
from pathlib import Path

from agent_framework import AgentResponseUpdate
from agent_framework.foundry import FoundryAgent
from agent_framework.orchestrations import ConcurrentBuilder
from azure.ai.projects.aio import AIProjectClient
from azure.identity.aio import AzureCliCredential
from dotenv import load_dotenv


# 고객, 요금, 네트워크 전문 Agent가 같은 입력을 동시에 처리한다.
HOL_ROOT = Path(__file__).resolve().parents[0]


async def create_workflow(project_client, credential):
    """Foundry UI에서 만든 Agent를 연결해 Concurrent Workflow를 반환한다."""

    agent_names = (
        # 고객 ID로 고객 상품과 서비스 상태를 찾아 핵심 사실을 정리하세요.
        "hol-day3-h04-customer-user11",
        # 고객 ID로 청구 정보를 찾아 요금 증가 내역과 근거를 정리하세요.
        "hol-day3-h04-billing-user11",
        # 고객 지역의 장애 정보를 찾아 속도 저하와의 관련성을 정리하세요.
        "hol-l02-data-incidents-user11",
    )
    agent_versions = {}
    async for agent in project_client.agents.list():
        if agent.name in agent_names:
            agent_versions[agent.name] = agent.versions.latest.version


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

    workflow = ConcurrentBuilder(
        participants=[agent_customer, agent_billing, agent_network],
        output_from="all",
    ).build()

    return workflow


async def main() -> None:
    load_dotenv(HOL_ROOT / ".env")
    customer_id = input("고객 ID를 입력하세요 (KT-C001): ").strip().upper()
    case = f"""
고객 ID: {customer_id}
인터넷 속도 저하와 요금 증가 가능성을 각각 조사하세요.
각 전문 Agent는 자신에게 해당하는 정보를 Foundry UI에 설정된 File Search로 찾으세요.
검색으로 확인되지 않은 내용은 추측하지 마세요.
"""

    async with AzureCliCredential() as credential:
        async with AIProjectClient(
            endpoint=os.environ["FOUNDRY_PROJECT_ENDPOINT"],
            credential=credential,
        ) as project_client:
            workflow = await create_workflow(project_client, credential)

            print("\n[Concurrent Workflow 실행]")
            print("세 전문 Agent가 동시에 실행됩니다.\n")
            responses = {}

            async for event in workflow.run(case, stream=True):
                if isinstance(event.data, AgentResponseUpdate):
                    update = event.data
                    responses.setdefault(update.author_name, []).append(update.text)

            for agent_name, response_parts in responses.items():
                print(f"[{agent_name}]\n{''.join(response_parts)}\n")


if __name__ == "__main__":
    asyncio.run(main())
