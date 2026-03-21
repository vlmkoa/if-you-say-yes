"""
Hierarchical reagent reference data: test method -> substance -> one or more reference hex
colors (for multi-step reactions like \"Purple > Black\").

**Sources (verify against your kit vendor — colors vary by batch, lighting, and photography):**
- DanceSafe — testing kit instructions & color charts:
  https://dancesafe.org/testing-kit-instructions/
  https://dancesafe.org/wp-content/uploads/2015/12/7-color-chart.pdf
- DanceSafe — reagent reaction updates: https://dancesafe.org/important-reagent-reaction-updates/
- DanceSafe — Simon’s reagent: https://dancesafe.org/rcblocks/simons-reagent/
- Wikipedia — Simon’s / Robadope overview: https://en.wikipedia.org/wiki/Simon%27s_reagent
- Morris reagent (A+B, mix ~30s): vendor charts (e.g. Bunk Police Morris booklet, PRO Test / DanceSafe instructions).

**Morris** is a **two-bottle** test used with cocaine, cathinones, and dissociatives (e.g. ketamine); **violet/purple**
reactions are common for ketamine, but **synthetic cathinones can also go purple** — confirm with Marquis/Mecke/etc.

**Simon’s** and **Robadope** are two-part tests (follow your kit: drop A then B on the same sample).
Simon’s turns **blue** for many **secondary amines** (e.g. MDMA, methamphetamine); **MDA / amphetamine**
(primary amines) typically show **no blue**. **Robadope** targets **primary amines** (e.g. MDA, amphetamine,
2C‑B, PMA) with a positive color change; **MDMA** (secondary) is typically **negative** — use your vendor chart.

Hex values below are **approximations** aligned to common published chart descriptions
(e.g. multi-panel Marquis / Liebermann / Froehde / Mandelin / Mecke grids). They are
**not** a substitute for reading the physical reaction against an authoritative chart.
"""

from __future__ import annotations

import re

# Canonical reagent names (keys for REAGENT_CHART)
REAGENT_METHOD_ORDER = (
    "Marquis",
    "Liebermann",
    "Froehde",
    "Mandelin",
    "Mecke",
    "Simon's",
    "Robadope",
    "Morris",
)

# Simon’s A+B — typical “positive” blue (secondary amines); verify with kit chart
_SIMONS_BLUE = "#1565C0"
# Robadope — typical positive (primary amine) teal/blue-green; verify with kit chart
_ROBADOPE_POS = "#00897B"
# Morris A+B — ketamine / many cathinones: violet–purple; cocaine: often blue–teal (vendor-dependent)
_MORRIS_VIOLET = "#8E24AA"
_MORRIS_COCA_TEAL = "#0097A7"

# Typical \"no visible reaction\" / clear reagent appearance (shared by many rows per column)
NC = "#EEF0EA"

REAGENT_CHART: dict[str, dict[str, list[str]]] = {
    "Marquis": {
        "2C-B": ["#FFCC33", "#2E7D32"],
        "3-MeO-PCP": [NC],
        "4-FA": [NC],
        "4-CMC": ["#FFF9C4"],
        "Amphetamine": ["#C62828", "#5D4037"],
        "Aspirin": ["#F8BBD9"],
        "Caffeine": [NC],
        "Cocaine": [NC],
        "Coca plant impurity": ["#FFD8B0"],
        "Diphenhydramine": ["#FFEE58"],
        "DOx (on blotter)": ["#2E7D32"],
        "Eutylone": ["#FFEB3B"],
        "Heroin": ["#7B1FA2"],
        "Ibuprofen": [NC],
        "Ketamine": [NC],
        "LSD (on blotter)": ["#424242"],
        "MDA": ["#5E35B1", "#1A1A1A"],
        "MDMA": ["#5E35B1", "#1A1A1A"],
        "Mephedrone": [NC],
        "Mescaline": ["#E65100"],
        "Methamphetamine": ["#FF5722", "#6D4C41"],
        "Methoxetamine": ["#F48FB1"],
        "Modafinil": ["#FFC107", "#A1887F"],
        "Paracetamol": [NC],
        "Pentylone": ["#FFEB3B"],
        "PMA / PMMA": [NC],
    },
    "Liebermann": {
        "2C-B": ["#1B5E20"],
        "3-MeO-PCP": ["#6D4C41"],
        "4-FA": ["#FF7043"],
        "4-CMC": ["#FFE0B2"],
        "Amphetamine": ["#FB8C00"],
        "Aspirin": ["#6D4C41"],
        "Caffeine": ["#FFFDE7"],
        "Cocaine": ["#FFB300"],
        "Coca plant impurity": [NC],
        "Diphenhydramine": ["#FFFDE7"],
        "DOx (on blotter)": ["#FFEB3B", "#212121"],
        "Eutylone": ["#BCAAA4"],
        "Heroin": ["#212121"],
        "Ibuprofen": ["#6D4C41"],
        "Ketamine": ["#FFF9C4"],
        "LSD (on blotter)": [NC],
        "MDA": ["#2E7D32", "#4A148C"],
        "MDMA": ["#5D4037", "#212121"],
        "Mephedrone": ["#FFEB3B"],
        "Mescaline": ["#212121"],
        "Methamphetamine": ["#FF5722"],
        "Methoxetamine": ["#BCAAA4"],
        "Modafinil": ["#EF6C00"],
        "Paracetamol": ["#5D4037"],
        "Pentylone": [NC],
        "PMA / PMMA": ["#4E342E"],
    },
    "Froehde": {
        "2C-B": ["#FFEB3B"],
        "3-MeO-PCP": [NC],
        "4-FA": ["#E1BEE7"],
        "4-CMC": [NC],
        "Amphetamine": [NC],
        "Aspirin": ["#3949AB", "#6A1B9A"],
        "Caffeine": [NC],
        "Cocaine": [NC],
        "Coca plant impurity": [NC],
        "Diphenhydramine": ["#FFEB3B"],
        "DOx (on blotter)": ["#FFEB3B", "#2E7D32"],
        "Eutylone": ["#FFEB3B", "#2E7D32"],
        "Heroin": ["#7B1FA2"],
        "Ibuprofen": [NC],
        "Ketamine": [NC],
        "LSD (on blotter)": [NC],
        "MDA": ["#5E35B1", "#1A1A1A"],
        "MDMA": ["#5E35B1", "#1A1A1A"],
        "Mephedrone": [NC],
        "Mescaline": ["#FFEB3B"],
        "Methamphetamine": [NC],
        "Methoxetamine": ["#FFEB3B", "#2E7D32"],
        "Modafinil": ["#FF5722"],
        "Paracetamol": [NC],
        "Pentylone": ["#FFEB3B", "#2E7D32"],
        "PMA / PMMA": ["#B2DFDB"],
    },
    "Mandelin": {
        "2C-B": ["#2E7D32"],
        "3-MeO-PCP": ["#558B2F", "#5D4037"],
        "4-FA": ["#B3E5FC"],
        "4-CMC": [NC],
        "Amphetamine": ["#6B8E23"],
        "Aspirin": ["#455A64"],
        "Caffeine": [NC],
        "Cocaine": ["#CFD8DC"],
        "Coca plant impurity": [NC],
        "Diphenhydramine": ["#8D6E63"],
        "DOx (on blotter)": ["#2E7D32", "#FFEB3B"],
        "Eutylone": [NC],
        "Heroin": ["#5D4037"],
        "Ibuprofen": ["#5D4037"],
        "Ketamine": ["#FFCC80"],
        "LSD (on blotter)": [NC],
        "MDA": ["#5E35B1", "#1A1A1A"],
        "MDMA": ["#5E35B1", "#1A1A1A"],
        "Mephedrone": [NC],
        "Mescaline": ["#5D4037"],
        "Methamphetamine": ["#2E7D32", "#1565C0"],
        "Methoxetamine": [NC],
        "Modafinil": ["#8D4E37"],
        "Paracetamol": ["#827717"],
        "Pentylone": ["#FFCC80"],
        "PMA / PMMA": ["#BF360C"],
    },
    "Mecke": {
        "2C-B": ["#FFEB3B"],
        "3-MeO-PCP": ["#FFEB3B"],
        "4-FA": [NC],
        "4-CMC": [NC],
        "Amphetamine": [NC],
        "Aspirin": [NC],
        "Caffeine": [NC],
        "Cocaine": [NC],
        "Coca plant impurity": [NC],
        "Diphenhydramine": ["#FFEB3B"],
        "DOx (on blotter)": ["#9E9E9E"],
        "Eutylone": ["#FF9800", "#6D4C41"],
        "Heroin": ["#00695C"],
        "Ibuprofen": ["#A1887F"],
        "Ketamine": [NC],
        "LSD (on blotter)": [NC],
        "MDA": ["#2E7D32", "#0D47A1"],
        "MDMA": ["#2E7D32", "#0D47A1"],
        "Mephedrone": [NC],
        "Mescaline": ["#FFEB3B", "#5D4037"],
        "Methamphetamine": ["#FFF9C4"],
        "Methoxetamine": ["#FFEB3B", "#2E7D32", "#C62828"],
        "Modafinil": ["#FF9800", "#5D4037"],
        "Paracetamol": [NC],
        "Pentylone": ["#FF9800"],
        "PMA / PMMA": ["#FFEB3B", "#827717"],
    },
    # Simon’s: blue after A+B for many secondary amines; little/no blue for primary amines (incl. MDA, amphetamine).
    "Simon's": {
        "2C-B": [NC],
        "3-MeO-PCP": [NC],
        "4-FA": [NC],
        "4-CMC": [_SIMONS_BLUE],
        "Amphetamine": [NC],
        "Aspirin": [NC],
        "Caffeine": [NC],
        "Cocaine": [NC],
        "Coca plant impurity": [NC],
        "Diphenhydramine": [NC],
        "DOx (on blotter)": [NC],
        "Eutylone": [_SIMONS_BLUE],
        "Heroin": [NC],
        "Ibuprofen": [NC],
        "Ketamine": [NC],
        "LSD (on blotter)": [NC],
        "MDA": [NC],
        "MDMA": [_SIMONS_BLUE],
        "Mephedrone": [_SIMONS_BLUE],
        "Mescaline": [NC],
        "Methamphetamine": [_SIMONS_BLUE],
        "Methoxetamine": [NC],
        "Modafinil": [NC],
        "Paracetamol": [NC],
        "Pentylone": [_SIMONS_BLUE],
        "PMA": [NC],
        "PMMA": [_SIMONS_BLUE],
    },
    # Robadope: positive color for many primary amines; MDMA / meth (secondary) typically negative on standard charts.
    "Robadope": {
        "2C-B": [_ROBADOPE_POS],
        "3-MeO-PCP": [NC],
        "4-FA": [_ROBADOPE_POS],
        "4-CMC": [NC],
        "Amphetamine": [_ROBADOPE_POS],
        "Aspirin": [NC],
        "Caffeine": [NC],
        "Cocaine": [NC],
        "Coca plant impurity": [NC],
        "Diphenhydramine": [NC],
        "DOx (on blotter)": [_ROBADOPE_POS],
        "Eutylone": [NC],
        "Heroin": [NC],
        "Ibuprofen": [NC],
        "Ketamine": [NC],
        "LSD (on blotter)": [NC],
        "MDA": [_ROBADOPE_POS],
        "MDMA": [NC],
        "Mephedrone": [NC],
        "Mescaline": [_ROBADOPE_POS],
        "Methamphetamine": [NC],
        "Methoxetamine": [NC],
        "Modafinil": [NC],
        "Paracetamol": [NC],
        "Pentylone": [NC],
        "PMA": [_ROBADOPE_POS],
        "PMMA": [NC],
    },
    # Morris (A + B, mix per kit): ketamine → violet; cathinones often purple too; cocaine → blue/teal on many charts.
    "Morris": {
        "2C-B": [NC],
        "3-MeO-PCP": [NC],
        "4-FA": [NC],
        "4-CMC": [_MORRIS_VIOLET],
        "Amphetamine": [NC],
        "Aspirin": [NC],
        "Caffeine": [NC],
        "Cocaine": [_MORRIS_COCA_TEAL],
        "Coca plant impurity": [_MORRIS_COCA_TEAL],
        "Diphenhydramine": [NC],
        "DOx (on blotter)": [NC],
        "Eutylone": [_MORRIS_VIOLET],
        "Heroin": [NC],
        "Ibuprofen": [NC],
        "Ketamine": [_MORRIS_VIOLET],
        "LSD (on blotter)": [NC],
        "MDA": [NC],
        "MDMA": [NC],
        "Mephedrone": [_MORRIS_VIOLET],
        "Mescaline": [NC],
        "Methamphetamine": [NC],
        "Methoxetamine": [_MORRIS_VIOLET],
        "Modafinil": [NC],
        "Paracetamol": [NC],
        "Pentylone": [_MORRIS_VIOLET],
        "PMA": [NC],
        "PMMA": [_MORRIS_VIOLET],
    },
}

