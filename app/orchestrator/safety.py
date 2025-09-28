from __future__ import annotations

from app.safety.policy import SafetyPolicy


def patch_allowed_by_policy(patch: dict, policy: SafetyPolicy) -> tuple[bool, str]:
    disallowed_keys = set(policy.pii_disallow)
    patch_keys = set(patch.keys())
    forbidden_keys = disallowed_keys.intersection(patch_keys)
    if forbidden_keys:
        return False, f"PII key(s) not allowed: {', '.join(forbidden_keys)}"
    return True, ""
