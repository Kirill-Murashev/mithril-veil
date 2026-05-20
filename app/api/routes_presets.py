from fastapi import APIRouter

from app.core.presets import list_presets, preset_to_api_dict
from app.core.schemas import PresetInfoResponse

router = APIRouter(prefix="/api/v1", tags=["presets"])


@router.get("/presets", response_model=list[PresetInfoResponse])
def list_presets_endpoint() -> list[PresetInfoResponse]:
    return [PresetInfoResponse(**preset_to_api_dict(info)) for info in list_presets()]