def _normalize_token_for_abbrev(text: str) -> str:
    """Lowercase, strip; drop a single trailing period (e.g. chart header \"M.\")."""
    return text.strip().rstrip(".").strip().lower()


# Whole-string / single-token abbreviations only (avoids \"m\" matching inside \"mdma\").
# M = Marquis is common on compact charts; Mandelin/Mecke use multi-letter codes to disambiguate.
_REAGENT_ABBREV_EXACT: dict[str, str] = {
    "m": "Marquis",
    "mq": "Marquis",
    "l": "Liebermann",
    "lb": "Liebermann",
    "f": "Froehde",
    "fr": "Froehde",
    "fd": "Froehde",
    "md": "Mandelin",
    "mn": "Mandelin",
    "mc": "Mecke",
    "mk": "Mecke",
    "sm": "Simon's",
    "sim": "Simon's",
    "rd": "Robadope",
    "rb": "Robadope",
    "rob": "Robadope",
    "mr": "Morris",
    "mo": "Morris",
    "mor": "Morris",
}


def reagent_method_abbreviation_hint() -> str:
    """Short legend for prompts / UI: map common initials to canonical method names."""
    return (
        "Chart initials (use full canonical name in JSON \"method\" when possible): "
        "M or Mq→Marquis; L or Lb→Liebermann; F or Fr→Froehde; Md or Mn→Mandelin; Mc or Mk→Mecke; "
        "Sm or Sim→Simon's; Rd or Rb or Rob→Robadope; Mr or Mo or Mor→Morris."
    )


