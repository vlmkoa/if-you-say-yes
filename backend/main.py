import logging
import os
from typing import Optional

from fastapi import FastAPI, File, Form, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from neo4j.exceptions import Neo4jError
from pydantic import BaseModel, Field

from .neo4j_client import get_interaction_resolved, close_driver, neo4j_available
from .reagent_chart_data import list_known_reagents
from .reagent_vision import (
    ReagentVisionQuotaError,
    extract_vision_from_image,
    match_hex_to_drugs_for_reagent,
    resolve_reagent_for_color_entry,
)


logger = logging.getLogger("drug-interaction-api")


class InteractionQuery(BaseModel):
    drug_a: str = Field(..., description="Name of the first substance.")
    drug_b: str = Field(..., description="Name of the second substance.")


class InteractionResult(BaseModel):
    drug_a: str
    drug_b: str
    risk_level: str
    mechanism: str
    inferred: bool = False
    reference_drug_a: Optional[str] = None
    reference_drug_b: Optional[str] = None
    no_known_effect: bool = False


class ErrorResponse(BaseModel):
    detail: str


app = FastAPI(
    title="Drug Interaction Engine",
    description="API for querying interaction risk between substances stored in Neo4j AuraDB.",
    version="0.1.0",
)


# Allow any origin so the frontend health check works regardless of host (localhost, 127.0.0.1, IP, etc.).
# credentials=False is required when using allow_origins=["*"]; we don't need cookies for /health or /interaction.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get(
    "/health",
    summary="Health check (Neo4j connectivity)",
    responses={200: {"description": "Neo4j reachable"}, 503: {"description": "Neo4j unreachable"}},
)
async def health() -> dict:
    """
    Returns 200 if Neo4j is reachable, 503 otherwise.
    Use this to show "interaction check temporarily unavailable" in the UI when Neo4j is off.
    """
    if neo4j_available():
        return {"status": "ok", "neo4j": "available"}
    raise HTTPException(
        status_code=503,
        detail="Neo4j is not available. Interaction lookup is disabled until the database is reachable.",
    )


@app.on_event("shutdown")
async def shutdown_event() -> None:
    # Ensure the Neo4j driver is closed when the app shuts down.
    close_driver()


@app.get(
    "/interaction",
    response_model=InteractionResult,
    responses={
        404: {"model": ErrorResponse, "description": "No interaction found between the given substances."},
        500: {"model": ErrorResponse, "description": "Internal error while querying the graph."},
    },
    summary="Get interaction between two substances",
)
async def read_interaction(
    drug_a: str = Query(..., description="Name of the first substance."),
    drug_b: str = Query(..., description="Name of the second substance."),
) -> InteractionResult:
    """
    Look up any [:INTERACTS_WITH] relationship between two Substance nodes
    and return its risk level and mechanism.
    """
    # Basic validation (Pydantic also validates but this gives clearer 400s for empty strings)
    trimmed_a = drug_a.strip()
    trimmed_b = drug_b.strip()
    if not trimmed_a or not trimmed_b:
        raise HTTPException(status_code=400, detail="Both drug_a and drug_b must be non-empty strings.")

    try:
        result: Optional[dict] = get_interaction_resolved(trimmed_a.lower(), trimmed_b.lower())
    except Neo4jError as e:
        logger.exception("Error while querying Neo4j for interaction.")
        raise HTTPException(
            status_code=503,
            detail="Interaction service temporarily unavailable. Neo4j may be offline or unreachable.",
        ) from e
    except RuntimeError as e:
        # get_driver() raises when NEO4J_URI / NEO4J_USERNAME / NEO4J_PASSWORD are missing
        logger.warning("Neo4j not configured: %s", e)
        raise HTTPException(
            status_code=503,
            detail="Interaction service not configured. Set NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD and run scripts/load_tripsit_to_neo4j.py to load data.",
        ) from e

    if result is None:
        # No interaction and no relative fallback: return 200 with "no known effects" (gray in UI)
        return InteractionResult(
            drug_a=trimmed_a,
            drug_b=trimmed_b,
            risk_level="Unknown",
            mechanism="No known interaction data for this combination. Colorimetric testing is presumptive; consult a professional.",
            no_known_effect=True,
        )

    return InteractionResult(
        drug_a=trimmed_a,
        drug_b=trimmed_b,
        risk_level=str(result.get("risk_level") or ""),
        mechanism=str(result.get("mechanism") or ""),
        inferred=bool(result.get("inferred")),
        reference_drug_a=result.get("reference_drug_a"),
        reference_drug_b=result.get("reference_drug_b"),
    )


