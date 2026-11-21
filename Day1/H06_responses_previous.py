from azure.ai.projects import AIProjectClient
from azure.identity import AzureCliCredential

ENDPOINT="https://proj-hol-t-resource.services.ai.azure.com/api/projects/proj-hol-t"
MODEL = "gpt-6-astra"
def run_step1(openai_client) -> str:
    """미리 정한 세 질문을 previous_response_id로 연결한다."""

    # 첫 번째 질문: 대화를 시작하므로 previous_response_id가 없다.
    first = openai_client.responses.create(
        model=MODEL,
        input="주말 아침에 간단하게 만들 수 있는 메뉴를 하나 추천해 주세요.",
    )
    print("[첫 번째 응답]\n" + first.output_text)
    print("response id:", first.id)

    # 두 번째 질문: 첫 번째 응답의 ID로 같은 대화를 이어 간다.
    second = openai_client.responses.create(
        model=MODEL,
        previous_response_id=first.id,
        input="그 메뉴를 만들 때 필요한 재료를 알려 주세요.",
    )
    print("\n[두 번째 응답]\n" + second.output_text)

    # 세 번째 질문: 두 번째 응답의 ID를 다시 사용한다.
    third = openai_client.responses.create(
        model=MODEL,
        previous_response_id=second.id,
        input="처음 요리하는 사람도 따라 할 수 있게 조리 순서를 설명해 주세요.",
    )
    print("\n[세 번째 응답]\n" + third.output_text)
    return third.id


def run_step2(openai_client, response_id: str) -> None:
    """마지막 응답 ID를 사용해 반복 입력형 대화를 실행한다."""

    print("\n[Step 2: 반복 대화]")
    print("대화를 계속 입력하세요. 종료하려면 quit 또는 exit를 입력합니다.")

    while True:
        question = input("\n사용자: ").strip()
        if question.lower() in {"quit", "exit"}:
            print("반복 대화를 종료합니다.")
            break
        if not question:
            continue

        response = openai_client.responses.create(
            model=MODEL,
            previous_response_id=response_id,
            input=question,
        )
        print("Agent:", response.output_text)

        # 다음 질문은 방금 받은 응답 ID를 기준으로 연결한다.
        response_id = response.id


def main() -> None:
    project_client = AIProjectClient(
        endpoint=ENDPOINT,
        credential=AzureCliCredential(),
    )
    openai_client = project_client.get_openai_client()

    # Step 1에서 마지막 응답 ID를 얻고, 같은 대화를 Step 2로 이어 간다.
    response_id = run_step1(openai_client)
    run_step2(openai_client, response_id)
    
if __name__ == "__main__":
    main()