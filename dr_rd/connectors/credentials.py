from __future__ import annotations

from pathlib import Path
from typing import Optional

from dr_rd.config.env import get_env
from dr_rd.tenancy.models import TenantContext


BASE_DIR = Path.home() / ".dr_rd" / "tenants"


def get_credential(ctx: TenantContext, name: str) -> Optional[str]:
    """Fetch a credential for ``name`` scoped to ``ctx``.

    Resolution order:
      1. Environment variables ``DRRD_CRED_<ORG>_<WS>_<NAME>`` then
         ``DRRD_CRED_<ORG>_<NAME>`` then ``DRRD_CRED_<NAME>``.
      2. Local secret files under ``.dr_rd/tenants/<org>/<ws>/secrets/<name>``.
    """

    env_keys = [
        f"DRRD_CRED_{ctx.org_id}_{ctx.workspace_id or '_'}_{name}".upper(),
        f"DRRD_CRED_{ctx.org_id}_{name}".upper(),
        f"DRRD_CRED_{name}".upper(),
    ]
    for key in env_keys:
        val = get_env(key)
        if val:
            return val

    path = BASE_DIR / ctx.org_id / (ctx.workspace_id or "_") / "secrets" / name
    if path.exists():
        return path.read_text().strip()
    return None
