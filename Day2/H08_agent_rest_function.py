import json
import os
from pathlib import Path

import httpx
from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import FunctionTool, PromptAgentDefinition
from azure.identity import AzureCliCredential
from dotenv import load_dotenv
from openai.types.responses.response_input_param import FunctionCallOutput


HOL_ROOT = Path(__file__).resolve().parents[0]
AGENT_NAME = "day2-h08-rest-function-agent-user11"
API_URL = "http://127.0.0.1:8555"

CUSTOMER_TOOL = FunctionTool(
    name="get_customer",
    description="REST API에서 고객 정보를 조회한다.",
    parameters={"type": "object", "properties": {"customer_id": {"type": "string"}}, "required": ["customer_id"], "additionalProperties": False},
    strict=True,
)


def main() -> None:
    load_dotenv(HOL_ROOT / ".env")
    credential = AzureCliCredential()
    project_client = AIProjectClient(endpoint=os.environ["FOUNDRY_PROJECT_ENDPOINT"], credential=credential)
    openai_client = project_client.get_openai_client()
    agent = None
    agent_version = None
    
    for existing_agent in project_client.agents.list():
        if existing_agent.name == AGENT_NAME:
            agent = project_client.agents.get(agent_name=AGENT_NAME)
            agent_version = agent.versions.latest.version
            break
    if agent is None:
        agent = project_client.agents.create_version(
            agent_name=AGENT_NAME,
            definition=PromptAgentDefinition(
                model=os.environ["FOUNDRY_MODEL_DEPLOYMENT"],
                instructions="고객 질문에는 get_customer Tool을 사용하세요.",
                tools=[CUSTOMER_TOOL],
            ),
        )
        agent_version = agent.version

    reference = {"name": agent.name, "version": agent_version, "type": "agent_reference"}
    conversation = openai_client.conversations.create()
    response = openai_client.responses.create(
        conversation=conversation.id,
        input="C001 고객의 상품을 알려 주세요.",
        extra_body={"agent_reference": reference},
    )

    outputs = []
    for item in response.output:
        if item.type != "function_call":
            continue

        # 등록한 Function Tool만 실행한다.
        if item.name == CUSTOMER_TOOL.name:
            args = json.loads(item.arguments)
            customer_id = args.get("customer_id")
            #고객정보 조회 REST API 호출
            try:
                # http://127.0.0.1:8555/customers/C001
                with httpx.Client(timeout=5.0) as client:
                    api_response = client.get(f"{API_URL}/customers/{customer_id}")
                    api_response.raise_for_status()
                    result = api_response.json()
            except httpx.HTTPError as error:
                result = {"error": str(error)}
        else:
            print(f"알 수 없는 Function Tool 호출: {item.name}")
            continue
        
        outputs.append(FunctionCallOutput(type="function_call_output", call_id=item.call_id, output=json.dumps(result, ensure_ascii=False)))

    if outputs:
        response = openai_client.responses.create(conversation=conversation.id, input=outputs, extra_body={"agent_reference": reference})
    print(response.output_text)

if __name__ == "__main__":
    main()

