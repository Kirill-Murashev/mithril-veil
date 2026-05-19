from fastapi import APIRouter

from app import __version__
from app.core.schemas import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(
        status="ok",
        service="mithril-veil",
        version=__version__,
    )
