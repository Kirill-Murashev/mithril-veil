"""Audit logging — placeholder; must never log raw PII when policy forbids it."""

from app.core.policies import DEFAULT_POLICY, SecurityPolicy


def may_log_detected_value(policy: SecurityPolicy | None = None) -> bool:
    policy = policy or DEFAULT_POLICY
    return policy.log_detected_values
