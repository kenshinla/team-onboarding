
from E03_speech_tts_functions import speak_to_default_speaker, speak_with_emotion_to_default_speaker


def main() -> None:
    print("\nHOL17 | Text-to-Speech")
    text = input("음성으로 들을 문장을 입력하세요: ").strip()

    if not text:
        print("입력 문장이 비어 있어 종료합니다.")
        return

    print("\n음성을 생성하고 재생합니다...")
    speak_to_default_speaker(text)
    #speak_with_emotion_to_default_speaker("화나게", text)
    #speak_with_emotion_to_default_speaker("슬프게", text)
    #speak_with_emotion_to_default_speaker("속삭이듯", text) 

    # # 감정 강도 최댓값
    # speak_with_emotion_to_default_speaker(
    #     "화나게",
    #     "지금 당장 멈춰 주세요!",
    #     styledegree=1.0,
    # )

    # # 감정 강도 + 속도 + 음높이
    # speak_with_emotion_to_default_speaker(
    #     "화나게",
    #     "지금 당장 멈춰 주세요!",
    #     styledegree=2.0,
    #     rate="+15%",
    #     pitch="+8%",
    # )

    # # 속삭이는 스타일
    # speak_with_emotion_to_default_speaker(
    #     "속삭이듯",
    #     "조용히 말씀드릴게요.",
    #     styledegree=2.0,
    #     rate="-10%",
    # )

    #     # 속삭이는 스타일
    # speak_with_emotion_to_default_speaker(
    #     "속삭이듯",
    #     "지금 당장 멈춰 주세요!",
    #     styledegree=2.0,
    #     rate="-10%",
    # )

    # daily_routine = (
    # "I wake up at seven in the morning. "
    # "I have breakfast and drink a cup of coffee. "
    # "I go to work and meet my team. "
    # "After work, I have dinner and relax at home."
    # )

    # speak_with_emotion_to_default_speaker("속삭이듯", daily_routine, styledegree=2.0)
    # speak_with_emotion_to_default_speaker("신나게", daily_routine, styledegree=2.0)
    # speak_with_emotion_to_default_speaker("즐겁게", daily_routine, styledegree=2.0)
    # speak_with_emotion_to_default_speaker("화나게", daily_routine, styledegree=2.0)
    # speak_with_emotion_to_default_speaker("슬프게", daily_routine, styledegree=2.0)


    print("재생이 완료되었습니다.")


if __name__ == "__main__":
    main()