from fastapi import APIRouter, HTTPException

from app.core.gliner_config import GLINER_MODEL_NAME
from app.core.pipeline import run_anonymization
from app.core.presets import UnknownPresetError
from app.core.schemas import AnonymizeRequest, AnonymizeResponse

router = APIRouter(prefix="/api/v1", tags=["anonymize"])


@router.post("/anonymize", response_model=AnonymizeResponse)
def anonymize_endpoint(body: AnonymizeRequest) -> AnonymizeResponse:
    try:
        response, _policy = run_anonymization(
            body.text,
            body.mode,
            preset=body.preset,
            use_ner=body.use_ner,
            use_gliner=body.use_gliner,
            gliner_labels=body.gliner_labels,
            gliner_threshold=body.gliner_threshold,
            gliner_model_name=body.gliner_model_name or GLINER_MODEL_NAME,
        )
    except UnknownPresetError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return response
