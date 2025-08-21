# Build Spec & Work Plan

When enabled, DR-RD emits a build specification package alongside the final proposal. The package contains:

- `SDD.md` – System Design Doc with requirements, interfaces and risks.
- `ImplementationPlan.md` – work items, milestones and rollback notes.
- `bom.csv` – lightweight bill of materials.
- `budget.csv` – phase-level budget summary.
- `interface_contracts/` – markdown stubs for each interface contract.

All files are written under `audits/<project_slug>/build/`.

## Enabling

Set environment variable `DRRD_ENABLE_BUILD_SPEC=true` or check **Generate Build Spec & Work Plan** in the *Build Spec* expander of the UI before running domain experts. After execution, download links for these files appear in the app.
