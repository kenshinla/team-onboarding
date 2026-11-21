
import base64
import os
import webbrowser
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI


# 실습 의도:
# 이미지 생성 모델에 프롬프트를 보내고 결과 PNG를 저장한다.
# 이미지 생성과 이미지 이해는 서로 다른 작업임을 비교한다.
HOL_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = HOL_ROOT / "outputs" / "generated_images"


def create_client() -> OpenAI:
    load_dotenv(HOL_ROOT / ".env")
    return OpenAI(
        base_url=os.environ["AZURE_OPENAI_ENDPOINT_IMAGE"],
        api_key=os.environ["AZURE_OPENAI_API_KEY_IMAGE"],
    )


def generate_image(prompt: str) -> Path:
    """이미지를 생성하고 로컬 PNG 파일로 저장한다."""

    prompt = prompt.strip()
    if not prompt:
        raise ValueError("이미지 프롬프트가 비어 있습니다.")

    load_dotenv(HOL_ROOT / ".env")
    deployment = os.environ["IMAGE_MODEL_DEPLOYMENT"]
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = OUTPUT_DIR / f"{datetime.now():%Y%m%d_%H%M%S_%f}.png"

    result = create_client().images.generate(
        model=deployment,
        prompt=prompt,
        size=os.getenv("IMAGE_SIZE", "1024x1024"),
        quality=os.getenv("IMAGE_QUALITY", "low"),
        n=1,
    )
    image = result.data[0]

    image_bytes = base64.b64decode(image.b64_json)

    output_path.write_bytes(image_bytes)

    # 생성된 로컬 PNG 파일을 기본 브라우저에서 연다.
    webbrowser.open(output_path.resolve().as_uri())

    return output_path


def main() -> None:
    prompt = input("생성할 이미지 설명을 입력하세요: ").strip()
    print("생성된 파일:", generate_image(prompt))


if __name__ == "__main__":
    main()