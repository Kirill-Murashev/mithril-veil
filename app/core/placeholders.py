"""Deterministic typed placeholders for replace / reversible pseudonymization."""


def placeholder_for(entity_type: str, index: int) -> str:
    """Build a stable placeholder token, e.g. ``[EMAIL_1]``."""
    return f"[{entity_type}_{index}]"
