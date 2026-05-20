from fastapi import FastAPI

from app import __version__
from app.api.routes_anonymize import router as anonymize_router
from app.api.routes_health import router as health_router
from app.api.routes_presets import router as presets_router

app = FastAPI(
    title="Mithril Veil",
    description="Self-hosted Russian PII anonymization gateway for safer AI workflows",
    version=__version__,
)

app.include_router(health_router)
app.include_router(anonymize_router)
app.include_router(presets_router)
