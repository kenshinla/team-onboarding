import ctypes
import json
import os
import shutil
from pathlib import Path

from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import FunctionTool, PromptAgentDefinition
from azure.identity import AzureCliCredential
from dotenv import load_dotenv
from openai.types.responses.response_input_param import FunctionCallOutput

HOL_ROOT = Path(__file__).resolve().parents[0]
AGENT_NAME = "hol-common-t-test"

DISK_TOOL = FunctionTool(
    name="get_disk_info",
    description=(
        "사용자가 요청한 로컬 디스크의 볼륨 이름, 전체 용량, "
        "사용 공간, 남은 공간을 조회한다."
    ),
    parameters={
        "type": "object",
        "properties": {
            "disk_name": {
                "type": "string",
                "description": "조회할 Windows 디스크 문자. 예: C, D, E",
            }
        },
        "required": ["disk_name"],
        "additionalProperties": False,
    },
    strict=True,
)

def get_disk_info_(disk_name: str) -> dict:
    """Windows 로컬 디스크의 볼륨 이름과 용량 정보를 반환한다."""

    disk_letter = disk_name.strip().replace(":", "").upper()
    if len(disk_letter) != 1 or not disk_letter.isalpha():
        return {"error": "디스크 문자를 C, D와 같은 형식으로 입력하세요."}

    drive_root = f"{disk_letter}:\\"
    if not os.path.exists(drive_root):
        return {
            "error": f"{disk_letter} 디스크를 찾을 수 없습니다.",
            "disk_name": disk_letter,
        }

    total, used, free = shutil.disk_usage(drive_root)
    volume_name = ctypes.create_unicode_buffer(261)

    # Windows API로 디스크 볼륨 이름을 조회한다.
    get_volume_information = ctypes.windll.kernel32.GetVolumeInformationW
    get_volume_information(
        drive_root,
        volume_name,
        len(volume_name),
        None,
        None,
        None,
        None,
        0,
    )

    gib = 1024**3
    return {
        "disk_name": disk_letter,
        "volume_name": volume_name.value or "이름 없음",
        "total_gb": round(total / gib, 2),
        "used_gb": round(used / gib, 2),
        "free_gb": round(free / gib, 2),
        "free_percent": round((free / total) * 100, 2) if total else 0,
    }

def get_disk_info(disk_name: str) -> dict:
    """디스크 이름에 따른 고정 샘플 정보를 반환합니다."""
    disk_letter = disk_name.strip().replace(":", "").upper()

    if disk_letter == "C":
        return {
            "disk_name": "C",
            "volume_name": "System-SKS",
            "total_gb": 512,
            "used_gb": 256,
            "free_gb": 256,
            "free_percent": 50.0,
        }
    elif disk_letter == "D":
        return {
            "disk_name": "D",
            "volume_name": "Data-SKS",
            "total_gb": 1024,
            "used_gb": 600,
            "free_gb": 424,
            "free_percent": 41.41,
        }
    elif disk_letter == "E":
        return {
            "disk_name": "E",
            "volume_name": "Backup-SKS",
            "total_gb": 2048,
            "used_gb": 1200,
            "free_gb": 848,
            "free_percent": 41.41,
        }
    else:
        return {
            "error": "C, D, E 디스크만 조회할 수 있습니다.",
            "requested_disk": disk_name,
        }


def run_function(name: str, arguments: dict) -> dict:
    """모델이 요청한 함수 이름에 따라 실제 Python 함수를 실행한다."""

    if name != "get_disk_info":
        return {"error": "지원하지 않는 함수입니다."}

    disk_name = arguments.get("disk_name")
    if not isinstance(disk_name, str):
        return {"error": "disk_name은 문자열이어야 합니다."}

    return get_disk_info(disk_name)

def main() -> None:
    load_dotenv(HOL_ROOT / ".env")
    credential = AzureCliCredential()
    project_client = AIProjectClient(
        endpoint=os.environ["FOUNDRY_PROJECT_ENDPOINT"], credential=credential
    )
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
                instructions=(
                        "사용자가 로컬 디스크 용량을 질문하면 get_disk_info를 "
                        "호출하세요. 디스크 문자가 없으면 먼저 물어보세요."
                    ),
                tools=[DISK_TOOL],
                ),
        )
        agent_version = agent.version

    reference = {"name": agent.name, "version": agent_version, "type": "agent_reference"}
    conversation = openai_client.conversations.create()
    response = openai_client.responses.create(
        conversation=conversation.id,
        input="C 드라이브의 전체 용량과 남은 공간을 알려 주세요.",
        extra_body={"agent_reference": reference},
    )

    tool_outputs = []
    for item in response.output:
        if item.type != "function_call":
                continue
        arguments = json.loads(item.arguments)
        result = run_function(item.name, arguments)
        print("Tool 호출:", item.name, arguments)
        tool_outputs.append(
            FunctionCallOutput(
                type="function_call_output",
                call_id=item.call_id,
                output=json.dumps(result, ensure_ascii=False),
            )
        )

    if tool_outputs:
            response = openai_client.responses.create(
                conversation=conversation.id,
                input=tool_outputs,
                extra_body={"agent_reference": reference},
            )
    print(response.output_text)

if __name__ == "__main__":
    main()



        



