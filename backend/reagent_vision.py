"""
Reagent test analysis — vision (hex extraction) and deterministic color matching.
Requires OPENAI_API_KEY for GPT-4o vision. Color matching is purely deterministic.
"""
from __future__ import annotations

import json
import logging
import os
import re
from typing import Any

logger = logging.getLogger("reagent-vision")


class ReagentVisionQuotaError(Exception):
    """Raised when the vision API fails due to quota/billing (429)."""
    pass


# Predefined reagent reaction colors (hex) for common reagents. Substance name -> hex.
# Euclidean distance in RGB space is used to find closest matches.
REAGENT_COLORS: dict[str, str] = {
    "MDMA (Marquis)": "#4B0082",
    "Amphetamine (Marquis)": "#E6B800",
    "LSD (Ehrlich)": "#6B2D5C",
    "Cocaine (Scott)": "#1E3A5F",
    "Heroin (Marquis)": "#6B2D5C",
    "Morphine (Marquis)": "#4B0082",
    "Ketamine (Mandelin)": "#8B4513",
    "DMT (Ehrlich)": "#4B0082",
    "2C-B (Marquis)": "#4B0082",
    "Methamphetamine (Simon's)": "#006400",
    "Negative/No reaction": "#F5F5DC",
    "Inconclusive": "#808080",
}


def hex_to_rgb(hex_str: str) -> tuple[int, int, int]:
    """Convert #RRGGBB to (R, G, B) 0-255."""
    hex_str = hex_str.strip().lstrip("#")
    if len(hex_str) != 6:
        raise ValueError(f"Invalid hex: {hex_str}")
    r = int(hex_str[0:2], 16)
    g = int(hex_str[2:4], 16)
    b = int(hex_str[4:6], 16)
    return (r, g, b)


def rgb_distance(a: tuple[int, int, int], b: tuple[int, int, int]) -> float:
    """Euclidean distance between two RGB tuples."""
    return (sum((x - y) ** 2 for x, y in zip(a, b))) ** 0.5


def match_hex_to_substances(hex_code: str, top_k: int = 3) -> list[dict[str, Any]]:
    """
    Deterministic matching: compute Euclidean distance from extracted hex to predefined
    reagent colors. Return top_k closest substances with probability percentages.
    Probability is derived from inverse distance, normalized so top matches sum to 100%.
    """
    try:
        target = hex_to_rgb(hex_code)
    except (ValueError, TypeError):
        return []

    distances: list[tuple[str, float]] = []
    for substance, ref_hex in REAGENT_COLORS.items():
        try:
            ref_rgb = hex_to_rgb(ref_hex)
            d = rgb_distance(target, ref_rgb)
            distances.append((substance, d))
        except ValueError:
            continue

    if not distances:
        return []

    distances.sort(key=lambda x: x[1])
    top = distances[:top_k]
    # Inverse distance as score; normalize to percentages (avoid div by zero)
    max_d = max(d for _, d in top) or 1
    scores = [1.0 / (1.0 + d) for _, d in top]
    total = sum(scores)
    if total <= 0:
        total = 1.0
    probabilities = [round(100.0 * s / total, 1) for s in scores]
    # Normalize so they sum to 100
    diff = 100.0 - sum(probabilities)
    if diff != 0 and probabilities:
        probabilities[0] = round(probabilities[0] + diff, 1)

    return [
        {"substance": name, "probability": p}
        for (name, _), p in zip(top, probabilities)
    ]


def _normalize_hex(s: str) -> str | None:
    if not s or not isinstance(s, str):
        return None
    s = s.strip().lstrip("#")
    if len(s) != 6:
        return None
    if re.match(r"^[0-9A-Fa-f]{6}$", s):
        return "#" + s
    return None


