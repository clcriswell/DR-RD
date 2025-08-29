# Multi-Tenancy and RBAC

This document provides a lightweight overview of the tenancy model and role-based
access control (RBAC) used in the DR-RD prototype.

## Tenancy Model
- **Org** – top level container for workspaces.
- **Workspace** – isolated environment within an org.
- **Principal** – authenticated actor (user or API key).
- **Tenant Context** – `{org_id, workspace_id, principal, run_id}` propagated through the system.

### Storage
Tenancy metadata is stored under `~/.dr_rd/tenants/` as JSONL files.

Each tenant may also have billing artifacts under
`~/.dr_rd/tenants/{org}/{workspace}/billing/` including usage rollups and
invoices. Budget and quota overlays can be supplied via
`config/tenants/{org}/{workspace}/billing.yaml`.

## Roles
| Role     | Scope      | Typical permissions |
|----------|------------|---------------------|
| OWNER    | Org        | all actions         |
| ADMIN    | Workspace  | manage keys/config  |
| RUNNER   | Workspace  | execute tasks       |
| VIEWER   | Workspace  | read results        |
| AUDITOR  | Org        | read audit/telemetry|
| CONFIG   | Org/WS     | edit tenant config  |

`DRRD_SUPERUSER_MODE=1` disables checks (development only).

## Enforcement Points
Permissions are enforced via decorators in `core.security.guard` which consult
`dr_rd.tenancy.policy`. All subsystems should call `require_perm()` before
performing tenant scoped actions.
