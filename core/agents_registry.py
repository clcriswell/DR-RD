import logging
from core.agents.unified_registry import (
    AGENT_REGISTRY,
    build_agents_unified,
    get_agent,
    get_agent_class,
    validate_registry,
)

logging.warning(
    "core.agents_registry is deprecated; use core.agents.unified_registry. This shim will be removed next release."
)
