
from E02_speech_stt_functions import recognize_microphone_once


def main() -> None:
    print("\nHOL16 | Speech-to-Text")
    print("마이크에 한 문장 말해보세요. 잠시 멈추면 인식이 완료됩니다.\n")
    input("Enter를 누르면 마이크 입력을 시작합니다...")

    text = recognize_microphone_once()
    if text:
        print(f"\n인식 결과: {text}")
    else:
        print("\n음성이 인식되지 않았습니다. 마이크와 발화를 확인하세요.")


if __name__ == "__main__":
    main()