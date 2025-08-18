"""
Deprecated shim. Import from core.agents.*. This package remains for backward compatibility.
"""

import warnings as _w
_w.warn("dr_rd/agents is deprecated; use core.agents.*", DeprecationWarning, stacklevel=2)
try:
    from core.agents.registry import build_agents as build_agents  # re-export
except Exception:
    pass