# --- Phase 4: Reagent test analysis (vision + color matching) ---

ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}


@app.post(
    "/reagent/analyze",
    summary="Analyze reagent test image (vision + color match)",
    responses={
        200: {"description": "Hex extracted; matches scoped to reagent method when resolved."},
        400: {"model": ErrorResponse, "description": "Invalid or missing image."},
        503: {"model": ErrorResponse, "description": "Vision API not configured or failed."},
    },
)
async def reagent_analyze(
    image: UploadFile = File(..., description="Reagent test result image"),
    prompt: str = Form("", description="Context: which reagent/column if not visible (e.g. Marquis, Mandelin)."),
    reagent: str = Form(
        "",
        description="Optional: explicit reagent test name (Marquis, Liebermann, Froehde, Mandelin, Mecke, Simon's, Robadope, Morris).",
    ),
) -> dict:
    """
    Multipart image + optional text. Vision extracts hex(es) and, when possible, the reagent **method**
    (column) for each color. Matching uses the chart for that method only (method → drug → reference hexes).
    If the method cannot be resolved, `needs_reagent` is true and matches are empty until the user
    specifies `reagent` or names the test in `prompt`.
    """
    if image.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported type. Use one of: {', '.join(ALLOWED_IMAGE_TYPES)}",
        )
    body = await image.read()
    if not body or len(body) > 10 * 1024 * 1024:  # 10 MB
        raise HTTPException(status_code=400, detail="Image empty or too large (max 10 MB).")

    api_key = (os.getenv("OPENAI_API_KEY") or "").strip()
    if not api_key:
        raise HTTPException(
            status_code=503,
            detail="OPENAI_API_KEY is not set. Add OPENAI_API_KEY=sk-... to your .env file (project root), then restart the backend: docker compose up -d backend.",
        )

    user_prompt = (prompt or "").strip() or None
    explicit_reagent = (reagent or "").strip() or None
    try:
        vision = await extract_vision_from_image(body, user_prompt=user_prompt)
    except ReagentVisionQuotaError as e:
        raise HTTPException(status_code=503, detail=str(e)) from e

    if vision is None or not vision.get("colors"):
        raise HTTPException(
            status_code=503,
            detail="Could not extract color from this image. Use a clear photo of a reagent test (test tube or kit with visible liquid color). If the key is set, check backend logs for API errors.",
        )

    vlabels = vision.get("labels") or []
    color_rows = [c for c in vision["colors"] if c.get("hex")]
    single = len(color_rows) == 1

    colors_out = []
    for c in color_rows:
        hex_code = c.get("hex")
        if not hex_code:
            continue
        method_resolved = resolve_reagent_for_color_entry(
            c,
            explicit_reagent=explicit_reagent,
            user_prompt=user_prompt,
            vision_labels=vlabels if isinstance(vlabels, list) else [],
            single_color=single,
        )
        needs = method_resolved is None
        matches = (
            []
            if needs
            else match_hex_to_drugs_for_reagent(hex_code, method_resolved, top_k=5)
        )
        colors_out.append(
            {
                "hex": hex_code,
                "label": c.get("label"),
                "method": method_resolved,
                "needs_reagent": needs,
                "matches": matches,
            }
        )
    return {
        "description": vision.get("description"),
        "labels": vlabels,
        "colors": colors_out,
        "known_reagents": list_known_reagents(),
        "reference_note": (
            "Chart data is approximate; verify with DanceSafe / your kit vendor instructions. "
            "See backend/reagent_chart_data.py and https://dancesafe.org/testing-kit-instructions/"
        ),
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )

