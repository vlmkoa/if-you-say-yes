"""
Reagent test analysis — vision (hex + reagent column extraction) and deterministic color matching
scoped by test method. Requires OPENAI_API_KEY for GPT-4o vision.
"""
from __future__ import annotations

import json
import logging
import os
import re
from typing import Any

from .reagent_chart_data import (
    REAGENT_CHART,
    infer_reagent_from_text,
    list_known_reagents,
    normalize_reagent_method,
    reagent_method_abbreviation_hint,
)

logger = logging.getLogger("reagent-vision")


class ReagentVisionQuotaError(Exception):
    """Raised when the vision API fails due to quota/billing (429)."""
    pass


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


def match_hex_to_drugs_for_reagent(hex_code: str, method: str, top_k: int = 5) -> list[dict[str, Any]]:
    """
    Deterministic matching within one reagent column: for each substance, distance is the
    minimum RGB distance to any of its reference hexes (multi-step reactions).
    Returns top_k drugs with probability percentages (inverse distance, normalized).
    """
    canon = normalize_reagent_method(method)
    if not canon or canon not in REAGENT_CHART:
        return []

    try:
        target = hex_to_rgb(hex_code)
    except (ValueError, TypeError):
        return []

    drugs = REAGENT_CHART[canon]
    distances: list[tuple[str, float]] = []
    for drug_name, hexes in drugs.items():
        best: float | None = None
        for ref in hexes:
            try:
                d = rgb_distance(target, hex_to_rgb(ref))
            except ValueError:
                continue
            best = d if best is None else min(best, d)
        if best is not None:
            distances.append((drug_name, best))

    if not distances:
        return []

    distances.sort(key=lambda x: x[1])
    top = distances[:top_k]
    scores = [1.0 / (1.0 + d) for _, d in top]
    total = sum(scores) or 1.0
    probabilities = [round(100.0 * s / total, 1) for s in scores]
    diff = 100.0 - sum(probabilities)
    if diff != 0 and probabilities:
        probabilities[0] = round(probabilities[0] + diff, 1)

    return [
        {"substance": name, "probability": p}
        for (name, _), p in zip(top, probabilities)
    ]


def resolve_reagent_for_color_entry(
    color_entry: dict[str, Any],
    *,
    explicit_reagent: str | None,
    user_prompt: str | None,
    vision_labels: list[str],
    single_color: bool,
) -> str | None:
    """
    Resolve which reagent column applies to this color sample.
    Priority: per-color method/label from vision (chart headers) > explicit form field >
    user chat text > OCR labels (only when there is a single color region).
    """
    r = normalize_reagent_method(color_entry.get("method") or color_entry.get("label"))
    if r:
        return r

    r = normalize_reagent_method(explicit_reagent)
    if r:
        return r

    r = infer_reagent_from_text(user_prompt)
    if r:
        return r

    if single_color:
        blob = " ".join(vision_labels)
        r = infer_reagent_from_text(blob)
        if r:
            return r
    return None


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
    """Parse LLM JSON; return normalized dict with colors[{hex, label?, method?}], labels[], description."""
    content = (content or "").strip()
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
    if isinstance(obj.get("description"), str) and obj["description"].strip():
        out["description"] = obj["description"].strip()
    labels = obj.get("labels")
    if isinstance(labels, list):
        out["labels"] = [str(x).strip() for x in labels if x and str(x).strip()]
    elif isinstance(obj.get("label"), str) and obj["label"].strip():
        out["labels"] = [obj["label"].strip()]

    def append_color(h: str, label: str | None, method: str | None) -> None:
        out["colors"].append(
            {
                "hex": h,
                "label": label.strip() if label else None,
                "method": method.strip() if method else None,
            }
        )

    hex_single = obj.get("hex") or obj.get("hex_code")
    if isinstance(hex_single, str):
        h = _normalize_hex(hex_single)
        if h:
            m = obj.get("method")
            m_str = str(m).strip() if m else None
            append_color(h, None, m_str)
            return out

    colors = obj.get("colors")
    if isinstance(colors, list):
        for c in colors:
            if isinstance(c, dict):
                h = _normalize_hex(str(c.get("hex") or c.get("hex_code") or ""))
                if not h:
                    continue
                label = c.get("label")
                method = c.get("method")
                append_color(
                    h,
                    str(label).strip() if label else None,
                    str(method).strip() if method else None,
                )
            elif isinstance(c, str):
                h = _normalize_hex(c)
                if h:
                    append_color(h, None, None)
    if out["colors"]:
        return out
    return None


async def extract_vision_from_image(
    image_bytes: bytes,
    user_prompt: str | None = None,
) -> dict[str, Any] | None:
    """
    Send image to GPT-4o vision. Extract:
    - colors: list of { hex, method?, label? } — **method** should be the reagent test name
      (Marquis, Liebermann, Froehde, Mandelin, Mecke) when visible as a column header or label.
    - labels: visible text (headers, bottle labels).
    - description: short scene description.
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

    known = ", ".join(list_known_reagents())
    abbrev_help = reagent_method_abbreviation_hint()
    system = (
        "You are analyzing reagent drug test documentation or photos (e.g. chart, kit, or reaction vial). "
        "Extract ONLY observable data; do not guess or name which illegal drug is in an unknown sample. "
        "Return a JSON object with:\n"
        f"1) \"colors\": array of objects. Each object MUST have \"hex\" (#RRGGBB) for the main liquid/reaction color shown. "
        f"When a column or region corresponds to a specific reagent test, set \"method\" to one of: {known}, "
        f"OR to the single- or two-letter code printed on the chart (e.g. M, L, F, Md, Mc). {abbrev_help} "
        "Use \"method\" when the image shows a chart column header, printed label, or clear association. "
        "Optional \"label\" for extra text (e.g. tube number).\n"
        "2) \"labels\": array of visible text strings (headers, kit name, handwritten notes).\n"
        "3) \"description\": optional short description.\n"
        "If the image is a multi-column chart, output one color object per distinct reaction color you are reporting, "
        "each with the correct \"method\" for that column when headers are visible. "
        "If only one reaction is shown and no method is visible, omit \"method\" (the user must state it separately). "
        "Return ONLY valid JSON."
    )

    user_text = (
        f"Return JSON: colors as [{{hex, method?, label?}}], labels as string array, optional description. "
        f"Known method names: {known}. {abbrev_help}"
    )
    if user_prompt and user_prompt.strip():
        user_text = (
            "User context: \""
            + user_prompt.strip()[:500]
            + "\". Use this to set \"method\" on each color when they name the reagent or tube. "
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
            max_tokens=800,
        )
        content = (response.choices[0].message.content or "").strip()
        return _parse_vision_json(content)
    except Exception as e:
        logger.exception("Vision API error: %s", e)
        err_str = str(e).lower()
        if "429" in err_str or "quota" in err_str or "insufficient_quota" in err_str or "rate" in err_str:
            raise ReagentVisionQuotaError(
                "OpenAI API quota exceeded. Add payment method and credits at https://platform.openai.com/account/billing"
            ) from e
        return None
