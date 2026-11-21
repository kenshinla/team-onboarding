from azure.ai.projects import AIProjectClient
from azure.identity import AzureCliCredential

Agent_NAME = "day1-h13-basic-agent"
def main() -> None :
    endpoint = "https://proj-hol-t-resource.services.ai.azure.com/api/projects/proj-hol-t"

    credential = AzureCliCredential()
    project_client = AIProjectClient(endpoint=endpoint, credential=credential)
    openai_client = project_client.get_openai_client()
    agent = project_client.agents.get(agent_name=Agent_NAME)

    agent_reference = {
        "name" : agent.name,
        "version" : agent.versions.latest.version,
        "type": "agent_reference",
    }
    conversation = openai_client.conversations.create()
    response = openai_client.responses.create(
        conversation=conversation.id,
        input="Microsoft Foundry Agent가 ChatApp와 다른 점을 설명해 주세요. 5줄 이하로 설명해주세요.",
        extra_body={"agent_reference" : agent_reference},
    )
    print("\n[Agent 응답]\n" + response.output_text)
    print("\n[Agent Usage]\n" + str(response.usage))

if __name__ == "__main__":
    main()