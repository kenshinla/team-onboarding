
import os
from pathlib import Path

import azure.cognitiveservices.speech as speechsdk
from dotenv import load_dotenv


HOL_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(HOL_ROOT / ".env")

def create_speech_config() -> speechsdk.SpeechConfig:
    """환경 설정을 읽고 Speech SDK 설정 객체를 만듭니다."""
    key = os.getenv("SPEECH_KEY")
    region = os.getenv("SPEECH_REGION")

    if not key or not region:
        raise RuntimeError(".env에 SPEECH_KEY와 SPEECH_REGION을 설정하세요.")

    config = speechsdk.SpeechConfig(subscription=key, region=region)
    config.speech_recognition_language = os.getenv("SPEECH_LANGUAGE", "ko-KR")
    return config


def recognize_microphone_once() -> str:
    """기본 마이크에서 한 번 발화한 내용을 인식해 문자열로 반환합니다.

    인식은 무음이 감지되면 끝납니다. 긴 오디오의 연속 전사는 별도 방식이 필요합니다.
    """
    recognizer = speechsdk.SpeechRecognizer(speech_config=create_speech_config())
    result = recognizer.recognize_once_async().get()

    if result.reason == speechsdk.ResultReason.RecognizedSpeech:
        return result.text.strip()

    if result.reason == speechsdk.ResultReason.NoMatch:
        return ""

    details = getattr(result, "cancellation_details", None)
    message = getattr(details, "error_details", "Speech 인식이 취소되었습니다.")
    raise RuntimeError(message)


def transcribe_wav(wav_path: str | Path) -> str:
    """HOL18 등에서 WAV 파일을 전달해 음성 인식 결과를 반환합니다."""
    path = Path(wav_path)
    if not path.is_file():
        raise FileNotFoundError(path)

    audio_config = speechsdk.audio.AudioConfig(filename=str(path))
    recognizer = speechsdk.SpeechRecognizer(
        speech_config=create_speech_config(),
        audio_config=audio_config,
    )
    result = recognizer.recognize_once_async().get()

    if result.reason == speechsdk.ResultReason.RecognizedSpeech:
        return result.text.strip()

    if result.reason == speechsdk.ResultReason.NoMatch:
        return ""

    details = getattr(result, "cancellation_details", None)
    message = getattr(details, "error_details", "Speech 인식이 취소되었습니다.")
    raise RuntimeError(message)