"""Data retention controls — placeholder for future implementation."""

from app.core.policies import DEFAULT_POLICY, SecurityPolicy


def should_persist_original(policy: SecurityPolicy | None = None) -> bool:
    policy = policy or DEFAULT_POLICY
    return policy.store_original_documents