def _parse_vision_json(content: str) -> dict[str, Any] | None:
    """Parse LLM JSON; return normalized dict with colors[], labels[], description or None."""
    content = (content or "").strip()
    # Strip markdown code block if present
    if content.startswith("```"):
        content = re.sub(r"^```(?:json)?\s*", "", content)
        content = re.sub(r"\s*```\s*$", "", content)
    try:
        obj = json.loads(content)
    except json.JSONDecodeError:
        return None
    if not isinstance(obj, dict):
        return None
    out: dict[str, Any] = {"colors": [], "labels": [], "description": None}
    # Description
    if isinstance(obj.get("description"), str) and obj["description"].strip():
        out["description"] = obj["description"].strip()
    # Labels: array of strings (visible text in image)
    labels = obj.get("labels")
    if isinstance(labels, list):
        out["labels"] = [str(x).strip() for x in labels if x and str(x).strip()]
    elif isinstance(obj.get("label"), str) and obj["label"].strip():
        out["labels"] = [obj["label"].strip()]
    # Colors: support single "hex" or "colors" array with { hex, label? }
    hex_single = obj.get("hex") or obj.get("hex_code")
    if isinstance(hex_single, str):
        h = _normalize_hex(hex_single)
        if h:
            out["colors"] = [{"hex": h, "label": None}]
            return out
    colors = obj.get("colors")
    if isinstance(colors, list):
        for c in colors:
            if isinstance(c, dict):
                h = _normalize_hex(str(c.get("hex") or c.get("hex_code") or ""))
                if h:
                    label = c.get("label")
                    out["colors"].append({"hex": h, "label": str(label).strip() if label else None})
            elif isinstance(c, str):
                h = _normalize_hex(c)
                if h:
                    out["colors"].append({"hex": h, "label": None})
    if out["colors"]:
        return out
    return None


async def extract_vision_from_image(
    image_bytes: bytes,
    user_prompt: str | None = None,
) -> dict[str, Any] | None:
    """
    Send image to GPT-4o vision. Extract:
    - colors: list of { hex, label? } for each reaction/liquid (multiple tubes or regions).
    - labels: any visible text (reagent name, bottle label, handwritten note).
    - description: optional short description of the scene.
    If user_prompt is provided, the model uses it to associate colors with the correct reagent/tube when possible.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key or not api_key.strip():
        logger.warning("OPENAI_API_KEY not set; cannot call vision API.")
        return None

    try:
        from openai import AsyncOpenAI
    except ImportError:
        logger.warning("openai package not installed; pip install openai")
        return None

    import base64
    client = AsyncOpenAI(api_key=api_key)
    b64 = base64.standard_b64encode(image_bytes).decode("ascii")
    data_uri = f"data:image/jpeg;base64,{b64}"

    system = (
        "You are analyzing a reagent drug test result image. Extract ONLY observable data; do not guess or name any drug. "
        "Return a JSON object with:\n"
        "1) \"colors\": an array of objects, each with \"hex\" (hex color code, e.g. \"#4B0082\") and optional \"label\" (e.g. reagent name or \"tube 1\"). "
        "If there is one main reaction color, use one object; if multiple tubes or regions, add one object per color.\n"
        "2) \"labels\": an array of any visible text in the image (reagent names on bottles, handwritten labels, kit name).\n"
        "3) \"description\": optional short description of the scene (e.g. \"Single test tube with purple liquid\", \"Multi-panel reagent kit\").\n"
        "Return ONLY valid JSON, no other text. For hex use 6-digit format with #."
    )

    user_text = "Return JSON with colors (array of {hex, label?}), labels (array of strings), and optional description."
    if user_prompt and user_prompt.strip():
        user_text = (
            "The user provided this description of what is in the image: \""
            + user_prompt.strip()[:500]
            + "\". Use it to label which reagent or tube each color corresponds to when possible (e.g. set \"label\" to the reagent name or tube the user refers to). "
            + user_text
        )

    try:
        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": user_text},
                        {"type": "image_url", "image_url": {"url": data_uri}},
                    ],
                },
            ],
            max_tokens=400,
        )
        content = (response.choices[0].message.content or "").strip()
        return _parse_vision_json(content)
    except Exception as e:
        logger.exception("Vision API error: %s", e)
        # Re-raise quota/billing errors so the API can return a clear message
        err_str = str(e).lower()
        if "429" in err_str or "quota" in err_str or "insufficient_quota" in err_str or "rate" in err_str:
            raise ReagentVisionQuotaError(
                "OpenAI API quota exceeded. Add payment method and credits at https://platform.openai.com/account/billing"
            ) from e
        return None
