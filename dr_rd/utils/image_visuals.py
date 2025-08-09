"""Utilities for generating and storing project visuals."""

import base64
import os
import time
from io import BytesIO

from openai import OpenAI
from PIL import Image

from .storage_gcs import upload_bytes_to_gcs


def _openai():
    return OpenAI()


SCHEMATIC_PROMPT = (
    "Technical line-art schematic of the proposed prototype. "
    "Style: clean black lines on white background, labeled blocks, arrows for signal/power flow, no photorealism. "
    "Summarize and diagram the subsystems from this brief:\n\n{brief}"
)

RENDER_PROMPT = (
    "Photorealistic studio render of the prototype exterior on a neutral background. "
    "High detail, no text, perspective three-quarter view. Brief:\n\n{brief}"
)


def _decode_to_bytes(b64: str) -> bytes:
    return base64.b64decode(b64)


def _gen_image(prompt: str, fmt: str = "png", size: str = "1024x1024", quality: str = "high"):
    client = _openai()
    res = client.images.generate(
        model="gpt-image-1",
        prompt=prompt,
        size=size,
        output_format=("png" if fmt == "png" else "jpeg"),
        quality=quality,
    )
    return res.data[0].b64_json


def make_visuals_for_project(idea: str, plan_roles: list[str] | None, bucket: str | None) -> list[dict]:
    """Generate schematic and render images for a project."""

    brief = idea or ""
    if plan_roles:
        brief += "\n\nKey subsystems: " + ", ".join(plan_roles)

    items = [
        ("schematic", "png", SCHEMATIC_PROMPT.format(brief=brief)),
        ("appearance", "jpeg", RENDER_PROMPT.format(brief=brief)),
    ]
    out: list[dict] = []
    ts = str(int(time.time()))

    for kind, fmt, prompt in items:
        try:
            b64 = _gen_image(prompt, fmt=fmt)
            data = _decode_to_bytes(b64)

            img = Image.open(BytesIO(data))
            bio = BytesIO()
            if fmt == "png":
                img.save(bio, format="PNG", optimize=True)
                content_type = "image/png"
            else:
                img.save(bio, format="JPEG", quality=90, optimize=True)
                content_type = "image/jpeg"
            data = bio.getvalue()

            if bucket:
                filename = f"{ts}-{kind}.{fmt}"
                try:
                    url = upload_bytes_to_gcs(data, filename, content_type, bucket)
                except Exception:
                    url = f"data:{content_type};base64,{base64.b64encode(data).decode()}"
            else:
                url = f"data:{content_type};base64,{base64.b64encode(data).decode()}"

            out.append({"kind": kind, "url": url, "caption": kind.capitalize()})
        except Exception:
            continue

    return out

