from fastapi import APIRouter

from app.core.pipeline import run_anonymization
from app.core.schemas import AnonymizeRequest, AnonymizeResponse

router = APIRouter(prefix="/api/v1", tags=["anonymize"])


@router.post("/anonymize", response_model=AnonymizeResponse)
def anonymize_endpoint(body: AnonymizeRequest) -> AnonymizeResponse:
    return run_anonymization(body.text, body.mode, use_ner=body.use_ner)
