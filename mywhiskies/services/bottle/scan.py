import base64
import io
import json
import re
from typing import Optional

import anthropic
from flask import current_app
from PIL import Image

from mywhiskies.models import BottleTypes

_TYPE_VALUES = ", ".join(t.value for t in BottleTypes)

_PROMPT = """You are analyzing one or more whiskey bottle label images.

Extract as much information as you can from the labels.
Return ONLY a JSON object with these keys (omit any you cannot determine):

- name: the bottle name as a collector would refer to it — include the distillery name, omit legal \
style descriptors (e.g. "Straight", "Kentucky") and marketing sub-labels \
(e.g. "Private Barrel Select", "Distiller's Reserve") unless they are the primary product name. \
Example: "Frey Ranch Barrel Strength Rye" not \
"Straight Rye Whiskey Barrel Strength Single Barrel - Distiller's Reserve Private Barrel Select" (string)
- distillery: the distillery name (string)
- bottler: the bottler name if different from the distillery (string)
- type: one of exactly: {type_values}
- abv: alcohol by volume as a float, e.g. 45.0 (not a string)
- size: bottle size in ml as an integer, e.g. 750
- year_barrelled: four-digit year as an integer
- year_bottled: four-digit year as an integer
- is_single_barrel: true if the bottle is explicitly labeled as a single barrel, otherwise false (boolean)
- description: a concise 3-5 sentence description in third person. Include the mash bill if known, \
any age statement, and general tasting notes. Draw on general knowledge of the distillery/expression \
if not visible on the label.

Return only the JSON object, no explanation, no markdown fences.""".format(type_values=_TYPE_VALUES)


_MAX_BYTES = 9 * 1024 * 1024  # 9 MB — stay comfortably under Anthropic's 10 MB limit


def _shrink_if_needed(data: bytes) -> bytes:
    if len(data) <= _MAX_BYTES:
        return data
    img = Image.open(io.BytesIO(data))
    if img.mode not in ("RGB", "L"):
        img = img.convert("RGB")
    scale = 0.8
    while True:
        w = max(1, int(img.width * scale))
        h = max(1, int(img.height * scale))
        resized = img.resize((w, h), Image.LANCZOS)
        buf = io.BytesIO()
        resized.save(buf, format="JPEG", quality=85)
        result = buf.getvalue()
        if len(result) <= _MAX_BYTES or (w <= 200 and h <= 200):
            return result
        scale *= 0.8


def scan_bottle_label(images: list[tuple[bytes, str]]) -> Optional[dict]:
    """Scan one or more bottle label images and return extracted fields.

    images: list of (image_data, mime_type) tuples
    """
    api_key = current_app.config.get("ANTHROPIC_API_KEY", "")
    if not api_key or not images:
        return None

    client = anthropic.Anthropic(api_key=api_key)

    content = []
    for image_data, mime_type in images:
        image_data = _shrink_if_needed(image_data)
        b64 = base64.standard_b64encode(image_data).decode("utf-8")
        content.append(
            {
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": mime_type,
                    "data": b64,
                },
            }
        )
    content.append({"type": "text", "text": _PROMPT})

    try:
        message = client.messages.create(
            model="claude-opus-4-7",
            max_tokens=512,
            messages=[{"role": "user", "content": content}],
        )
    except anthropic.APIError:
        current_app.logger.exception("Anthropic API error during label scan")
        return None

    raw = message.content[0].text.strip()
    raw = re.sub(r"^```[a-z]*\n?", "", raw)
    raw = re.sub(r"\n?```$", "", raw)

    try:
        return json.loads(raw)
    except (json.JSONDecodeError, ValueError):
        current_app.logger.warning(f"Label scan returned non-JSON: {raw!r}")
        return None
