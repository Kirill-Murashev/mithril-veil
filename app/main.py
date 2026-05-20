from fastapi import FastAPI

from app.api.routes_anonymize import router as anonymize_router
from app.api.routes_health import router as health_router
from app.api.routes_presets import router as presets_router

app = FastAPI(
    title="Mithril Veil",
    description="Self-hosted Russian PII anonymization gateway for safer AI workflows",
    version="0.1.0",
)

app.include_router(health_router)
app.include_router(anonymize_router)
app.include_router(presets_router)
