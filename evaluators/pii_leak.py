from __future__ import annotations

from dr_rd.safety import filters


def evaluate(output_json, intentional: bool = False) -> bool:
    """Return False if redactions would occur and not intentional."""
    _, decision = filters.filter_output(output_json)
    if decision.redactions and not intentional:
        return False
    return True
