import logging
from .unified_registry import (
    AGENT_REGISTRY,
    build_agents_unified,
    get_agent,
    get_agent_class,
    validate_registry,
)

logging.warning(
    "core.agents.registry is deprecated; use core.agents.unified_registry. This shim will be removed next release."
)

# Backwards compatibility helpers -------------------------------------------------

def build_agents(*args, **kwargs):
    return build_agents_unified(*args, **kwargs)


def load_mode_models(*args, **kwargs):  # pragma: no cover - legacy shim
    raise NotImplementedError(
        "load_mode_models has been removed; use AGENT_MODEL_MAP and model router instead."
    )