# Substrings (lowercase) -> canonical method; longer / more specific first where needed
_REAGENT_SUBSTRING_MAP: tuple[tuple[str, str], ...] = (
    ("liebermann", "Liebermann"),
    ("froehde", "Froehde"),
    ("froede", "Froehde"),
    ("robadope", "Robadope"),
    ("simon's", "Simon's"),
    ("simons", "Simon's"),
    ("simon", "Simon's"),
    ("mandelin", "Mandelin"),
    ("marquis", "Marquis"),
    ("mecke", "Mecke"),
)


def _word_boundary_match(haystack_lower: str, word: str) -> bool:
    """True if `word` appears as a whole token (not as prefix of another word, e.g. morris vs morrison)."""
    return re.search(rf"(?<![a-z]){re.escape(word)}(?![a-z])", haystack_lower, re.I) is not None


def normalize_reagent_method(text: str | None) -> str | None:
    """Map free text (label, user input) to a canonical REAGENT_CHART key."""
    if not text or not isinstance(text, str):
        return None
    t = _normalize_token_for_abbrev(text)
    if not t:
        return None
    if t in _REAGENT_ABBREV_EXACT:
        return _REAGENT_ABBREV_EXACT[t]
    raw_l = text.strip().lower()
    if _word_boundary_match(raw_l, "morris"):
        return "Morris"
    for needle, canon in _REAGENT_SUBSTRING_MAP:
        if needle in t:
            return canon
    # Exact match on canonical names (ASCII fold for Simon’s)
    for canon in REAGENT_METHOD_ORDER:
        if canon.lower().replace("'", "") == t.replace("'", ""):
            return canon
    return None


def infer_reagent_from_text(blob: str | None) -> str | None:
    """Best-effort: find a reagent name or chart initial in user-visible text."""
    if not blob or not isinstance(blob, str):
        return None
    for tok in re.split(r"[^A-Za-z0-9']+", blob):
        if not tok:
            continue
        hit = normalize_reagent_method(tok)
        if hit:
            return hit
    tl = blob.strip().lower()
    if _word_boundary_match(tl, "morris"):
        return "Morris"
    for needle, canon in _REAGENT_SUBSTRING_MAP:
        if needle in tl:
            return canon
    return None


def list_known_reagents() -> list[str]:
    return list(REAGENT_METHOD_ORDER)
