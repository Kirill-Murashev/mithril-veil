"""GLiNER zero-shot detector configuration."""

GLINER_MODEL_NAME = "urchade/gliner_mediumv2.1"
GLINER_DEFAULT_THRESHOLD = 0.5
GLINER_MAX_LABELS = 50
GLINER_DEFAULT_CONFIDENCE = 0.60

DEFAULT_GLINER_LABELS: list[str] = [
    "person",
    "organization",
    "location",
    "address",
    "passport number",
    "contract number",
    "bank account",
    "court case number",
    "tax identification number",
    "phone number",
    "email",
    "vehicle registration number",
]

GLINER_LABEL_TO_ENTITY: dict[str, str] = {
    "person": "PERSON",
    "organization": "ORGANIZATION",
    "location": "LOCATION",
    "address": "ADDRESS",
    "passport number": "PASSPORT_RU",
    "contract number": "CONTRACT_NUMBER",
    "bank account": "BANK_ACCOUNT",
    "court case number": "COURT_CASE_NUMBER",
    "tax identification number": "INN",
    "phone number": "PHONE",
    "email": "EMAIL",
    "vehicle registration number": "VEHICLE_REGISTRATION_NUMBER",
}


def normalize_gliner_label(label: str) -> str:
    return label.strip().lower()


def map_gliner_label(label: str) -> str | None:
    return GLINER_LABEL_TO_ENTITY.get(normalize_gliner_label(label))


def validate_gliner_labels(labels: list[str] | None) -> list[str] | None:
    if labels is None:
        return None
    if len(labels) > GLINER_MAX_LABELS:
        raise ValueError(f"At most {GLINER_MAX_LABELS} GLiNER labels are allowed.")
    normalized: list[str] = []
    for label in labels:
        stripped = label.strip()
        if not stripped:
            raise ValueError("GLiNER labels must not contain empty strings.")
        normalized.append(stripped)
    return normalized
