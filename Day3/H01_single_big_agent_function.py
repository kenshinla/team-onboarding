import json
import os
from pathlib import Path

from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import FileSearchTool, FunctionTool, PromptAgentDefinition
from azure.identity import AzureCliCredential
from dotenv import load_dotenv
from openai.types.responses.response_input_param import FunctionCallOutput
HOL_ROOT = Path(__file__).resolve().parents[0]
DATA_FILE = HOL_ROOT.parent / "Day3//hol_l02_data.json"
AGENT_NAME = "day3-h01-single-big-agent-test"

def create_function_tools() -> list[FunctionTool]:
    return [
        FunctionTool(
            name="get_customer_profile",
            description="고객 ID로 상품과 고객 상태를 조회한다.",
            parameters={
                "type": "object",
                "properties": {"customer_id": {"type": "string"}},
                "required": ["customer_id"],
                "additionalProperties": False,
            },
            strict=True,
        ),
        FunctionTool(
            name="get_billing_summary",
            description="고객 ID로 요금과 청구 정보를 조회한다.",
            parameters={
                "type": "object",
                "properties": {"customer_id": {"type": "string"}},
                "required": ["customer_id"],
                "additionalProperties": False,
            },
            strict=True,
        ),
        FunctionTool(
            name="get_incident_status",
            description="지역의 네트워크 장애 정보를 조회한다.",
            parameters={
                "type": "object",
                "properties": {"region": {"type": "string"}},
                "required": ["region"],
                "additionalProperties": False,
            },
            strict=True,
        ),
    ]

def execute_tool(name: str, arguments: dict, data: dict) -> dict | list:
    """Agent가 요청한 업무 Tool을 교육용 JSON 데이터로 실행한다."""

    if name == "get_customer_profile":
        customer_id = arguments["customer_id"].strip().upper()
        return data["customers"].get(customer_id, {"error": "고객을 찾을 수 없습니다."})

    if name == "get_billing_summary":
        customer_id = arguments["customer_id"].strip().upper()
        return data["billing"].get(customer_id, {"error": "요금 정보를 찾을 수 없습니다."})

    if name == "get_incident_status":
        region = arguments["region"].strip()
        matches = [item for item in data["incidents"] if item["region"] == region]
        return matches or [{"error": "장애 정보를 찾을 수 없습니다."}]

    return {"error": f"지원하지 않는 Tool입니다: {name}"}

def create_or_get_agent(project_client, model: str):
    """같은 이름의 Agent를 재사용하고 없으면 새 버전을 만든다."""

    for existing in project_client.agents.list():
        if existing.name == AGENT_NAME:
            print("기존 Agent 재사용:", AGENT_NAME)
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
                "고객, 요금, 장애 Tool을 필요한 만큼 사용하세요. "
                "문서 정책 질문은 File Search 결과를 근거로 답하세요. "
                "확인하지 못한 내용은 추측하지 마세요."
            ),
            tools=[*create_function_tools()],
        ),
    )
    return {
        "name": agent.name,
        "version": agent.version,
        "type": "agent_reference",
    }

def run_agent(question: str) -> str:
    load_dotenv(HOL_ROOT / ".env")
    data = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    credential = AzureCliCredential()
    project_client = AIProjectClient(
        endpoint=os.environ["FOUNDRY_PROJECT_ENDPOINT"],
        credential=credential,
    )
    openai_client = project_client.get_openai_client()

    agent = create_or_get_agent(
            project_client,
            os.environ["FONUDRY_MODEL_DEPLOYMENT"]
        )
    
    agent_reference = agent
    conversation = openai_client.conversations.create()
    response = openai_client.responses.create(
        input=question,
        conversation=conversation.id,
        extra_body={"agent_reference": agent_reference},
    )

    while True:
        tool_outputs = []
        for item in response.output:
            if item.type != "function_call":
                continue
            arguments = json.loads(item.arguments)
            result = execute_tool(item.name, arguments, data)
            print("Tool 호출:", item.name, arguments)
            tool_outputs.append(
                FunctionCallOutput(
                    type="function_call_output",
                    call_id=item.call_id,
                    output=json.dumps(result, ensure_ascii=False),
                )
            )

        if not tool_outputs:
            return response.output_text

        response = openai_client.responses.create(
            input=tool_outputs,
            conversation=conversation.id,
            extra_body={"agent_reference": agent_reference},
            )

def main() -> None:
    question = input("질문을 입력하세요: ").strip()
    print("\nAgent 응답:\n", run_agent(question))


if __name__ == "__main__":
    main()