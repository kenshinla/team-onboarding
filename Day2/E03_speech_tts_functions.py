
from __future__ import annotations

import os
import html
from pathlib import Path

import azure.cognitiveservices.speech as speechsdk
from dotenv import load_dotenv


HOL_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(HOL_ROOT / ".env")


def create_speech_config() -> speechsdk.SpeechConfig:
    """환경 설정을 읽고 한국어 음성 합성용 설정을 만듭니다."""
    key = os.getenv("SPEECH_KEY")
    region = os.getenv("SPEECH_REGION")

    if not key or not region:
        raise RuntimeError(".env에 SPEECH_KEY와 SPEECH_REGION을 설정하세요.")

    config = speechsdk.SpeechConfig(subscription=key, region=region)
    config.speech_synthesis_voice_name = os.getenv(
        "SPEECH_VOICE", "ko-KR-SunHiNeural"
    )
    return config


def speak_to_default_speaker(text: str) -> None:
    """텍스트를 기본 스피커로 재생합니다. HOL17 콘솔 실습에서 사용합니다."""
    text = text.strip()
    if not text:
        raise ValueError("읽을 텍스트가 비어 있습니다.")

    synthesizer = speechsdk.SpeechSynthesizer(
        speech_config=create_speech_config()
    )
    result = synthesizer.speak_text_async(text).get()

    if result.reason != speechsdk.ResultReason.SynthesizingAudioCompleted:
        details = getattr(result, "cancellation_details", None)
        message = getattr(details, "error_details", "음성 합성에 실패했습니다.")
        raise RuntimeError(message)


def save_speech_to_wav(text: str, output_path: str | Path) -> Path:
    """텍스트 음성을 WAV 파일로 저장합니다."""
    text = text.strip()
    if not text:
        raise ValueError("읽을 텍스트가 비어 있습니다.")

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    audio_config = speechsdk.audio.AudioOutputConfig(filename=str(path))
    synthesizer = speechsdk.SpeechSynthesizer(
        speech_config=create_speech_config(),
        audio_config=audio_config,
    )
    result = synthesizer.speak_text_async(text).get()

    if result.reason != speechsdk.ResultReason.SynthesizingAudioCompleted:
        details = getattr(result, "cancellation_details", None)
        message = getattr(details, "error_details", "음성 합성에 실패했습니다.")
        raise RuntimeError(message)

    return path



def speak_with_emotion_to_default_speaker(
    emotion: str,
    text: str,
    styledegree: float = 2.0,
    rate: str | None = None,
    pitch: str | None = None,
    volume: str | None = None,
) -> None:
    """감정과 음성 효과를 지정해 SSML로 기본 스피커에서 재생합니다.

    Args:
        emotion: 중립, 즐겁게, 화나게, 슬프게, 신나게, 속삭이듯
        text: 읽을 문장
        styledegree: 감정 강도. SSML 허용 범위는 0.01~2.0
        rate: 말하기 속도. 예: "+15%", "-10%"
        pitch: 음높이. 예: "+8%", "-5%"
        volume: 음량. 예: "+10%", "-5%", "loud"
    """
    text = text.strip()
    if not text:
        raise ValueError("읽을 텍스트가 비어 있습니다.")

    if not 0.01 <= styledegree <= 2.0:
        raise ValueError("styledegree는 0.01부터 2.0 사이여야 합니다.")

    # 텍스트 안의 &, <, >가 SSML 태그로 해석되지 않게 처리합니다.
    safe_text = html.escape(text)

    config = create_speech_config()
    voice = config.speech_synthesis_voice_name

    # 예: ko-KR-Haena:MAI-Voice-2.1 -> ko-KR
    #     ko-KR-SunHiNeural        -> ko-KR
    voice_parts = voice.split("-")
    locale = "-".join(voice_parts[:2])

    # 한국어 MAI Haena 음성에서 지원되는 스타일명 사용
    emotion_styles = {
        "중립": None,
        "즐겁게": "happy",
        "화나게": "angry",
        "슬프게": "sad",
        "신나게": "excited",
        "속삭이듯": "softvoice",
    }

    if emotion not in emotion_styles:
        choices = ", ".join(emotion_styles)
        raise ValueError(f"지원하는 감정: {choices}")

    style = emotion_styles[emotion]

    # 속도, 음높이, 음량 설정을 SSML 속성으로 만듭니다.
    prosody_attributes = []
    if rate is not None:
        prosody_attributes.append(f'rate="{rate}"')
    if pitch is not None:
        prosody_attributes.append(f'pitch="{pitch}"')
    if volume is not None:
        prosody_attributes.append(f'volume="{volume}"')

    if prosody_attributes:
        attributes = " ".join(prosody_attributes)
        spoken_text = f"<prosody {attributes}>{safe_text}</prosody>"
    else:
        spoken_text = safe_text

    if style is not None:
        spoken_text = (
            f'<mstts:express-as style="{style}" '
            f'styledegree="{styledegree}">'
            f"{spoken_text}"
            "</mstts:express-as>"
        )

    ssml = (
        '<speak version="1.0" '
        'xmlns="http://www.w3.org/2001/10/synthesis" '
        'xmlns:mstts="http://www.w3.org/2001/mstts" '
        f'xml:lang="{locale}">'
        f'<voice name="{voice}">{spoken_text}</voice>'
        "</speak>"
    )

    synthesizer = speechsdk.SpeechSynthesizer(
        speech_config=config
    )
    result = synthesizer.speak_ssml_async(ssml).get()

    if result.reason != speechsdk.ResultReason.SynthesizingAudioCompleted:
        details = getattr(result, "cancellation_details", None)
        message = getattr(
            details,
            "error_details",
            "SSML 음성 합성에 실패했습니다.",
        )
        raise RuntimeError(message)