import json
import os
from pathlib import Path

from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import FunctionTool, PromptAgentDefinition
from azure.identity import AzureCliCredential
from dotenv import load_dotenv
from openai.types.responses.response_input_param import FunctionCallOutput


HOL_ROOT = Path(__file__).resolve().parents[0]
#DATA_FILE = Path(r"G:\OneDrive\2026\MS-강의\TT-Proj\...\hol_l02_data.json")
DATA_FILE = HOL_ROOT / "hol_l02_data.json"
AGENT_NAME = "day2-h09-business-tools-agent-user11"


CUSTOMER_TOOL = FunctionTool(
    name="get_customer_profile",
    description="고객 ID로 가입 상품, 속도, 상태, 지역을 조회한다.",
    parameters={
        "type": "object",
        "properties": {
            "customer_id": {
                "type": "string",
                "description": "고객 ID 예: KT-C001",
            }
        },
        "required": ["customer_id"],
        "additionalProperties": False,
    },
    strict=True,
)

BILLING_TOOL = FunctionTool(
    name="get_billing_summary",
    description="고객 ID로 이전·현재 청구액과 요금 변경 사유를 조회한다.",
    parameters={
        "type": "object",
        "properties": {
            "customer_id": {"type": "string", "description": "고객 ID 예: KT-C001"}
        },
        "required": ["customer_id"],
        "additionalProperties": False,
    },
    strict=True,
)

INCIDENT_TOOL = FunctionTool(
    name="get_incident_status",
    description="지역명으로 해당 지역의 인터넷 장애 현황을 조회한다.",
    parameters={
        "type": "object",
        "properties": {
            "region": {"type": "string", "description": "지역명 예: 서울시 강남구"}
        },
        "required": ["region"],
        "additionalProperties": False,
    },
    strict=True,
)

FUNCTION_TOOLS = [CUSTOMER_TOOL, BILLING_TOOL, INCIDENT_TOOL]


def create_or_get_agent(project_client: AIProjectClient, model: str):
    """이름으로 Agent를 검색하고 없을 때 세 가지 Tool을 등록한다."""

    for existing_agent in project_client.agents.list():
        if existing_agent.name == AGENT_NAME:
            print("기존 Agent 사용:", existing_agent.name)
            agent = project_client.agents.get(agent_name=AGENT_NAME)
            return {
                "name": agent.name,
                "version": agent.versions.latest.version,
                "type": "agent_reference",
            }

    agent = project_client.agents.create_version(
        agent_name=AGENT_NAME,
        definition=PromptAgentDefinition(
            model=model,
            instructions=(
                "고객 정보는 get_customer_profile, 요금 정보는 get_billing_summary, "
                "지역 장애는 get_incident_status를 호출하세요. "
                "고객 ID나 지역명이 없으면 먼저 질문하세요. "
                "복합 질문에는 필요한 Tool을 모두 호출한 뒤 결과를 종합하세요. "
                "Tool 결과에 없는 내용은 추측하지 마세요. 데이터는 교육용 가상 정보입니다."
            ),
            tools=FUNCTION_TOOLS,
        ),
    )
    return {
        "name": agent.name,
        "version": agent.version,
        "type": "agent_reference",
    }


def execute_tool(tool_name: str, arguments: dict, data: dict) -> dict | list:
    """Agent가 요청한 Tool을 로컬 교육 데이터로 실행한다."""

    if tool_name == "get_customer_profile":
        customer_id = arguments["customer_id"].strip().upper()
        return data["customers"].get(
            customer_id,
            {"error": "고객 정보를 찾을 수 없습니다."},
        )

    if tool_name == "get_billing_summary":
        customer_id = arguments["customer_id"].strip().upper()
        return data["billing"].get(
            customer_id,
            {"error": "고객 요금 정보를 찾을 수 없습니다."},
        )

    if tool_name == "get_incident_status":
        region = arguments["region"].strip()
        matches = [
            incident for incident in data["incidents"] if incident["region"] == region
        ]
        return matches or [{"error": "해당 지역 정보를 찾을 수 없습니다."}]

    return {"error": f"지원하지 않는 Tool입니다: {tool_name}"}


def main() -> None:
    load_dotenv(HOL_ROOT / ".env")
    data = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    print("교육용 데이터 로드 완료:", DATA_FILE)
    credential = AzureCliCredential()
    project_client = AIProjectClient(
        endpoint=os.environ["FOUNDRY_PROJECT_ENDPOINT"],
        credential=credential,
    )
    openai_client = project_client.get_openai_client()


    agent_reference = create_or_get_agent(project_client, os.environ["FOUNDRY_MODEL_DEPLOYMENT"])
    agent_body = {"agent_reference": agent_reference}
    conversation = openai_client.conversations.create()
    question = input("질문을 입력하세요: ").strip()

    response = openai_client.responses.create(
        input=question,
        conversation=conversation.id,
        extra_body=agent_body,
    )

    # Agent가 여러 Tool을 요청할 수 있으므로 Tool 호출이 끝날 때까지 반복한다.
    while True:
        tool_outputs = []
        for item in response.output:
            if item.type != "function_call":
                continue

            arguments = json.loads(item.arguments)
            result = execute_tool(item.name, arguments, data)
            print("Tool 호출:", item.name)
            print("Tool 인자:", arguments)
            print("Tool 결과:", result)
            tool_outputs.append(
                FunctionCallOutput(
                    type="function_call_output",
                    call_id=item.call_id,
                    output=json.dumps(result, ensure_ascii=False),
                )
            )

        if not tool_outputs:
            break

        response = openai_client.responses.create(
            input=tool_outputs,
            conversation=conversation.id,
            extra_body=agent_body,
        )

    print("\nAgent 답변:")
    print(response.output_text)
    openai_client.conversations.delete(conversation_id=conversation.id)



if __name__ == "__main__":
    main()