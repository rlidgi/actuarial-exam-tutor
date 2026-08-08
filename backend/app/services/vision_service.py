"""Live, on-demand transcription of a student's uploaded problem screenshot
into text the tutor loop can treat as a normal typed question -- the image
itself never reaches tutor_service/dispatch.py, only this transcription
does.
"""
import base64
import io

from flask import current_app
from openai import OpenAI
from PIL import Image

TRANSCRIBE_PROMPT = (
    "Transcribe this image of a practice problem to Markdown, using LaTeX for all math: "
    "$...$ for inline expressions, $$...$$ for standalone equations. Preserve the exact "
    "wording, numbers, and any multiple-choice answer options exactly as shown. Do not "
    "solve the problem or add commentary -- output only the transcription."
)

# OpenAI's vision pipeline scales any input down to fit within a 2048x2048
# box before tiling it for the model, so a phone photo far larger than that
# costs more to upload and encode without buying any extra transcription
# accuracy -- pre-shrinking to this size locally is pure savings.
_MAX_DIMENSION = 2048
_JPEG_QUALITY = 85


def downscale_image(image_bytes: bytes) -> tuple[bytes, str]:
    img = Image.open(io.BytesIO(image_bytes))
    img = img.convert("RGB")  # drop alpha -- JPEG doesn't support it
    if max(img.size) > _MAX_DIMENSION:
        img.thumbnail((_MAX_DIMENSION, _MAX_DIMENSION), Image.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=_JPEG_QUALITY)
    return buf.getvalue(), "image/jpeg"


def transcribe_image(image_bytes: bytes, mime_type: str) -> str:
    """image_bytes is expected to already be downscale_image()'d by the
    caller."""
    client = OpenAI(api_key=current_app.config["OPENAI_API_KEY"])
    b64 = base64.b64encode(image_bytes).decode()
    resp = client.chat.completions.create(
        model=current_app.config["VISION_MODEL"],
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": TRANSCRIBE_PROMPT},
                    {"type": "image_url", "image_url": {"url": f"data:{mime_type};base64,{b64}"}},
                ],
            }
        ],
    )
    return resp.choices[0].message.content
