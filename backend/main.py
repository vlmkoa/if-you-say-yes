import logging
from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from neo4j.exceptions import Neo4jError
from pydantic import BaseModel, Field

from .neo4j_client import get_interaction, close_driver, neo4j_available


logger = logging.getLogger("drug-interaction-api")


class InteractionQuery(BaseModel):
    drug_a: str = Field(..., description="Name of the first substance.")
    drug_b: str = Field(..., description="Name of the second substance.")


class InteractionResult(BaseModel):
    drug_a: str
    drug_b: str
    risk_level: str
    mechanism: str


class ErrorResponse(BaseModel):
    detail: str


app = FastAPI(
    title="Drug Interaction Engine",
    description="API for querying interaction risk between substances stored in Neo4j AuraDB.",
    version="0.1.0",
)


# Allow local Next.js dev by default; adjust origins as needed.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
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
    if not drug_a.strip() or not drug_b.strip():
        raise HTTPException(status_code=400, detail="Both drug_a and drug_b must be non-empty strings.")

    try:
        result: Optional[dict] = get_interaction(drug_a.strip(), drug_b.strip())
    except Neo4jError as e:
        logger.exception("Error while querying Neo4j for interaction.")
        # 503 when Neo4j is unreachable (e.g. AuraDB sleeping, network down)
        raise HTTPException(
            status_code=503,
            detail="Interaction service temporarily unavailable. Neo4j may be offline or unreachable.",
        ) from e

    if result is None:
        raise HTTPException(
            status_code=404,
            detail="No interaction found for the specified substances.",
        )

    return InteractionResult(
        drug_a=drug_a.strip(),
        drug_b=drug_b.strip(),
        risk_level=str(result.get("risk_level")),
        mechanism=str(result.get("mechanism")),
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )

